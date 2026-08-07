# ============================================================
# PakLaw AI — Worker Dockerfile
# Celery workers for ingestion, embedding, and reporting
# ============================================================

FROM python:3.12-slim AS runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq5 \
    libgomp1 \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    celery[redis]==5.4.0 \
    redis==5.2.1 \
    sqlalchemy[asyncio]==2.0.36 \
    asyncpg==0.30.0 \
    psycopg2-binary==2.9.10 \
    pydantic==2.10.3 \
    pydantic-settings==2.7.0 \
    python-dotenv==1.0.1 \
    structlog==24.4.0 \
    langchain==0.3.12 \
    langchain-google-genai==2.0.7 \
    langchain-community==0.3.12 \
    langgraph==0.2.59 \
    llama-index==0.12.0 \
    llama-index-vector-stores-qdrant==0.4.3 \
    FlagEmbedding==1.3.3 \
    pdf2image==1.17.0 \
    pypdf==5.1.0 \
    python-docx==1.1.2 \
    beautifulsoup4==4.12.3 \
    langdetect==1.0.9 \
    reportlab==4.2.5 \
    flower==2.0.1 \
    httpx==0.28.1 \
    && (pip install paddlepaddle==2.6.2 paddleocr==2.9.1 2>/dev/null || true)

# Copy source code
COPY backend/ ./backend/
COPY ai/ ./ai/
COPY workers/ ./workers/

ENV PYTHONPATH=/app/backend:/app

# Create directories
RUN mkdir -p uploads logs

# Create non-root user
RUN groupadd -r celery && useradd -r -g celery celery
RUN chown -R celery:celery /app
USER celery

# Default command (overridden in docker-compose)
CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info"]
