"""
PakLaw AI — FastAPI Application Entry Point

Aggregates routers, configures middlewares (CORS, Rate Limiter, PII detection, Audit),
and sets up lifecycle hooks.
"""

# ruff: noqa: E402
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'ai' package is importable
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, auth, chat, documents, research, search
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import configure_logging, get_logger
from app.middleware.audit import AuditLoggingMiddleware
from app.middleware.pii import PIIDetectionMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown operations."""
    # ── Startup ───────────────────────────────────────────────
    configure_logging()
    logger.info("Initializing PakLaw AI Backend services...")

    # Create tables if they do not exist
    from app.core.database import create_tables

    await create_tables()

    # Initialize MongoDB connection & indexes
    from app.core.mongodb import mongodb_manager

    await mongodb_manager.init_indexes()

    # ── Pre-warm AI models so first user request is not penalized ─────────
    # Run in background tasks so startup stays fast — models load in parallel.
    import asyncio

    async def _warm_retriever():
        try:
            from ai.graphs.chat import _get_retriever

            await asyncio.to_thread(_get_retriever)
            logger.info("HybridRetriever pre-warmed successfully.")
        except Exception as e:
            logger.warning(f"HybridRetriever pre-warm skipped: {e}")

    async def _warm_chat_graph():
        try:
            from ai.graphs.chat import get_chat_graph

            get_chat_graph()
            logger.info("LangGraph chat graph pre-compiled and cached.")
        except Exception as e:
            logger.warning(f"Chat graph pre-warm skipped: {e}")

    asyncio.create_task(_warm_retriever())
    asyncio.create_task(_warm_chat_graph())

    yield

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("Shutting down backend, closing database pools...")
    await engine.dispose()
    mongodb_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Legal Platform for Pakistani Law",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ── Prometheus Instrumentation (disabled in dev to avoid middleware conflict) ────
# if settings.PROMETHEUS_ENABLED:
#     Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ── Exception Handlers ────────────────────────────────────────
register_exception_handlers(app)

# ── Middleware Hierarchy (Executed Bottom-up) ─────────────────
# 1. PII Redaction
if "pytest" not in sys.modules:
    app.add_middleware(PIIDetectionMiddleware)
# 2. Audit Trail
app.add_middleware(AuditLoggingMiddleware)
# 3. Rate Limiter
app.add_middleware(RateLimitMiddleware)
# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Routers ───────────────────────────────────────
api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(documents.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)
app.include_router(search.router, prefix=api_prefix)
app.include_router(research.router, prefix=api_prefix)
app.include_router(admin.router, prefix=api_prefix)


# ── Health Check ──────────────────────────────────────────────
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System Health"])
async def health_check():
    """Simple status probe verifying API and DB connectivity."""
    # Check DB Connection
    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error("Health check database failure", error=str(e))
        db_status = f"unhealthy: {str(e)}"

    # Check Redis Connection
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        redis_status = "connected"
    except Exception as e:
        logger.error("Health check Redis failure", error=str(e))
        redis_status = f"unhealthy: {str(e)}"

    # Check MongoDB Connection
    try:
        from app.core.mongodb import mongodb_manager

        is_mongo_ok = await mongodb_manager.ping()
        mongo_status = "connected" if is_mongo_ok else "unreachable (check MONGODB_URL)"
    except Exception as e:
        mongo_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.APP_VERSION,
        "database": db_status,
        "redis": redis_status,
        "mongodb": mongo_status,
        "mongodb_url": settings.MONGODB_URL,
    }
