# Master Build Prompt — PS 26249

Paste the prompt below into your coding agent in the project workspace after splitting the master documentation bundle. This authorizes local implementation and verification, not publication or deployment to an external environment.

---

You are the implementation agent for **Aircraft Predictive Maintenance & Fleet Availability — PS 26249**.

Build the documented product in the currently open workspace. Carry implementation through integration and appropriate verification; do not stop at a plan, scaffold or attractive mock interface. Work autonomously within this authorized scope, preserving unrelated existing work.

## 1. Establish the Actual Starting State

Inspect the workspace and applicable AGENTS.md instructions. Read:

- `intent.md`, `scope.md`, `design.md`, `rule.md`.
- `docs/product/feature_specifications.md` and `acceptance_criteria.md`.
- Relevant research, engineering, UI and decision documents.

Verify that the master bundle was correctly split. Distinguish completed documentation, placeholder source/configuration and implemented code. Do not assume dependencies or services run because files exist.

If expected documentation is missing, recover it from the provided master bundle when available. If both are unavailable, explain the specific missing specification and ask for it while continuing independent setup work that does not depend on it.

Maintain a concise implementation plan and evidence-based progress updates. Inspect existing implementations before replacing anything. Resolve routine choices within the agreed architecture yourself. Ask only for genuinely required missing information or authorization, not ordinary reversible implementation steps.

## 2. Architecture to Implement

- React + TypeScript + Vite frontend.
- Radix UI, Tailwind CSS, TanStack Query and Apache ECharts.
- Python + FastAPI + Pydantic + Uvicorn application API.
- One installable Python package shared by API, scripts and workers.
- PostgreSQL + SQLAlchemy + Alembic.
- Celery + RabbitMQ, with durable job/attempt state and an outbox.
- PyTorch plus scikit-learn/XGBoost prediction comparators.
- OR-Tools CP-SAT maintenance planning.
- SimPy/NumPy simulation.
- MLflow/manifest-based research provenance.
- Docker Compose service topology and persistent artifact storage.

Choose compatible maintained stable dependency versions, verify them against official documentation as needed, and generate real lockfiles. Keep substantive rules/transformations shared. Do not introduce a second Rust/Go/Node backend, additional database or external inference API without a measured reason and a documented architecture decision.

Use the existing structure as a responsibility map. Create coherent modules as needed rather than filling every planned source file with empty classes or unnecessary abstractions.

## 3. First Make the Environment Runnable

Replace configuration placeholders with valid manifests, TypeScript/Python settings, environment templates, containers and service wiring. Install dependencies in workspace-appropriate isolated environments. Generate actual locks, migrations and API clients through their tools.

Implement safe local configuration, readiness checks, labelled fixture seeding and verified setup/check commands. Do not overwrite real credentials or commit secrets. Do not destroy existing persistent volumes as a routine reset. Inspect actual environment capabilities; if Docker/GPU/another capability is unavailable, document that limitation and use a technically valid local alternative where available. Do not bypass an access restriction.

Validate frontend build/type checks, backend imports/configuration and available service startup before proceeding. Do not label setup complete while a required service is unavailable.

## 4. Build in Dependency Order

### Stage A — Records, Contracts and Provenance

Implement operational entities, supported imports, source/version/unit validation and corrections. Add small clearly synthetic fleet, task, resource, stock and scenario fixtures. Implement API contracts and generated frontend access. Establish sessions/permissions and the shared application shell.

Verify deduplication, invalid-input handling, record relationships and versioned provenance. Preserve the distinction between actual observations and synthetic logistics.

### Stage B — Prediction, Uncertainty and Evidence

Acquire the documented public engine dataset through an authorized source when accessible. Record actual hashes/usage metadata. Follow engine-level partitioning and namespace train/test identities correctly. Freeze split, target, transformation, calibration and evaluation definitions before relevant final evaluations.

Implement a reproducible classical baseline and a sequence comparator. Fit transformations only on permitted data; reuse them for inference. Implement evaluated uncertainty and version-aligned evidence. Historical replay must exclude future observations/labels.

Train/evaluate with resources actually available. Select the predictor using results, not a preference for neural complexity. Record unsuccessful experiments and provisional findings. If acquisition/training is blocked, implement and verify independent pipeline code, expose the blocked/unavailable state and report the remaining blocker; do not substitute fake predictions as working ML.

### Stage C — Quality and Alerts

Implement validated input-quality findings, qualified/withheld assessment states and explicit imputation provenance. Implement the versioned stable-alert policy and its history. Compare it with a simple threshold baseline. Keep acknowledgement distinct from resolution; missing predictions do not clear mandatory tasks.

