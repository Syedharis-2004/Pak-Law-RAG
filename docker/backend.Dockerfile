# ============================================================
# PakLaw AI — Backend Dockerfile
# Multi-stage build for production
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /build

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

COPY backend/pyproject.toml backend/
COPY ai/pyproject.toml ai/

# Install dependencies
RUN cd backend && uv pip install --system --no-cache -r pyproject.toml 2>/dev/null || true
RUN uv pip install --system --no-cache \
    fastapi[all]==0.115.5 \
    sqlalchemy[asyncio]==2.0.36 \
    asyncpg==0.30.0 \
    alembic==1.14.0 \
    pydantic==2.10.3 \
    pydantic-settings==2.7.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.12 \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    httpx==0.28.1 \
    python-dotenv==1.0.1 \
    structlog==24.4.0 \
    prometheus-fastapi-instrumentator==7.0.0 \
    slowapi==0.1.9 \
    langchain==0.3.12 \
    langchain-google-genai==2.0.7 \
    langchain-community==0.3.12 \
    langgraph==0.2.59 \
    llama-index==0.12.0 \
    llama-index-vector-stores-qdrant==0.4.3 \
    qdrant-client==1.12.2 \
    sentence-transformers==3.3.1 \
    FlagEmbedding==1.3.3 \
    pdf2image==1.17.0 \
    pypdf==5.1.0 \
    python-docx==1.1.2 \
    beautifulsoup4==4.12.3 \
    langdetect==1.0.9 \
    reportlab==4.2.5 \
    python-pptx==1.0.2 \
    && (pip install paddlepaddle==2.6.2 paddleocr==2.9.1 2>/dev/null || true)

# ── Runtime stage ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libgomp1 \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY backend/ ./backend/
COPY ai/ ./ai/
COPY workers/ ./workers/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p uploads logs

# Create non-root user
RUN groupadd -r paklawai && useradd -r -g paklawai paklawai
RUN chown -R paklawai:paklawai /app
USER paklawai

# Expose port
EXPOSE 8000
ENV PYTHONPATH=/app/backend:/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
