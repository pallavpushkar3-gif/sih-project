# Aircraft Predictive Maintenance & Fleet Availability

PS 26249 is a local decision-workspace demonstrator connecting labelled component records, maintenance constraints, inventory reservations and scenario-specific availability simulation. It is not an airworthiness, dispatch or operational-readiness system.

## Current implemented boundary

The repository currently provides:

- a React/TypeScript/Vite interface for fleet, component evidence, alerts, planning, inventory and simulation scenarios;
- a FastAPI/SQLAlchemy API with an Alembic schema and labelled synthetic demo records;
- PostgreSQL-backed proposal approval with current-input checks, row locking, reservations and audit records;
- an OR-Tools CP-SAT planner with independent checks for windows, capacity, fixed work, precedence and aggregate stock;
- deterministic SimPy reference scenarios with explicit aircraft-time availability, queue wait and horizon handling;
- Celery/RabbitMQ durable job execution with PostgreSQL outbox dispatch, attempt claiming, cancellation and stale-result rejection; and
- unit, verification, API and browser workflow checks.

A reproducible, local-only NASA C-MAPSS FD001 research pipeline now validates and partitions engines, compares an engineered gradient-boosting baseline with a CPU LSTM under a common validation protocol, and calibrates the selected baseline on separate engines. Bulk data and artifacts remain ignored and prediction remains deliberately unavailable in the running demo until serving/evidence integration and final acceptance decisions are complete. The unresolved scientific budgets in `docs/research/evaluation_protocol.md` prevent a supported final RUL-quality claim.

## Prerequisites

- Docker with Compose
- Node.js 24 and Corepack/pnpm 12

The backend image uses Python 3.12, matching `backend/pyproject.toml`. A host Python installation is not required.

## Setup and run

```sh
make setup
make dev
```

Open <http://localhost:8080>. The Compose stack migrates PostgreSQL and seeds the labelled demo records on first API startup. RabbitMQ management is exposed at <http://localhost:15672> for local inspection only.

Environment defaults are in `.env.example`. Do not use the demonstration credentials or session secret outside local development.

## Verified checks

```sh
make web-check
make backend-check
make backend-integration
make e2e
make science-check
make sequence-check
```

`make web-check` runs ESLint, TypeScript, the production build and Vitest. `make backend-check` builds the Python 3.12 test image, then runs Ruff, mypy, and the unit/verification suites. `make backend-integration` runs the integration tests against PostgreSQL, including the concurrent stock-reservation race. `make e2e` starts PostgreSQL, RabbitMQ, the API, outbox dispatcher and worker before running Playwright in Chrome.

PostgreSQL-specific reservation races and broker/process fault injection require the integration environment described in `docs/operations/local_setup.md`; SQLite results must not be used as evidence for those criteria.

After acquiring and preparing FD001 as documented in `docs/operations/local_setup.md`, `make science-train`, `make sequence-train`, `make science-calibrate`, and `make science-robustness` reproduce the validation-only model, calibration, and robustness comparisons. These commands do not inspect the official final test labels.

`make planner-benchmark` compares CP-SAT with the transparent earliest-deadline baseline on the configured deterministic reference instances and writes an ignored result manifest.
`make simulation-reference` runs the matched, explicitly synthetic capacity scenarios and retains per-run metrics without fabricating variability for the single deterministic replication.
`make alert-evaluation` compares the configured hysteresis policy with a no-hysteresis threshold baseline on fixed synthetic validation histories. Its report remains non-accepting while alert budgets are unset.

## Data and claims

- Fleet, tasks, stock, durations, capacities and scenario assumptions are synthetic demonstration inputs.
- Scenario outputs are simulated projections, not observed fleet improvements.
- Sensor names retain generic C-MAPSS-style identifiers unless a source provides a validated physical mapping.
- Bulk data, learned weights and generated result artifacts are intentionally excluded from Git and require manifests/hashes.

See `intent.md`, `scope.md`, `rule.md`, and `docs/product/acceptance_criteria.md` for the governing product and evidence boundaries.
