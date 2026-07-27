# ============================================================
# PakLaw AI — Frontend Local Start Script
# Run: .\start_frontend.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$FRONTEND = Join-Path $ROOT "frontend"

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Magenta
Write-Host "  PakLaw AI — Frontend Server (Local)" -ForegroundColor Magenta
Write-Host "=====================================================" -ForegroundColor Magenta
Write-Host ""

# Check node_modules
if (-not (Test-Path (Join-Path $FRONTEND "node_modules"))) {
    Write-Host "[INFO] Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $FRONTEND
    npm install
} else {
    Write-Host "[INFO] node_modules already installed" -ForegroundColor Green
}

Write-Host "[INFO] Starting Next.js frontend on http://localhost:3000" -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

Set-Location $FRONTEND
npm run dev
