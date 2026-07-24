"""
PakLaw AI — Auth Pydantic Schemas
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    organization: str | None = Field(None, max_length=200)
    designation: str | None = Field(None, max_length=200)
    preferred_language: str = Field("en", pattern="^(en|ur|hi|ro)$")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    organization: str | None
    designation: str | None
    preferred_language: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    roles: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_roles(cls, user: object) -> "UserResponse":
        roles = []
        user_dict = getattr(user, "__dict__", {})
        if "roles" in user_dict and user_dict["roles"] is not None:
            roles = [r.name for r in user_dict["roles"]]

        data = {
            "id": getattr(user, "id"),
            "email": getattr(user, "email"),
            "full_name": getattr(user, "full_name"),
            "organization": getattr(user, "organization", None),
            "designation": getattr(user, "designation", None),
            "preferred_language": getattr(user, "preferred_language", "en"),
            "is_active": getattr(user, "is_active", True),
            "is_verified": getattr(user, "is_verified", False),
            "is_superuser": getattr(user, "is_superuser", False),
            "roles": roles,
            "created_at": getattr(user, "created_at"),
        }
        return cls(**data)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
