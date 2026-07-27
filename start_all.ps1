# ============================================================
# PakLaw AI — Full Stack Local Start Script
# Starts Backend + Frontend in separate windows
# Run: .\start_all.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$ROOT = $PSScriptRoot

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  PakLaw AI — Full Stack Local Setup" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# ── Check optional services ───────────────────────────────
Write-Host "[CHECK] Checking optional services..." -ForegroundColor Gray

# Redis check
$redisOk = (Test-NetConnection -ComputerName localhost -Port 6379 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue).TcpTestSucceeded
if ($redisOk) {
    Write-Host "  [OK]   Redis  — localhost:6379 (running)" -ForegroundColor Green
}
else {
    Write-Host "  [WARN] Redis  — NOT running (Celery workers disabled)" -ForegroundColor Yellow
}

# Qdrant check
$qdrantOk = (Test-NetConnection -ComputerName localhost -Port 6333 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue).TcpTestSucceeded
if ($qdrantOk) {
    Write-Host "  [OK]   Qdrant — localhost:6333 (running)" -ForegroundColor Green
}
else {
    Write-Host "  [WARN] Qdrant — NOT running (vector search disabled)" -ForegroundColor Yellow
    Write-Host "         Tip: docker run -p 6333:6333 qdrant/qdrant" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[INFO] Launching Backend and Frontend in separate windows..." -ForegroundColor Cyan
Write-Host ""

# Start Backend in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $ROOT "start_backend.ps1") -WindowStyle Normal

Start-Sleep -Seconds 3

# Start Frontend in new PowerShell window
Start-Process powershell -ArgumentList "-NoExit", "-File", (Join-Path $ROOT "start_frontend.ps1") -WindowStyle Normal

Write-Host "=====================================================" -ForegroundColor Green
Write-Host "  Both servers launching in separate windows!" -ForegroundColor Green
Write-Host "" 
Write-Host "  Backend:  http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Health:   http://127.0.0.1:8000/health" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Magenta
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""
