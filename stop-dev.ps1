<#
.SYNOPSIS
    Stops the Docker infrastructure started by start-dev.ps1.

.DESCRIPTION
    Backend and frontend run as background jobs inside the same terminal as start-dev.ps1 -
    press Ctrl+C there to stop those two. This script only tears down the Docker containers
    (Postgres, Chroma, Chroma Admin), since those run detached via the Docker daemon and
    keep running even after start-dev.ps1's terminal is closed.

.USAGE
    From the repo root:
        .\stop-dev.ps1
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "==> Stopping Docker infrastructure (Postgres, Chroma, Chroma Admin)..." -ForegroundColor Cyan
docker compose -f (Join-Path $root "docker-compose.yml") down

Write-Host ""
Write-Host "Docker infrastructure stopped. If start-dev.ps1 is still running in another terminal, press Ctrl+C there to stop backend/frontend too." -ForegroundColor DarkGray

