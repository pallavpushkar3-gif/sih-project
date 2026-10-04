.PHONY: setup web-check backend-check backend-integration science-check science-train science-evaluate science-calibrate science-robustness sequence-check sequence-train alert-evaluation planner-benchmark simulation-reference test e2e services-up services-down migrate seed dev

setup:
	corepack pnpm install --frozen-lockfile
	docker build --target test -t fleet-maintenance-test backend

web-check:
	corepack pnpm lint
	corepack pnpm typecheck
	corepack pnpm build
	corepack pnpm test:web

backend-check:
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm fleet-maintenance-test sh -c 'ruff check src tests && mypy --exclude "science/prediction/(sequence|sequence_training)\\.py" src/fleet_maintenance && python -m pytest tests/unit tests/verification'

backend-integration: services-up
	docker compose build api
	docker build --target test -t fleet-maintenance-test backend
	docker compose run --rm --no-deps api python -c "from sqlalchemy import create_engine,text; from sqlalchemy.engine import make_url; from fleet_maintenance.settings import get_settings; e=create_engine(make_url(get_settings().database_url).set(database='postgres'),isolation_level='AUTOCOMMIT'); c=e.connect(); c.execute(text('CREATE DATABASE fleet_release_integration_test')) if not c.scalar(text(\"SELECT 1 FROM pg_database WHERE datname='fleet_release_integration_test'\")) else None; c.close(); e.dispose()"
	docker compose run --rm --no-deps -e FLEET_DATABASE_URL=postgresql+psycopg://fleet:fleet@postgres:5432/fleet_release_integration_test api alembic upgrade head
	docker run --rm --network fleet-maintenance_default -e FLEET_DATABASE_URL=postgresql+psycopg://fleet:fleet@postgres:5432/fleet_release_integration_test fleet-maintenance-test python -m pytest tests/integration

science-check:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science sh -c 'ruff check backend/src backend/tests/science scripts && mypy --exclude "science/prediction/(sequence|sequence_training)\\.py" backend/src/fleet_maintenance && python -m pytest backend/tests/science'

science-train:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science python scripts/train_model.py

science-calibrate:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science python scripts/calibrate_model.py

science-robustness:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science python scripts/evaluate_robustness.py --output artifacts/evaluations/robustness-validation-v1.json

sequence-check:
	docker build --target sequence -t fleet-maintenance-sequence backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-sequence sh -c 'ruff check backend/src backend/tests/science scripts && mypy backend/src/fleet_maintenance && python -m pytest backend/tests/science'

sequence-train:
	docker build --target sequence -t fleet-maintenance-sequence backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-sequence python scripts/train_model.py --candidate sequence

alert-evaluation:
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-test python scripts/evaluate_alert_policy.py --output artifacts/evaluations/alert-policy-demo-v1.json

planner-benchmark:
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-test python scripts/benchmark_planner.py --output artifacts/benchmarks/planner-demo-v1.json

simulation-reference:
	docker build --target test -t fleet-maintenance-test backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-test python scripts/run_simulation.py --output artifacts/simulations/reference-demo-v1.json

test: web-check backend-check

e2e: services-up
	docker compose up -d --build api worker outbox
	corepack pnpm --filter @fleet-maintenance/web test:e2e

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

science-evaluate:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science python scripts/evaluate_model.py

.PHONY: explanation-evaluation workload-diagnostic
explanation-evaluation:
	docker build --target science -t fleet-maintenance-science backend
	docker run --rm -v "$(CURDIR):/workspace" -w /workspace -e PYTHONPATH=/workspace/backend/src fleet-maintenance-science python scripts/evaluate_explanations.py

# Host Python environment must have the installable backend package and science dependencies.
workload-diagnostic:
	PYTHONPATH=backend/src .venv313/bin/python scripts/benchmark_workload.py
