"""
PakLaw AI — Pytest Configuration

Sets up test database engines, initializes Alembic schema structures,
and configures mock async database sessions and httpx clients.
"""

from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.database import Base, get_db
from app.main import app

# Use a single in-memory SQLite DB shared across the full test session
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Session-scoped DB setup ──────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once for the whole test session, then drop them."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Single async session shared across the entire test session.
    
    We intentionally do NOT roll back between tests so that user/role rows
    created by one test (or fixture) are visible to the next.
    """
    async with TestSessionLocal() as session:
        yield session


# ── HTTP client ──────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the app with the shared test DB session."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Auth token fixtures ──────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def user_token_headers(db_session: AsyncSession) -> dict:
    """Create (or reuse) a citizen test user and return bearer token headers."""
    from app.models.user import User, Role
    from app.core.security import create_access_token

    # Create citizen role if absent
    citizen_role = (await db_session.execute(
        select(Role).where(Role.name == "citizen")
    )).scalar_one_or_none()
    if not citizen_role:
        citizen_role = Role(name="citizen", display_name="Citizen", is_system=True)
        db_session.add(citizen_role)
        await db_session.flush()

    # Reuse or create the test citizen user
    user = (await db_session.execute(
        select(User).where(User.email == "testcitizen@paklaw.ai")
    )).scalar_one_or_none()

    if not user:
        user = User(
            email="testcitizen@paklaw.ai",
            hashed_password="hashedpassword",
            full_name="Test Citizen",
            is_active=True,
            is_verified=True,
        )
        user.roles.append(citizen_role)
        db_session.add(user)
        await db_session.flush()
        await db_session.commit()

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"roles": ["citizen"], "superuser": False}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_token_headers(db_session: AsyncSession) -> dict:
    """Create (or reuse) a superuser test user and return bearer token headers."""
    from app.models.user import User, Role, Permission
    from app.core.security import create_access_token

    # Create admin role if absent
    admin_role = (await db_session.execute(
        select(Role).where(Role.name == "admin")
    )).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="admin", display_name="Admin", is_system=True)
        db_session.add(admin_role)
        await db_session.flush()

    # Create upload permission if absent — use eager load to avoid lazy-load errors
    upload_perm = (await db_session.execute(
        select(Permission).where(Permission.name == "documents:upload")
    )).scalar_one_or_none()
    if not upload_perm:
        upload_perm = Permission(
            name="documents:upload", resource="documents", action="upload"
        )
        db_session.add(upload_perm)
        await db_session.flush()

    # Reload role with permissions eagerly to avoid MissingGreenlet on lazy access
    role_with_perms = (await db_session.execute(
        select(Role)
        .where(Role.id == admin_role.id)
        .options(selectinload(Role.permissions))
    )).scalar_one()

    if upload_perm not in role_with_perms.permissions:
        role_with_perms.permissions.append(upload_perm)
        await db_session.flush()

    # Reuse or create the test admin user
    admin = (await db_session.execute(
        select(User).where(User.email == "testadmin@paklaw.ai")
    )).scalar_one_or_none()

    if not admin:
        admin = User(
            email="testadmin@paklaw.ai",
            hashed_password="hashedpassword",
            full_name="Test Admin",
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )
        admin.roles.append(admin_role)
        db_session.add(admin)
        await db_session.flush()
        await db_session.commit()

    access_token = create_access_token(
        subject=str(admin.id),
        extra_claims={"roles": ["admin"], "superuser": True}
    )
    return {"Authorization": f"Bearer {access_token}"}