### Stage D — Maintenance Planning and Inventory

Implement finite-horizon constraints, deadlines, qualifications/capacities, parts timing, precedence and commitments. Include a simple scheduling baseline and independently validate usable solver outputs. Distinguish optimal, feasible, infeasible, unknown/time limit, invalid and failed results.

Implement compatible grouping and visible bottlenecks. Approval rechecks current inputs and atomically commits reservations/work/audit history. Verify stock races, stale proposals, repeated requests, rollback and reservation/consumption lifecycle. A proposal alone consumes nothing.

### Stage E — Simulation and Comparisons

Implement versioned scenarios, explicit cycle/calendar usage, maintenance-effect assumptions and availability definitions. Verify deterministic reference cases before stochastic comparisons. Compare policies on matched scenarios; preserve seeds, per-run outputs and variability.

Never interpret an interval as a full failure-time probability distribution without a justified method. If using sensitivity scenarios, label them. Simulation must not mutate live inventory/plans. Report worse outcomes honestly and avoid invented benefits.

### Stage F — Durable Computation and Connected Interface

Integrate job/outbox/attempt handling as stages require it; do not postpone reliability until the end. Separate calculations from web handlers. Handle duplicate delivery, dispatch interruption, worker restart, retries, cancellation and rejected stale results. Persist outputs before success events. Provide authoritative status retrieval plus authorized SSE updates.

Complete fleet/component/evidence/alerts/planning/inventory/scenario screens. Provide a usable timeline and equivalent task details/forms. Implement loading, empty, error, denied, stale and degraded states; keyboard/focus and text equivalents for warning colours. No production screen may silently substitute hard-coded model or optimizer results.

## 5. Resolve Evaluation Decisions Honestly

Some numerical acceptance budgets remain unresolved in the documentation. Identify them before evaluating the corresponding final test. Establish proposed budgets from declared application needs or validation-only experiments, record their rationale/support boundary, and freeze them before test inspection. If a decision genuinely depends on stakeholder input, keep its acceptance criterion blocked and continue independent implementation.

Do not tune budgets after seeing final results just to pass. Separate functional acceptance from predictive quality and operational claims. Zero violations in accepted schedules and consistent reservations are mandatory invariants; numerical scientific/performance targets require their own documented basis.

## 6. Required Verification

Run appropriate checks for each stage and the acceptance criteria. Prioritize:

- Frontend/backend types, build/import and contract agreement.
- Engine-split leakage, cutoff isolation and training/inference parity.
- Evaluated error, interval coverage/width and robustness.
- Alert reference cases and baseline tradeoffs.
- Independent schedule validation and solver-result semantics.
- Stock concurrency, stale approval, idempotency and partial failures.
- Simulation reference cases, resource/state invariants and matched comparisons.
- Job fault/restart/duplicate/cancellation cases.
- Evidence-to-plan, scenario comparison and degraded-data E2E flows.

Use PostgreSQL/RabbitMQ for tests whose correctness depends on them. Do not claim SQLite or in-memory mocks prove PostgreSQL concurrency or durable broker recovery. Use small deterministic fixtures where appropriate; do not download/train huge datasets on every ordinary test run.

Run workload/hardware-specific performance checks once meaningful. No generic framework benchmark proves this application's performance. Record exact commands, outcomes and unavailable checks. Do not create a passing test that merely asserts a hard-coded implementation output.

## 7. Documentation and Completion

Update README with verified setup/demo/check commands and actual status. Update reproduction logs with actual experiments and artifacts. Keep evidence linked to revisions/configurations. Maintain contracts, data model and decisions when implementation materially changes them.

Treat the product as complete only when its required documented workflow works, appropriate acceptance evidence exists and unresolved blockers are disclosed. A working interface with unavailable prediction or unverified scientific budgets is a partial implementation, not the full validated product.

Provide a final report containing:

1. What is actually implemented and how to run it locally.
2. Changes and major implementation decisions.
3. Checks/experiments actually run and their results.
4. Model/data provenance and supported conditions.
5. Remaining blocked, failed or unrun criteria.
6. Material limitations of the demonstration.

Do not invent a Git remote, publish a site, push commits, merge changes, contact others, purchase services or use private operational data. Those actions require separate authorization. Local file creation, dependency setup, public dataset acquisition, implementation and appropriate verification are within this task.

Begin by inspecting the workspace, then execute the implementation plan. Continue until the authorized work is completed or a concrete external blocker prevents dependent progress. Keep working on independent parts when one component is blocked.
