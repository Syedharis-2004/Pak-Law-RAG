# PakLaw AI — مکمل یوزر گائیڈ
## (Local Development Guide — Docker کے بغیر)

> [!NOTE]
> یہ guide Docker کے بغیر PakLaw AI کو locally چلانے کے لیے ہے۔  
> تمام Docker files `docker/_archived/` میں محفوظ ہیں۔

---

## فہرست (Table of Contents)

1. [پروجیکٹ کا تعارف](#پروجیکٹ-کا-تعارف)
2. [System Requirements](#system-requirements)
3. [پروجیکٹ Structure](#پروجیکٹ-structure)
4. [پہلی بار Setup](#پہلی-بار-setup)
5. [پروجیکٹ چلانا](#پروجیکٹ-چلانا)
6. [Environment Variables](#environment-variables)
7. [API Endpoints](#api-endpoints)
8. [Optional Services](#optional-services)
9. [Troubleshooting](#troubleshooting)

---

## پروجیکٹ کا تعارف

**PakLaw AI** ایک enterprise-grade AI legal platform ہے جو Pakistani law کے لیے بنایا گیا ہے۔

### اہم Features:
| Feature | تفصیل |
|---------|--------|
| 🔐 Authentication | JWT-based secure login/register |
| 📄 Document Management | PDF, DOCX, TXT upload اور indexing |
| 💬 AI Chat | Gemini AI سے قانونی سوالات |
| 🔍 Hybrid Search | Vector + keyword search |
| 📊 Research Reports | AI-generated legal reports |
| 🌐 Bilingual | Urdu اور English دونوں support |

### Technology Stack:
| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12+) |
| Database | SQLite (local dev) + MongoDB Atlas |
| AI Model | Google Gemini 2.5 Pro |
| Frontend | Next.js 14 |
| Vector DB | Qdrant (optional) |
| Task Queue | Celery + Redis (optional) |

---

## System Requirements

### ضروری (Required):
- ✅ **Python 3.12+** — `python --version`
- ✅ **Node.js 18+** — `node --version`
- ✅ **npm** — `npm --version`

### اختیاری (Optional):
- ⚡ **Redis** — Celery task queue کے لیے (document background processing)
- 🔍 **Qdrant** — Vector/semantic search کے لیے

> [!TIP]
> **Redis اور Qdrant کے بغیر بھی** یہ features کام کرتے ہیں:
> - ✅ Login / Register
> - ✅ Document Upload
> - ✅ AI Chat
> - ✅ Basic Search
> - ❌ Background processing (Celery workers)
> - ❌ Semantic vector search (Qdrant)

---

## پروجیکٹ Structure

```
e:\Haris\PAK LAW\
│
├── 📁 backend/              ← FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/          ← API Routes (auth, chat, docs, search)
│   │   ├── core/            ← Config, Database, Security
│   │   ├── models/          ← SQLAlchemy ORM Models
│   │   ├── services/        ← Business Logic
│   │   └── main.py          ← App Entry Point
│   └── pyproject.toml       ← Python Dependencies
│
├── 📁 frontend/             ← Next.js Frontend
│   ├── src/
│   └── package.json
│
├── 📁 ai/                   ← AI/ML Pipeline
│   ├── embeddings/          ← BGE-M3 Embedding
│   ├── pipelines/           ← Document ingestion
│   ├── prompts/             ← Gemini prompts
│   └── qdrant/              ← Vector store client
│
├── 📁 workers/              ← Celery Background Workers
├── 📁 docker/_archived/     ← Docker files (archived, not deleted)
│
├── 📄 .env                  ← Environment Variables
├── 📄 start_backend.ps1     ← ✅ Backend Start Script
├── 📄 start_frontend.ps1    ← ✅ Frontend Start Script
└── 📄 start_all.ps1         ← ✅ دونوں ایک ساتھ Start
```

---

## پہلی بار Setup

### Step 1: Python Virtual Environment بنائیں
```powershell
cd "e:\Haris\PAK LAW"
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> [!WARNING]
> اگر execution policy error آئے:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 2: Backend Dependencies Install کریں
```powershell
pip install -e backend/
pip install "uvicorn[standard]" aiosqlite
```

### Step 3: Frontend Dependencies Install کریں
```powershell
cd frontend
npm install
cd ..
```

### Step 4: Environment Variables چیک کریں
`.env` file پہلے سے configured ہے۔ یہ values verify کریں:

```env
# Google Gemini API Key (ضروری!)
GOOGLE_API_KEY=your_actual_api_key_here

# Database (SQLite - local dev, already set)
DATABASE_URL=sqlite+aiosqlite:///./paklawai_local.db

# MongoDB (already configured with Atlas)
MONGODB_URL=mongodb+srv://...
USE_MONGODB=true
```

> [!CAUTION]
> `GOOGLE_API_KEY` بغیر AI chat کام نہیں کرے گا۔  
> Key یہاں سے لیں: https://aistudio.google.com/apikey

---

## پروجیکٹ چلانا

### 🚀 آسان طریقہ — سب کچھ ایک ساتھ

```powershell
cd "e:\Haris\PAK LAW"
.\start_all.ps1
```

یہ script دونوں servers الگ الگ windows میں start کرتی ہے۔

---

### صرف Backend چلانا

```powershell
cd "e:\Haris\PAK LAW"
.\start_backend.ps1
```

**یا manually:**
```powershell
$env:PYTHONPATH = "e:\Haris\PAK LAW\backend;e:\Haris\PAK LAW"
cd "e:\Haris\PAK LAW\backend"
.\..\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### صرف Frontend چلانا

```powershell
cd "e:\Haris\PAK LAW"
.\start_frontend.ps1
```

**یا manually:**
```powershell
cd "e:\Haris\PAK LAW\frontend"
npm run dev
```

---

### URLs جب سب چل رہا ہو:

| URL | مقصد |
|-----|------|
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | Swagger API Docs (interactive) |
| http://localhost:8000/redoc | ReDoc API Docs |
| http://localhost:8000/health | System Health Status |
| http://localhost:3000 | Frontend UI |

---

## Environment Variables

`.env` file میں اہم settings کی تفصیل:

### Application:
```env
APP_ENV=development
APP_NAME=PakLaw AI
APP_SECRET_KEY=...          # Security key
DEBUG=true
```

### Database:
```env
# SQLite (local development - no install needed)
DATABASE_URL=sqlite+aiosqlite:///./paklawai_local.db
SYNC_DATABASE_URL=sqlite:///./paklawai_local.db

# MongoDB Atlas (chat history, documents)
MONGODB_URL=mongodb+srv://user:pass@cluster/db
MONGODB_DB_NAME=paklawai
USE_MONGODB=true
```

### AI Model:
```env
GOOGLE_API_KEY=...          # Gemini API key (ضروری)
GEMINI_MODEL=gemini-2.5-pro
GEMINI_TEMPERATURE=0.1
```

### JWT Security:
```env
JWT_SECRET_KEY=...
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Optional Redis/Qdrant:
```env
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

---

## API Endpoints

### Authentication:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `POST` | `/api/v1/auth/register` | نیا account بنائیں |
| `POST` | `/api/v1/auth/login` | Login |
| `GET` | `/api/v1/auth/me` | اپنی profile دیکھیں |
| `POST` | `/api/v1/auth/refresh` | Token refresh |
| `POST` | `/api/v1/auth/logout` | Logout |

### Documents:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `POST` | `/api/v1/documents/upload` | File upload |
| `GET` | `/api/v1/documents/` | Documents list |
| `GET` | `/api/v1/documents/{id}` | Document detail |
| `DELETE` | `/api/v1/documents/{id}` | Delete |

### Chat:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `POST` | `/api/v1/chat/conversations` | New conversation |
| `GET` | `/api/v1/chat/conversations` | تمام conversations |
| `POST` | `/api/v1/chat/conversations/{id}/messages` | Message بھیجیں |
| `GET` | `/api/v1/chat/conversations/{id}/messages` | Messages history |

### Search:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `POST` | `/api/v1/search/` | قانونی دستاویزات search |

### Research:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `POST` | `/api/v1/research/generate` | AI research report generate |
| `GET` | `/api/v1/research/` | Reports list |
| `GET` | `/api/v1/research/{id}` | Report detail |

### System:
| Method | Endpoint | تفصیل |
|--------|----------|--------|
| `GET` | `/health` | System health check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc UI |

> [!TIP]
> http://localhost:8000/docs پر جائیں، **Authorize** button کلک کریں اور login token paste کریں — پھر تمام APIs براہ راست test کر سکتے ہیں۔

---

## Optional Services

### Redis — Celery Workers کے لیے

Background document processing (embedding, OCR) کے لیے Redis ضروری ہے۔

**Windows پر install:**

```powershell
# Option 1: Docker (آسان)
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Option 2: WSL (Linux subsystem)
wsl --install
# WSL terminal میں:
sudo apt update && sudo apt install redis-server -y
redis-server --daemonize yes

# Option 3: Memurai (Windows native)
# Download: https://www.memurai.com/get-memurai
```

**Celery Worker چلانا:**
```powershell
$env:PYTHONPATH = "e:\Haris\PAK LAW\backend;e:\Haris\PAK LAW"
cd "e:\Haris\PAK LAW"
.venv\Scripts\python.exe -m celery -A workers.celery_app worker -Q ingestion -c 2 --loglevel=info
```

---

### Qdrant — Vector Search کے لیے

AI semantic search کے لیے Qdrant vector database چاہیے۔

**Option 1: Docker (آسان)**
```powershell
docker run -d -p 6333:6333 -p 6334:6334 `
    -v "${PWD}/backend/qdrant_db:/qdrant/storage" `
    --name qdrant qdrant/qdrant:latest
```

**Option 2: Qdrant Cloud (مفت tier)**
1. https://cloud.qdrant.io پر account بنائیں
2. Cluster create کریں (free tier available)
3. `.env` update کریں:
```env
QDRANT_HOST=your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-api-key-here
QDRANT_HTTPS=true
QDRANT_PORT=6333
```

---

## Troubleshooting

### ❌ ModuleNotFoundError
```powershell
# PYTHONPATH manually set کریں
$env:PYTHONPATH = "e:\Haris\PAK LAW\backend;e:\Haris\PAK LAW"
```

### ❌ uvicorn not found
```powershell
# python -m uvicorn use کریں
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

### ❌ Database Error / Tables Missing
```powershell
# SQLite file delete کریں (auto-recreate ہوگا)
Remove-Item "e:\Haris\PAK LAW\backend\paklawai_local.db" -ErrorAction SilentlyContinue
# Backend restart کریں
```

### ❌ Redis Connection Error (Health endpoint میں)
Normal behavior ہے اگر Redis install نہیں۔  
Backend پھر بھی کام کرتی رہتی ہے — صرف Celery disabled ہوتا ہے۔

### ❌ MongoDB Connection Error
```env
# .env میں MongoDB URL verify کریں
MONGODB_URL=mongodb+srv://correct_user:correct_pass@cluster.mongodb.net/paklawai
```

### ❌ CORS Error (Frontend سے)
```env
# .env میں
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# frontend/.env.local میں
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### ❌ PowerShell Execution Policy
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ Port Already in Use
```powershell
# Port 8000 use کرنے والا process دیکھیں
netstat -ano | findstr ":8000"
# Process kill کریں (PID replace کریں)
taskkill /PID <PID> /F
```

---

## ✅ Verified Test Results

یہ guide بنانے کے وقت درج ذیل verified تھا:

| Component | Status | Details |
|-----------|--------|---------|
| Backend Startup | ✅ | `http://0.0.0.0:8000` پر چل رہا |
| SQLite Database | ✅ Connected | `paklawai_local.db` auto-created |
| MongoDB Atlas | ✅ Connected | Indexes created |
| Health Endpoint | ✅ `{"status":"healthy"}` | |
| API Docs | ✅ HTTP 200 | Swagger UI available |
| Auth Routes | ✅ Working | Correct 405/401 responses |
| Redis | ⚠️ Not running | Optional — install if needed |
| Qdrant | ⚠️ Not running | Optional — install if needed |

---

*PakLaw AI v1.0.0 — User Guide*  
*Generated: 2026-07-26*
