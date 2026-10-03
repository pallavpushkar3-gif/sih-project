.PHONY: setup web-check backend-check backend-integration test e2e services-up services-down migrate seed dev

setup:
	corepack enable
	pnpm install --frozen-lockfile
	docker build --target test -t fleet-maintenance-test backend

web-check:
	pnpm lint
	pnpm typecheck
	pnpm build
	pnpm test:web

backend-check:
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm fleet-maintenance-test sh -c 'ruff check src tests && mypy src/fleet_maintenance && python -m pytest tests/unit tests/verification'

backend-integration: services-up
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm --network fleet-maintenance_default -e FLEET_DATABASE_URL=postgresql+psycopg://fleet:fleet@postgres:5432/fleet fleet-maintenance-test python -m pytest tests/integration

test: web-check backend-check

e2e: services-up
	docker compose up -d --build api
	pnpm --filter @fleet-maintenance/web test:e2e

services-up:
	docker compose up -d postgres rabbitmq

services-down:
	docker compose down

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose exec api python -c 'from fleet_maintenance.persistence.database import SessionLocal; from fleet_maintenance.services.records import seed_demo; s=SessionLocal(); print("seeded" if seed_demo(s) else "already seeded"); s.close()'

dev:
	docker compose up --build
