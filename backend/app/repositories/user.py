"""
PakLaw AI — User Repository

Handles database operations for User, Role, and Permission models.
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.user import Permission, Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """User repository for managing users, roles, and permissions."""

    model_class = User

    async def get_by_email(self, email: str, include_roles: bool = True) -> User | None:
        """Fetch a user by email, optionally preloading roles and permissions."""
        query = select(User).where(User.email == email, User.is_deleted == False)  # noqa: E712
        if include_roles:
            query = query.options(selectinload(User.roles).selectinload(Role.permissions))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_roles(self, id: uuid.UUID) -> User | None:
        """Fetch a user by ID with roles and permissions preloaded."""
        query = (
            select(User)
            .where(User.id == id, User.is_deleted == False)  # noqa: E712
            .options(selectinload(User.roles).selectinload(Role.permissions))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_role_by_name(self, name: str) -> Role | None:
        """Fetch a role by its unique name."""
        query = select(Role).where(Role.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_permission_by_name(self, name: str) -> Permission | None:
        """Fetch a permission by its unique name."""
        query = select(Permission).where(Permission.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_users_list(
        self, *, skip: int = 0, limit: int = 50, search: str | None = None
    ) -> tuple[Sequence[User], int]:
        """Fetch users list with pagination and search filter."""
        query = select(User).where(User.is_deleted == False)  # noqa: E712
        if search:
            query = query.where(
                User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get items
        query = query.offset(skip).limit(limit).options(selectinload(User.roles))
        result = await self.db.execute(query)
        return result.scalars().all(), total
