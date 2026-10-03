# Local Setup

Status: implemented local demonstrator procedure; scientific dataset/model setup remains pending.

## Required Environment

Use Node 24 with pnpm 12.8.1 and Docker Compose. Backend containers use Python 3.12 as declared in `backend/pyproject.toml` and `backend/Dockerfile`; the host Python is not used by the documented checks. GPU access is not required for the current functional demonstrator.

## Setup Sequence

1. Run `make setup` to install the frozen web lock and build the Python 3.12 backend test image.
2. Review `.env.example`; copy it to the ignored `.env` only when overriding local defaults.
3. Run `make dev`. Compose starts PostgreSQL and RabbitMQ, applies Alembic migrations, seeds labelled fixtures, and starts the API, worker and web proxy.
4. Check `http://localhost:8000/api/health/ready` and open `http://localhost:8080`.
5. Run `make web-check`, `make backend-check`, and `make e2e` as appropriate.

`make services-down` stops containers without deleting named volumes. Do not add `-v` as routine troubleshooting because it destroys persisted local PostgreSQL/artifact state.

The current `scripts/fetch_dataset.py`, training and calibration entry points are placeholders. There is no authorized, hashed C-MAPSS artifact or evaluated model in the workspace. Prediction setup therefore remains blocked and must not be represented as completed by running the functional demo.

## Commands and Troubleshooting

If the API is not ready, inspect `docker compose ps` and `docker compose logs api postgres rabbitmq`. A host with Python 3.14 cannot create the declared backend environment directly because the package supports Python 3.12–3.13; use the documented container target. For browser failures, verify the API health endpoint before Playwright and ensure Chrome is installed. File-access errors from the former `/Users/rax/Desktop/sih-project` location are not evidence about this workspace; rerun from `/Users/rax/Projects/sih-project`.
