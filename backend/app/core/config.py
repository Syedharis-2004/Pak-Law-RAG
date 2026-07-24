"""
PakLaw AI Backend — Core Configuration

Centralizes all application settings using Pydantic Settings,
supporting environment variables and .env files.
"""

from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyHttpUrl, BeforeValidator, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from pathlib import Path

def parse_cors(v: Any) -> list[str]:
    """Parse CORS origins from comma-separated string or list."""
    if isinstance(v, str):
        return [origin.strip() for origin in v.split(",")]
    return v
BASE_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "PakLaw AI"
    APP_VERSION: str = "1.0.0"
    APP_SECRET_KEY: str
    DEBUG: bool = False

    # ── Server ────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str
    SYNC_DATABASE_URL: str | None = None
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # ── MongoDB ───────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "paklawai"
    USE_MONGODB: bool = True

    # ── Redis ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Qdrant ────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: str | None = None
    QDRANT_HTTPS: bool = False

    # ── Google Gemini ─────────────────────────────────────────
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-pro"
    GEMINI_TEMPERATURE: float = 0.1
    GEMINI_MAX_TOKENS: int = 8192
    GEMINI_TOP_P: float = 0.95
    GEMINI_TOP_K: int = 40

    # ── Embedding & Reranker ──────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_DIMENSION: int = 1024
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cpu"
    RERANKER_TOP_K: int = 10

    # ── JWT ───────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────────
    # NoDecode permits the documented comma-separated .env value instead of
    # requiring JSON syntax for this list setting.
    CORS_ORIGINS: Annotated[list[str], NoDecode, BeforeValidator(parse_cors)] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True

    # ── File Storage ──────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,html,md"

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    # ── OCR ───────────────────────────────────────────────────
    OCR_LANG: str = "en"
    OCR_USE_GPU: bool = False

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_CHAT_REQUESTS: int = 30
    RATE_LIMIT_CHAT_WINDOW_SECONDS: int = 60

    # ── Chunking ──────────────────────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    MAX_CHUNKS_PER_DOCUMENT: int = 5000

    # ── Retrieval ─────────────────────────────────────────────
    RETRIEVAL_TOP_K: int = 20
    RERANKER_FINAL_TOP_K: int = 5
    HYBRID_SEARCH_ALPHA: float = 0.7
    CONTEXT_COMPRESSION_RATIO: float = 0.5

    # ── Logging ───────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "./logs/paklawai.log"

    # ── Observability ─────────────────────────────────────────
    SENTRY_DSN: str | None = None
    PROMETHEUS_ENABLED: bool = True

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Accept conventional deployment values such as `release` and `production`."""
        if isinstance(v, str) and v.strip().lower() in {"release", "production", "prod"}:
            return False
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call this everywhere."""
    return Settings()


settings = get_settings()
