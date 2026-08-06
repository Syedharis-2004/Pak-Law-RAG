"""
PakLaw AI — Authentication Service

Handles user registration, login, JWT token issuance, token refresh,
and password management.
"""

import uuid
from datetime import UTC, datetime

from jose import JWTError

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.repositories.user import UserRepository
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """Service layer for authentication and user management."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register_user(self, schema: UserRegisterRequest) -> UserResponse:
        """Register a new user, hash password, and assign default citizen role."""
        # Check if email already registered
        existing_user = await self.user_repo.get_by_email(schema.email, include_roles=False)
        if existing_user:
            raise ConflictError(f"Email '{schema.email}' is already registered")

        # Hash password and prepare data
        hashed_pwd = hash_password(schema.password)
        user_data = schema.model_dump(exclude={"password"})
        user_data["hashed_password"] = hashed_pwd

        # Create user
        user = await self.user_repo.create(user_data)

        # Refetch with roles preloaded to avoid MissingGreenlet in AsyncIO
        loaded_user = await self.user_repo.get_with_roles(user.id)
        target_user = loaded_user or user

        # Assign default 'citizen' role if it exists
        citizen_role = await self.user_repo.get_role_by_name("citizen")
        if citizen_role and target_user:
            target_user.roles.append(citizen_role)
            await self.user_repo.db.flush()

        return UserResponse.from_orm_with_roles(target_user)


    async def login_user(self, schema: UserLoginRequest) -> TokenResponse:
        """Authenticate user by email and password, generate JWT tokens."""
        user = await self.user_repo.get_by_email(schema.email)
        if not user or not verify_password(schema.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Update last login
        user.last_login_at = datetime.now(UTC)

        # Generate tokens
        user_dict = getattr(user, "__dict__", {})
        roles_list = (
            [r.name for r in user_dict["roles"]]
            if "roles" in user_dict and user_dict["roles"] is not None
            else []
        )
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"roles": roles_list, "superuser": user.is_superuser},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # Save refresh token in DB
        user.refresh_token = refresh_token
        await self.user_repo.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes in seconds
            user=UserResponse.from_orm_with_roles(user),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Verify refresh token and issue new access/refresh tokens (refresh token rotation)."""
        try:
            payload = verify_refresh_token(refresh_token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise AuthenticationError("Invalid refresh token")
        except JWTError as e:
            raise AuthenticationError("Invalid or expired refresh token") from e

        user_id = uuid.UUID(user_id_str)
        user = await self.user_repo.get_with_roles(user_id)

        if not user or user.refresh_token != refresh_token:
            raise AuthenticationError("Invalid refresh token")

        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Generate new tokens
        user_dict = getattr(user, "__dict__", {})
        roles_list = (
            [r.name for r in user_dict["roles"]]
            if "roles" in user_dict and user_dict["roles"] is not None
            else []
        )
        new_access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"roles": roles_list, "superuser": user.is_superuser},
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        # Update refresh token in DB
        user.refresh_token = new_refresh_token
        await self.user_repo.db.flush()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60,
            user=UserResponse.from_orm_with_roles(user),
        )

    async def logout_user(self, user_id: uuid.UUID) -> None:
        """Revoke user's refresh token on logout."""
        user = await self.user_repo.get(user_id)
        if user:
            user.refresh_token = None
            await self.user_repo.db.flush()
