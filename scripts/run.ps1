# BoponX Windows PowerShell Helper (Spec v2 Item R)
# Usage:
#   .\scripts\run.ps1 setup      # create .venv and install backend + frontend dependencies
#   .\scripts\run.ps1 snapshot   # download 40 NASA POWER grid-cell snapshots & build onset_results.json
#   .\scripts\run.ps1 test       # run offline backend pytest suite + frontend TypeScript build
#   .\scripts\run.ps1 backend    # start FastAPI backend in LIVE NASA mode on http://127.0.0.1:8000
#   .\scripts\run.ps1 frontend   # start Vite frontend on http://127.0.0.1:5173

param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "snapshot", "test", "backend", "frontend")]
    [string]$Command = "backend"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function Ensure-Venv {
    if (-not (Test-Path $VenvPython)) {
        Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Cyan
        python -m venv .venv
        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -r backend\requirements.txt -r backend\requirements-dev.txt
    }
}

switch ($Command) {
    "setup" {
        Ensure-Venv
        & $VenvPython -m pip install -r backend\requirements.txt -r backend\requirements-dev.txt
        Push-Location frontend
        npm.cmd install
        Pop-Location
        Write-Host "BoponX setup complete." -ForegroundColor Green
    }
    "snapshot" {
        Ensure-Venv
        Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
        Remove-Item Env:BOPONX_OFFLINE -ErrorAction SilentlyContinue
        & $VenvPython -m scripts.build_snapshot
        & $VenvPython -m scripts.build_onset_results
    }
    "test" {
        Ensure-Venv
        $env:OFFLINE = "1"
        try {
            & $VenvPython -m pytest -q backend\tests
        } finally {
            # Always clear OFFLINE after tests so starting uvicorn in the same terminal uses LIVE NASA APIs!
            Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
        }
        Push-Location frontend
        npm.cmd run build
        Pop-Location
    }
    "backend" {
        Ensure-Venv
        # Explicitly clear OFFLINE so live NASA POWER, EONET, and GIBS APIs are active!
        Remove-Item Env:OFFLINE -ErrorAction SilentlyContinue
        Remove-Item Env:BOPONX_OFFLINE -ErrorAction SilentlyContinue
        Write-Host "Starting BoponX Backend in LIVE REAL-TIME NASA MODE on http://127.0.0.1:8000 ..." -ForegroundColor Green
        & $VenvPython -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
    }
    "frontend" {
        Push-Location frontend
        npm.cmd run dev
        Pop-Location
    }
}
