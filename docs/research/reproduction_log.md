# Reproduction Log

## Current Status

Literature has been reviewed at the depths recorded in `literature_review.md`. No paper code/result has been reproduced, no model trained and no performance check is claimed here.

## 2026-10-04 — Functional reference checks (not a model reproduction)

- State: completed-with-results.
- Source: uncommitted workspace at `/Users/rax/Projects/sih-project`; the repository currently has no committed implementation revision.
- Environment: Docker Desktop, Python 3.12 backend test/runtime images; Node 24.12.0; pnpm 12.8.1; Chrome via Playwright 1.63.0.
- Inputs: labelled synthetic demo records only. No C-MAPSS dataset, model weights or calibration artifact was used.
- Commands exercised: locked pnpm install; web lint/type/build; Docker Compose PostgreSQL/RabbitMQ/API startup; three Playwright flows; backend test-image build and initial Ruff/mypy invocation.
- Observed result before the subsequent fixes in this workspace: web lint/type/build passed; all three Playwright flows passed from the moved repository path; the initial mypy run found 14 typing errors; Vitest incorrectly collected Playwright suites and failed before tests. These configuration/type defects were retained and corrected rather than reported as passing.
- Supported conclusion: the basic synthetic UI/API workflows can execute from the new path, and the earlier unreadable-file/Vite-500 failures were not reproduced. This does not support a predictive-quality, uncertainty, alert-budget, concurrency, job-recovery or fleet-improvement claim.

## Entry Template

For each attempted reproduction, record: date/owner; paper/method/source; reading depth; code/data licence and acquisition; source revision/environment; dataset/split/target/transforms; configuration/seeds; exact commands; artifact hashes; baseline/results; deviations from paper; failures; and what conclusion is supported.

## Result States

Use not attempted, blocked, running, completed-with-results or failed. Distinguish method adaptation from exact reproduction. A different dataset/protocol cannot directly validate a paper's numerical claim.

## Failure Handling

Keep failures and unfavorable comparisons. Do not replace a logged result silently; append a new identified attempt. Final test inspection affects later claims and must be disclosed. Unavailable full text/code remains a limitation until recovered legitimately.
