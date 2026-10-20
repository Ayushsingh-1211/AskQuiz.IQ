#!/usr/bin/env bash
set -e

echo "==> Starting database container..."
docker compose -f infra/docker-compose.yml up -d

echo "==> Waiting for database to become ready..."
for i in {1..30}; do
    if python -c "from apps.api.app.db.session import check_db_health; exit(0 if check_db_health() else 1)"; then
        echo "Database is ready."
        break
    fi
    sleep 1
done

echo "==> Running migrations..."
python -c "from apps.api.app.db.session import run_migrations; run_migrations()"

echo "==> Seeding users..."
python infra/scripts/seed_users.py

echo "==> Running preflight checks..."
python infra/scripts/preflight.py || true

echo "==> Starting API server in background..."
python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

trap "kill $API_PID" EXIT

echo "==> Starting Cloudflare Tunnel..."
cloudflared tunnel --url http://localhost:8000
