# PakLaw AI — Enterprise AI Legal Platform

PakLaw AI is a production-ready, multilingual Enterprise AI Legal Platform focused on Pakistani law. Comparable to Harvey AI or CoCounsel, it features advanced Retrieval-Augmented Generation (RAG) conversational agents, legal research graph workflows, document indexing pipelines with PaddleOCR, and secure role-based administration consoles.

---

## Technical Stack

* **LLM**: Google Gemini 2.5 Pro
* **Embedding Model**: BAAI/bge-m3 (dense & sparse representations)
* **Reranker**: BAAI/bge-reranker-v2-m3
* **Framework**: LangGraph + LlamaIndex
* **Vector Store**: Qdrant (Hybrid dense/sparse collections)
* **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Celery + Redis
* **Frontend**: Next.js 14 + TypeScript + Tailwind CSS

---

## Directory Structure

```
paklawai/
├── frontend/           # Next.js 14 app router codebase
├── backend/            # FastAPI application models, services & routers
├── ai/                 # LangGraph workflow pipelines, embeddings & prompt templates
├── workers/            # Celery workers tasks handling ingestion & PDF report exports
├── docker/             # Docker runtime files
├── infrastructure/     # Nginx reverse proxy configuration with SSL routing
├── scripts/            # Database initialization and sample data seeder scripts
├── tests/              # Pytest integration tests suite
├── docker-compose.yml  # Orchestrates full platform execution
└── README.md
```

---

## Getting Started

### 1. Configure the Environment
Create your local environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your details (specifically your Google API Key: `GOOGLE_API_KEY`).

### 2. Launch the Platform via Docker Compose
Run the entire platform including backend, Next.js frontend, Celery workers, Redis, PostgreSQL, and Qdrant:
```bash
docker compose up -d --build
```

### 3. Run Database Migrations
Deploy the database schema via Alembic:
```bash
docker compose exec backend alembic upgrade head
```

### 4. Seed Database & Index the Included Legal Corpus
Load the default RBAC permissions matrix, then index every PDF already supplied in `data/`.
The indexer copies source PDFs into managed upload storage, extracts/chunks their text, and stores
their vectors in Qdrant:
```bash
# Seed default roles and admin (admin@paklaw.ai / Password: PakLawAdmin2026!)
docker compose exec backend python scripts/seed.py

# Index all PDFs from data/
docker compose exec backend python scripts/index_data_folder.py
```

### 5. Running Tests
Run the pytest suite to verify application status:
```bash
docker compose exec backend pytest
```

---

## UI Access Ports

* **Next.js Web Interface**: `http://localhost:3000` (or `https://localhost` if nginx proxy linked)
* **FastAPI Docs**: `http://localhost:8000/docs`
* **Qdrant Dashboard**: `http://localhost:6333/dashboard`
* **Celery Flower Monitor**: `http://localhost:5555`
