# ============================================================
# PakLaw AI — Backend Local Start Script
# Run: .\start_backend.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$VENV_PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"
$VENV_ACTIVATE = Join-Path $ROOT ".venv\Scripts\Activate.ps1"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  PakLaw AI — Backend Server (Local)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Check virtual environment exists ──────────────────────
if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "[ERROR] Virtual environment not found at .venv/" -ForegroundColor Red
    Write-Host "  Run: python -m venv .venv && .venv\Scripts\pip install -e backend/" -ForegroundColor Yellow
    exit 1
}

# ── 2. Activate venv so all sub-shells use the right Python ──
# This also sets PATH, so 'python' resolves to .venv Python.
if (Test-Path $VENV_ACTIVATE) {
    & $VENV_ACTIVATE
    Write-Host "[INFO] Activated virtualenv: .venv (Python $( & $VENV_PYTHON --version ))" -ForegroundColor Gray
}

# ── 3. Verify critical packages are present ──────────────────
$checks = @("uvicorn", "langchain_groq", "langgraph", "qdrant_client", "fastapi")
$missing = @()
foreach ($pkg in $checks) {
    $result = & $VENV_PYTHON -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) { $missing += $pkg }
}
if ($missing.Count -gt 0) {
    Write-Host "[WARN] Missing packages: $($missing -join ', '). Installing via uv..." -ForegroundColor Yellow
    uv pip install -e "$ROOT\backend" --python $VENV_PYTHON --quiet 2>&1
}

# ── 4. Create required directories ───────────────────────────
$dirs = @("uploads", "uploads\exports", "logs", "data")
foreach ($dir in $dirs) {
    $dirPath = Join-Path $ROOT $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-Host "[INFO] Created directory: $dir" -ForegroundColor Gray
    }
}

# ── 5. Set PYTHONPATH so both backend/ and root ai/ are importable ───
$env:PYTHONPATH = "$ROOT\backend;$ROOT"

Write-Host "[INFO] PYTHONPATH = $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "[INFO] Python     = $VENV_PYTHON" -ForegroundColor Gray
Write-Host ""
Write-Host "[INFO] Starting FastAPI backend on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "[INFO] API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "[INFO] Health:    http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# ── 6. Start uvicorn with the correct venv Python ────────────
# Watch both backend/ (app code) and ai/ (AI graphs/pipelines) for hot-reload.
Set-Location (Join-Path $ROOT "backend")
& $VENV_PYTHON -m uvicorn app.main:app `
    --host 127.0.0.1 `
    --port 8000 `
    --reload `
    --reload-dir (Join-Path $ROOT "backend") `
    --reload-dir (Join-Path $ROOT "ai") `
    --log-level info
