.PHONY: db-up db-down api worker web test eval health preflight

db-up:
	docker compose -f infra/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker-compose.yml down

api:
	python -m uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	python apps/api/app/worker.py

web:
	npm --prefix apps/web run dev

test:
	pytest tests/conftest.py

eval:
	python core/eval/runner.py

health:
	python infra/scripts/preflight.py
