"""
PakLaw AI — Pytest Configuration

Sets up test database engines, initializes Alembic schema structures,
and configures mock async database sessions and httpx clients.
"""

import asyncio
from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Use local test sqlite database in-memory/on-disk for testing fast iteration
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


@pytest.fixture(scope="session")
def event_loop():
    """Create session-scoped event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Creates schemas in the test sqlite database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injecting clean mock session."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client linked with mock DB dependencies."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest.fixture
async def user_token_headers(db_session: AsyncSession) -> dict:
    from app.models.user import User, Role
    from app.core.security import create_access_token
    from sqlalchemy import select
    
    # Check/Create citizen role
    citizen_role = (await db_session.execute(select(Role).where(Role.name == "citizen"))).scalar_one_or_none()
    if not citizen_role:
        citizen_role = Role(name="citizen", display_name="Citizen", is_system=True)
        db_session.add(citizen_role)
        await db_session.flush()

    user = User(
        email="testuser@paklaw.ai",
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


@pytest.fixture
async def admin_token_headers(db_session: AsyncSession) -> dict:
    from app.models.user import User, Role, Permission
    from app.core.security import create_access_token
    from sqlalchemy import select
    
    # Check/Create admin role & permissions
    admin_role = (await db_session.execute(select(Role).where(Role.name == "admin"))).scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="admin", display_name="Admin", is_system=True)
        db_session.add(admin_role)
        await db_session.flush()
        
    # Seed permission to upload
    upload_perm = (await db_session.execute(select(Permission).where(Permission.name == "documents:upload"))).scalar_one_or_none()
    if not upload_perm:
        upload_perm = Permission(name="documents:upload", resource="documents", action="upload")
        db_session.add(upload_perm)
        await db_session.flush()
        
    if upload_perm not in admin_role.permissions:
        admin_role.permissions.append(upload_perm)
        await db_session.flush()

    user = User(
        email="admin@paklaw.ai",
        hashed_password="hashedpassword",
        full_name="Test Admin",
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    user.roles.append(admin_role)
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"roles": ["admin"], "superuser": True}
    )
    return {"Authorization": f"Bearer {access_token}"}
