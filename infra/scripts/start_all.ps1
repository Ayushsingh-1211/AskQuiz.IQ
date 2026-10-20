# Start all services for AskQuiz.IQ
$ErrorActionPreference = "Stop"

Write-Host "==> Starting database container..."
docker compose -f infra/docker-compose.yml up -d

Write-Host "==> Waiting for database to become ready..."
$maxAttempts = 30
$attempt = 0
$dbReady = $false
while (-not $dbReady -and $attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 1
    $attempt++
    try {
        python -c "from apps.api.app.db.session import check_db_health; exit(0 if check_db_health() else 1)"
        if ($LASTEXITCODE -eq 0) {
            $dbReady = $true
        }
    } catch {}
}

if (-not $dbReady) {
    Write-Error "Database failed to become ready in time."
    exit 1
}

Write-Host "==> Running migrations..."
python -c "from apps.api.app.db.session import run_migrations; run_migrations()"

Write-Host "==> Seeding users..."
python infra/scripts/seed_users.py

Write-Host "==> Running preflight checks..."
python infra/scripts/preflight.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Preflight checks reported issues; proceeding..."
}

Write-Host "==> Starting API server in background..."
$apiJob = Start-Process python -ArgumentList "-m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000" -PassThru

Write-Host "==> Starting Cloudflare Tunnel..."
$cfPath = "cloudflared"
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    if (Test-Path "C:\Program Files (x86)\cloudflared\cloudflared.exe") {
        $cfPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    } elseif (Test-Path "C:\Program Files\cloudflared\cloudflared.exe") {
        $cfPath = "C:\Program Files\cloudflared\cloudflared.exe"
    }
}

& $cfPath tunnel --url http://localhost:8000
