# ============================================================
# PakLaw AI — Backend Local Start Script
# Run: .\start_backend.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$VENV = Join-Path $ROOT ".venv\Scripts\python.exe"
$PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  PakLaw AI — Backend Server (Local)" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path $VENV)) {
    Write-Host "[ERROR] Virtual environment not found at .venv/" -ForegroundColor Red
    Write-Host "  Run: python -m venv .venv && .venv\Scripts\pip install -e backend/" -ForegroundColor Yellow
    exit 1
}

# Check uvicorn
$uvicornCheck = & $PYTHON -c "import uvicorn; print('ok')" 2>&1
if ($uvicornCheck -ne 'ok') {
    Write-Host "[INFO] uvicorn not found, installing..." -ForegroundColor Yellow
    & (Join-Path $ROOT ".venv\Scripts\pip.exe") install "uvicorn[standard]" --quiet
}

# Create required directories
$dirs = @("uploads", "logs", "data")
foreach ($dir in $dirs) {
    $dirPath = Join-Path $ROOT $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-Host "[INFO] Created directory: $dir" -ForegroundColor Gray
    }
}

# Set environment
$env:PYTHONPATH = "$ROOT\backend;$ROOT"

Write-Host "[INFO] Starting FastAPI backend on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "[INFO] API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "[INFO] Health:   http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn via python -m
Set-Location (Join-Path $ROOT "backend")
& $PYTHON -m uvicorn app.main:app `
    --host 127.0.0.1 `
    --port 8000 `
    --reload `
    --reload-dir (Join-Path $ROOT "backend") `
    --reload-dir (Join-Path $ROOT "ai") `
    --log-level info
