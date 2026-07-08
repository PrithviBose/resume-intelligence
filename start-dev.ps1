<#
.SYNOPSIS
    Starts the full Resume Intelligence local dev stack with one command, entirely inside this terminal.

.DESCRIPTION
    1. docker compose up -d   -> Postgres, ChromaDB, Chroma Admin UI (detached, managed by Docker)
    2. Backend (uvicorn)      -> runs as a background job in THIS PowerShell session
    3. Frontend (next dev)    -> runs as a background job in THIS PowerShell session

    Nothing opens outside your IDE - both jobs' output is streamed live into this same terminal,
    prefixed with [backend]/[frontend] so you can tell them apart.

    Press Ctrl+C to stop watching and shut both jobs down. Docker containers keep running
    (they're managed by the Docker daemon, not this terminal) - use .\stop-dev.ps1 for those.

.USAGE
    From the repo root, in your IDE's integrated terminal:
        .\start-dev.ps1

    If PowerShell blocks the script with an execution-policy error, run it as:
        powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "==> Starting Docker infrastructure (Postgres, Chroma, Chroma Admin)..." -ForegroundColor Cyan
docker compose -f (Join-Path $root "docker-compose.yml") up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "docker compose up failed - is Docker Desktop running? Aborting." -ForegroundColor Red
    exit 1
}

$backendVenvPython = Join-Path $root "backend\venv\Scripts\python.exe"
$backendJob = $null

if (-not (Test-Path $backendVenvPython)) {
    Write-Host "Backend venv not found at $backendVenvPython" -ForegroundColor Yellow
    Write-Host "Create it first: cd backend; python -m venv venv; venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "Continuing without the backend." -ForegroundColor Yellow
} else {
    Write-Host "==> Starting backend (FastAPI + uvicorn) as a background job..." -ForegroundColor Cyan
    $backendJob = Start-Job -Name "backend" -ScriptBlock {
        param($backendDir, $pythonExe)
        Set-Location $backendDir
        & $pythonExe -m uvicorn app.main:app --reload --port 8000 2>&1
    } -ArgumentList (Join-Path $root "backend"), $backendVenvPython
}

Write-Host "==> Starting frontend (Next.js dev server) as a background job..." -ForegroundColor Cyan
$frontendJob = Start-Job -Name "frontend" -ScriptBlock {
    param($frontendDir)
    Set-Location $frontendDir
    npm run dev 2>&1
} -ArgumentList (Join-Path $root "frontend")

Write-Host ""
Write-Host "==> Stack starting up:" -ForegroundColor Green
Write-Host "    Postgres:        localhost:5432"
Write-Host "    Chroma:          localhost:8001"
Write-Host "    Chroma Admin UI: http://localhost:3001"
Write-Host "    Backend API:     http://127.0.0.1:8000/docs"
Write-Host "    Frontend:        http://localhost:3000"
Write-Host ""
Write-Host "Streaming logs below. Press Ctrl+C to stop watching and shut backend/frontend down." -ForegroundColor DarkGray
Write-Host "(Docker containers keep running - use .\stop-dev.ps1 to stop those.)" -ForegroundColor DarkGray
Write-Host ""

try {
    while ($true) {
        if ($backendJob) {
            Receive-Job $backendJob | ForEach-Object { Write-Host "[backend]  $_" -ForegroundColor Cyan }
            if ($backendJob.State -eq "Failed") {
                Write-Host "[backend] job failed - see messages above." -ForegroundColor Red
                $backendJob = $null
            }
        }
        Receive-Job $frontendJob | ForEach-Object { Write-Host "[frontend] $_" -ForegroundColor Magenta }
        if ($frontendJob.State -eq "Failed") {
            Write-Host "[frontend] job failed - see messages above." -ForegroundColor Red
            break
        }

        Start-Sleep -Milliseconds 300
    }
} finally {
    Write-Host ""
    Write-Host "==> Stopping backend/frontend jobs..." -ForegroundColor Cyan
    if ($backendJob) {
        Stop-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
        Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
    }
    Stop-Job $frontendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "Backend/frontend stopped. Docker containers are still running - use .\stop-dev.ps1 to stop those." -ForegroundColor DarkGray
}
