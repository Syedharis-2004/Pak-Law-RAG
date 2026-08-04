"""
PakLaw AI Backend — Async Database Engine & Session Factory

Uses SQLAlchemy async engine with connection pooling.
Provides dependency-injectable async session.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# ── Async Engine ──────────────────────────────────────────────
engine_options = {
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_options.update(
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_options)

# ── Session Factory ───────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all database tables and seed initial system data (roles, admin)."""
    import app.models  # noqa: F401 - ensures all ORM models are registered in Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default roles and admin user if missing
    async with AsyncSessionLocal() as session:
        try:
            from sqlalchemy import select

            from app.core.security import hash_password
            from app.models.user import Role, User

            # 1. Seed default system roles
            roles_data = [
                ("citizen", "Citizen", "General public / citizen user"),
                ("lawyer", "Lawyer", "Verified legal professional"),
                ("student", "Law Student", "Law student / academic researcher"),
                ("admin", "Administrator", "System administrator"),
            ]
            for role_name, display, desc in roles_data:
                r = (
                    await session.execute(select(Role).where(Role.name == role_name))
                ).scalar_one_or_none()
                if not r:
                    session.add(
                        Role(
                            name=role_name,
                            display_name=display,
                            description=desc,
                            is_system=True,
                        )
                    )
            await session.flush()

            # 2. Seed default admin user
            admin_email = "admin@paklaw.ai"
            admin = (
                await session.execute(select(User).where(User.email == admin_email))
            ).scalar_one_or_none()
            if not admin:
                admin_role = (
                    await session.execute(select(Role).where(Role.name == "admin"))
                ).scalar_one_or_none()
                new_admin = User(
                    email=admin_email,
                    hashed_password=hash_password("Admin123!"),
                    full_name="PakLaw System Admin",
                    is_active=True,
                    is_verified=True,
                    is_superuser=True,
                )
                if admin_role:
                    new_admin.roles.append(admin_role)
                session.add(new_admin)

            await session.commit()
        except Exception:
            await session.rollback()



async def drop_tables() -> None:
    """Drop all database tables (for testing cleanup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
