"""
PakLaw AI — FastAPI Dependency Injection Helpers

Provides dependency injection for current user authentication, Superuser checks,
and RBAC verification.
"""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_access_token
from app.models.user import User
from app.repositories.user import UserRepository

security = HTTPBearer()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Dependency injects UserRepository."""
    return UserRepository(User, db)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Dependency to authenticate and return the current active user from the JWT.

    Raises:
        HTTPException: 401 if token is invalid or expired.
    """
    token = credentials.credentials
    try:
        payload = verify_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid authentication credentials")
    except JWTError as e:
        raise AuthenticationError("Could not validate credentials") from e

    user_id = uuid.UUID(user_id_str)
    user = await user_repo.get_with_roles(user_id)
    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User is inactive")

    return user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency checking if the user is a superuser/admin."""
    if not current_user.is_superuser:
        raise AuthorizationError("The user does not have enough privileges")
    return current_user


class PermissionChecker:
    """Dependency class to enforce Role-Based Access Control (RBAC)."""

    def __init__(self, resource: str, action: str) -> None:
        self.resource = resource
        self.action = action

    def __call__(self, current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not current_user.has_permission(self.resource, self.action):
            raise AuthorizationError(
                f"Required permission '{self.resource}:{self.action}' is missing"
            )
        return current_user
