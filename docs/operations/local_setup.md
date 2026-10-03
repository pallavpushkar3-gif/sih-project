# Local Setup

Status: implemented local demonstrator and validation-only scientific procedure; final evaluation and prediction serving remain pending.

## Required Environment

Use Node 24 with pnpm 12.8.1 and Docker Compose. Backend containers use Python 3.12 as declared in `backend/pyproject.toml` and `backend/Dockerfile`; the host Python is not used by the documented checks. GPU access is not required. The sequence target installs the official PyTorch 2.8 CPU wheel separately so ordinary checks do not pull CUDA packages.

## Setup Sequence

1. Run `make setup` to install the frozen web lock and build the Python 3.12 backend test image.
2. Review `.env.example`; copy it to the ignored `.env` only when overriding local defaults.
3. Run `make dev`. Compose starts PostgreSQL and RabbitMQ, applies Alembic migrations, seeds labelled fixtures, and starts the API, worker and web proxy.
4. Check `http://localhost:8000/api/health/ready` and open `http://localhost:8080`.
5. Run `make web-check`, `make backend-check`, and `make e2e` as appropriate.

`make services-down` stops containers without deleting named volumes. Do not add `-v` as routine troubleshooting because it destroys persisted local PostgreSQL/artifact state.

## Validation-only prediction research

1. Run `python scripts/fetch_dataset.py` from a compatible Python environment, or use the documented container approach, to acquire the allowlisted official NASA archive. The command verifies the archive layout and records hashes; existing mismatched files are not silently replaced.
2. Run `scripts/prepare_dataset.py` with `PYTHONPATH=backend/src` in Python 3.12 to validate FD001 and create the ignored engine-split manifest.
3. Run `make science-check` and `make sequence-check`.
4. Run `make science-train`, `make sequence-train`, then `make science-calibrate`.

The commands read the frozen YAML configurations and store their hashes with the ignored artifacts. They use only the supplied FD001 training histories for model selection/calibration. The official test histories and RUL labels remain reserved. The comparison is validation evidence, not a final performance or operational claim, and learned artifacts are not wired into the running demo.

## Commands and Troubleshooting

If the API is not ready, inspect `docker compose ps` and `docker compose logs api postgres rabbitmq`. A host with Python 3.14 cannot create the declared backend environment directly because the package supports Python 3.12–3.13; use the documented container target. For browser failures, verify the API health endpoint before Playwright and ensure Chrome is installed. File-access errors from the former `/Users/rax/Desktop/sih-project` location are not evidence about this workspace; rerun from `/Users/rax/Projects/sih-project`.
