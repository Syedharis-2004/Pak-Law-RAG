"""
PakLaw AI — User, Role, and Permission ORM Models

Implements RBAC with many-to-many user↔role and role↔permission
relationships. Uses UUID primary keys and soft deletes.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

# ── Association Tables ────────────────────────────────────────
user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)

role_permissions_table = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id", Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Uuid(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Permission(Base):
    """Granular permission (e.g., 'documents:upload', 'admin:users:manage')."""

    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary=role_permissions_table, back_populates="permissions"
    )

    __table_args__ = (UniqueConstraint("resource", "action", name="uq_resource_action"),)

    def __repr__(self) -> str:
        return f"<Permission {self.name}>"


class Role(Base):
    """User role (e.g., 'admin', 'lawyer', 'student', 'citizen')."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(
        "User", secondary=user_roles_table, back_populates="roles"
    )
    permissions: Mapped[list[Permission]] = relationship(
        Permission, secondary=role_permissions_table, back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class User(Base):
    """Platform user with profile, authentication, and roles."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Token management
    refresh_token: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Usage tracking
    api_calls_today: Mapped[int] = mapped_column(Integer, default=0)
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    storage_used_bytes: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        Role, secondary=user_roles_table, back_populates="users"
    )
    documents: Mapped[list["Document"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "Document", back_populates="owner", lazy="dynamic"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "Conversation", back_populates="user", lazy="dynamic"
    )
    research_reports: Mapped[list["ResearchReport"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "ResearchReport", back_populates="user", lazy="dynamic"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined] # noqa: F821
        "AuditLog", back_populates="user", lazy="dynamic"
    )

    def has_permission(self, resource: str, action: str) -> bool:
        """Check if user has a specific permission through any role."""
        if self.is_superuser:
            return True
        for role in self.roles:
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    return True
        return False

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(r.name == role_name for r in self.roles)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
