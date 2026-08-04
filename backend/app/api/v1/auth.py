"""
PakLaw AI — Authentication Router

Handles signup, login, logout, password change, and token refresh.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user, get_user_repository
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(user_repo)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    schema: UserRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Register a new user account with default citizen permissions."""
    return await auth_service.register_user(schema)


@router.post("/login", response_model=TokenResponse)
async def login(
    schema: UserLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Authenticate credentials and return access & refresh tokens."""
    return await auth_service.login_user(schema)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    schema: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Rotate JWT access and refresh tokens using a valid refresh token."""
    return await auth_service.refresh_tokens(schema.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Log out user and invalidate refresh token."""
    await auth_service.logout_user(current_user.id)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Retrieve details of the currently authenticated user."""
    return UserResponse.from_orm_with_roles(current_user)
