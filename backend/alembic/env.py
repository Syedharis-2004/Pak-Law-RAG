import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Load config ───────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Load models metadata ─────────────────────────────────────
from app.core.database import Base
# Import all models to ensure they register on Base.metadata
from app.models.user import User, Role, Permission
from app.models.document import Document, DocumentChunk, ProcessingJob
from app.models.conversation import Conversation, Message, Citation, Bookmark
from app.models.research import ResearchReport
from app.models.audit import AuditLog, AnalyticsEvent

target_metadata = Base.metadata

# Read sync database URL from env settings
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.SYNC_DATABASE_URL or settings.DATABASE_URL.replace("+asyncpg", ""))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
