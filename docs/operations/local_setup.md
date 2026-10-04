# Local Setup

Status: implemented local demonstrator, integrated prediction serving and completed frozen FD001 final evaluation. See production_readiness.md for release limitations.

## Required Environment

Use Node 24 with pnpm 12.8.1 and Docker Compose. Backend containers use Python 3.13 as declared in `backend/pyproject.toml` and `backend/Dockerfile`; the host Python is not used by the documented checks. GPU access is not required. The sequence target installs the official PyTorch 2.8 CPU wheel separately so ordinary checks do not pull CUDA packages.

## Setup Sequence

1. Run `make setup` to install the frozen web lock and build the Python 3.13 backend test image.
2. Review `.env.example`; copy it to the ignored `.env` only when overriding local defaults.
3. Run `make dev`. Compose starts PostgreSQL and RabbitMQ, applies Alembic migrations, seeds labelled fixtures, and starts the API, outbox dispatcher, worker and web proxy.
4. Check `http://localhost:8000/api/health/ready` and open `http://localhost:8080`.
5. Run `make web-check`, `make backend-check`, and `make e2e` as appropriate.

`make services-down` stops containers without deleting named volumes. Do not add `-v` as routine troubleshooting because it destroys persisted local PostgreSQL/artifact state.

## Prediction research and serving

1. Run `python scripts/fetch_dataset.py` from a compatible Python environment, or use the documented container approach, to acquire the allowlisted official NASA archive. The command verifies the archive layout and records hashes; existing mismatched files are not silently replaced.
2. Run `scripts/prepare_dataset.py` with `PYTHONPATH=backend/src` in Python 3.13 to validate FD001 and create the ignored engine-split manifest.
3. Run `make science-check` and `make sequence-check`.
4. Run `make science-train`, `make sequence-train`, then `make science-calibrate`.

The commands read the frozen YAML configurations and store their hashes with the ignored artifacts. They use only the supplied FD001 training histories for model selection/calibration. The training/calibration commands do not consume official test labels. After the user approved the frozen targets, `make science-evaluate` was run on the official final test. Later tuning must disclose that inspection. Install the selected artifact directory under FLEET_ARTIFACT_ROOT and register it through POST /api/models/registrations as an administrator; import a supported component history, then submit POST /api/jobs/assessment. The default seed contains no fabricated predictions.

## Commands and Troubleshooting

If the API is not ready, inspect `docker compose ps` and `docker compose logs api postgres rabbitmq`. A host with Python 3.14 cannot create the declared backend environment directly because the package supports Python 3.13–3.13; use the documented container target. For browser failures, verify the API health endpoint before Playwright and ensure Chrome is installed. Run commands from the actual repository root. Corepack invokes the pinned pnpm without requiring host shim installation.
