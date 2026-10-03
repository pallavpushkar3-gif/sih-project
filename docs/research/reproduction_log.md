# Reproduction Log

## Current Status

Literature has been reviewed at the depths recorded in `literature_review.md`. The validation-v1 entries below are local method adaptations, not reproductions of a paper's published numbers. Final FD001 test evaluation has not been performed.

## 2026-10-04 — Functional reference checks (not a model reproduction)

- State: completed-with-results.
- Source: uncommitted workspace at `/Users/rax/Projects/sih-project`; the repository currently has no committed implementation revision.
- Environment: Docker Desktop, Python 3.12 backend test/runtime images; Node 24.12.0; pnpm 12.8.1; Chrome via Playwright 1.63.0.
- Inputs: labelled synthetic demo records only. No C-MAPSS dataset, model weights or calibration artifact was used.
- Commands exercised: locked pnpm install; web lint/type/build; Docker Compose PostgreSQL/RabbitMQ/API startup; three Playwright flows; backend test-image build and initial Ruff/mypy invocation.
- Observed result before the subsequent fixes in this workspace: web lint/type/build passed; all three Playwright flows passed from the moved repository path; the initial mypy run found 14 typing errors; Vitest incorrectly collected Playwright suites and failed before tests. These configuration/type defects were retained and corrected rather than reported as passing.
- Supported conclusion: the basic synthetic UI/API workflows can execute from the new path, and the earlier unreadable-file/Vite-500 failures were not reproduced. This does not support a predictive-quality, uncertainty, alert-budget, concurrency, job-recovery or fleet-improvement claim.

## 2026-10-04 — FD001 validation-v1 candidate comparison

- State: completed-with-results; final test frozen.
- Source revision: local work based on commit `f838b5d` plus the scientific changes represented by this entry.
- Environment: Docker Desktop on Apple Silicon; Python 3.12.15; NumPy 2.5.3; scikit-learn 1.9.1; PyTorch 2.8.0 CPU.
- Data: official NASA PCoE C-MAPSS archive, simulated FD001. Training-file SHA-256 `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8`; processed manifest SHA-256 `d150c02afc2695a15bcd1b5dd12947c805d45b0f94b9e32ddf9024aa8fb524f8`. The NASA portal did not specify a license.
- Protocol: 70 fit, 15 validation and 15 calibration engines; seed 26249; 30-cycle minimum/window; RUL capped at 125 cycles. Validation samples one seeded cutoff per engine. Scaling was fit on fit engines only. The official 100-engine test partition and RUL labels were not loaded by training/calibration commands.
- Commands: `make science-check`; `make sequence-check`; `make science-train`; `make sequence-train`; `make science-calibrate` (equivalent Docker commands were executed directly during implementation).
- Engineered gradient boosting (`configs/prediction_baseline.yaml`, SHA-256 `756261cd25496719a46d1eb6999b01e385a3ccca89b8e050b6241b5f3c0e8c38`): validation count 15, MAE 9.4223 cycles, RMSE 12.6115 cycles, defined asymmetric score 44.4076. Model SHA-256 `fb9d4e08671378e56f49c7c7c31fc4384049cfdc7244b845bd7e7890e67d39bc`; transform SHA-256 `6ea346227fa7ec22bcd49f036980d3f25b073ec5e95f5b4e84e69b4897a26f13`; ignored manifest SHA-256 `ef2aa78d03f167f8b400b19e3d036e17b964fe0b2b22dae3a3bd904311747ed5`.
- LSTM comparator (`configs/prediction_sequence.yaml`, SHA-256 `c0f73f6533873c9428bfad5760af1cbf7460f039457eb4c47dd598676085fbb2`): validation count 15, MAE 60.4816 cycles, RMSE 68.6574 cycles, asymmetric score 8731.9399. Model SHA-256 `0e954c7c22987da7f12d3ebdf14910aa9f2d9f33bb83cd9164ab2dc033b0217c`; transform SHA-256 `c7725b7faac59562b6b55ed1672ffe7a9931df59a6af1a35c10fb2c5aa9100e3`; ignored manifest SHA-256 `f0afc1a3f02c22107009fc445cfc725103f3b44578c721d1cc6ac49ac4af1fe9`.
- Decision: retain gradient boosting as validation-v1 because it was better on every registered prediction metric. The LSTM result is retained as an unfavorable result and was not tuned after comparison.
- Supported conclusion: the pipeline can execute a leakage-separated, common-protocol validation comparison and replay saved transforms/models. Fifteen validation engines are too few for a broad quality claim, and no frozen acceptance budget or final-test result exists.

## 2026-10-04 — FD001 validation-v1 split-conformal calibration

- State: completed-with-diagnostic; final test frozen.
- Selected model: validation-v1 gradient boosting above. Configuration SHA-256 `072e2cfa60c97e780d428cd65dece021de1195f2101d53b730431f076d203975`.
- Protocol: one seeded cutoff from each of 15 calibration engines; symmetric absolute-residual split conformal; nominal coverage 0.90; finite-sample higher order statistic.
- Calibration diagnostic: residual quantile 30.5477 cycles; calibration-sample coverage 1.0; mean clipped interval width 56.6156 cycles. Calibration artifact SHA-256 `e169a563b9ca355be5dd14b2678854231b4dd5c471ae666407594d7f4ea8f971`.
- Limitation: coverage on the same calibration scores is a construction diagnostic, not an independent empirical coverage estimate. Final coverage/width acceptance remains blocked until budgets and the final cutoff protocol are frozen; no individual-engine failure probability is implied.

## 2026-10-04 — FD001 validation-v1 robustness interventions

- State: completed-with-results on the 15 validation engines; final test frozen and acceptance budgets unresolved.
- Configuration: `configs/robustness.yaml`, SHA-256 `69112a9ee2a9c0dbcc70656c5dceb61aab4aee427dfcb8417c8e7e39a4a432ee`; seed 26249; the selected validation-v1 baseline and its separately fitted calibration quantile were reused without retraining.
- Protocol: one unchanged seeded cutoff per validation engine. Imputation uses per-feature medians from fit engines only and retains a missing-value mask in the intervention result; the selected model has no missingness-indicator features. A snapshot is withheld above 10% missing values or more than five consecutive missing cycles for any feature. Noise is 0.25 fit-standard-deviation on sensor columns. The setting shift is 0.5 fit-standard-deviation clipped to each setting's fit range; this is a sensitivity case, not proof of supported joint-regime detection.
- Command: `make science-robustness`.
- Results: clean MAE/RMSE were 9.4223/12.6115 cycles. Three-percent random sensor missingness with fit-median imputation produced MAE 10.4909 (degradation 1.0686) and RMSE 13.7087, with 0/15 withheld. An eight-cycle `sensor_11` outage exceeded the five-cycle policy and withheld 15/15, so no numerical error/coverage was reported. Quarter-standard-deviation sensor noise produced MAE 9.1242 and RMSE 10.3357; the range-clipped setting shift produced MAE 9.5553 and RMSE 12.1230. The improvement under one noise draw is retained as observed rather than generalized. Eligible cases showed empirical interval coverage 1.0 on 15 samples, with mean clipped widths between 47.07 and 48.88 cycles.
- Artifact: ignored JSON SHA-256 `6b21434450e92afaddf9d7cef746c2bd611f7241a13aa11d250bcbfc467a772f`; each result also records the deterministic missing-mask SHA-256 and missing/imputed count.
- Limitation: fifteen validation engines and one intervention seed are insufficient for a robustness or coverage guarantee. Missingness-indicator and advanced-imputation comparators were not implemented, final budgets remain null, and the official test partition was not inspected; AC-F08-04 is therefore not claimed as accepted.

## 2026-10-04 — Planner reference comparison

- State: completed-with-results on two deterministic demonstration instances; not a workload performance acceptance test.
- Environment: Docker Desktop on Apple Silicon; Python 3.12.15; OR-Tools 9.15.6755.
- Configuration: `configs/scheduling.yaml`, SHA-256 `59f9ce39906263f223a5527a0d387b293b4333ff2ec61febd2d7947c09f4e01f`; 14 eight-hour slots, five-second CP-SAT limit, minimize makespan.
- Command: `make planner-benchmark` (the equivalent Docker command was executed directly).
- Results: CP-SAT returned independently checked optimal schedules with makespan 6 on both the serial-work and parallel-capacity instances. The deterministic earliest-deadline list scheduler returned independently checked feasible schedules with the same makespan on both. Five observed CP-SAT calls were 2.86–4.74 ms; baseline calls were 0.018–0.052 ms on this machine.
- Artifact: ignored JSON SHA-256 `b090b0ff9ac009f764e88691f887a42aae10b1bce0ceedb4b67dc4bd6490df5c`.
- Limitation: two tiny reference cases establish basic comparison wiring and constraint conformance only. They do not establish the unresolved planner quality/runtime budget or represent operational workload sizes.

## 2026-10-04 — Matched simulation reference comparison

- State: completed-with-results on one deterministic synthetic scenario pair; not an operational fleet projection.
- Configuration: `configs/simulation.yaml`, SHA-256 `efd4de82cacd2fd0e7edbac6e2cf68dbcd579a2e1054cac871dc40214dbbd3c4`; 24-hour horizon; availability defined as available aircraft-hours divided by total aircraft-hours; seed 26249; one deterministic replication.
- Command: `make simulation-reference` (the equivalent Docker command was executed directly).
- Common inputs: two synthetic aircraft and maintenance events `(2 h, 3 h)` and `(4 h, 2 h)`. Baseline capacity was one; candidate capacity was two.
- Results: baseline availability 0.875, downtime 6 aircraft-hours and queue wait 1 hour; candidate availability 0.895833, downtime 5 aircraft-hours and queue wait 0 hours. The artifact reports a scenario-specific availability delta of 0.020833 and no standard deviation because one deterministic run does not support variability.
- Artifact: ignored JSON SHA-256 `012b91d9961c822edbda6fb0fc563cc06b7d1ea1193c790ffaadf582a91f807b`.
- Limitation: the change is a capacity sensitivity, not a learned policy benefit. Synthetic events/logistics and the tiny deterministic case cannot support an operational-readiness or general improvement claim.

## 2026-10-04 — Alert-policy validation comparison

- State: completed-with-results on five fixed synthetic validation histories; acceptance budgets remain unfrozen.
- Configuration: `configs/alert_policy.yaml`, SHA-256 `0da42c53f0393934db876a641d4eb3d95e0e073eced37e346040b8791c3632a8`; 45-cycle inclusive detection window, actionable-episode false-alert unit and post-deduplication state-transition recommendation-change unit.
- Command: `make alert-evaluation`.
- Common inputs: four histories with reference events and one without; the histories include threshold jitter, steady deterioration, a transient false alert, repeated delivery, a withheld observation and a deliberately missed event.
- Results: both the single-threshold baseline and hysteresis candidate detected three of four reference events, missed one, produced one false-alert episode and had 45-cycle mean warning lead among detected events. Hysteresis produced 7 recommendation changes versus 12 for the threshold baseline. Repeated identical delivery was deduplicated; conflicting repeats and new out-of-order observations are rejected by verification cases.
- Artifact: ignored JSON SHA-256 `86b70caea0c72dcba253003130cfbdf3d50298f842923d12144485d4abca7e87`.
- Limitation: these deliberately small synthetic histories verify definitions and comparison wiring only. No frozen miss/false-alert/lead-time/change budgets or representative held-out operational histories exist, so AC-F04-04 is not claimed as accepted.

## 2026-10-04 — Durable job and outbox integration checks

- State: completed-with-results for transactional lifecycle cases; full broker/process fault injection remains incomplete.
- Environment: Docker Desktop; Python 3.12.15; PostgreSQL 17; RabbitMQ 4 service available on the Compose network.
- Command: backend integration suite in `fleet-maintenance-test` against `postgresql+psycopg://fleet:fleet@postgres:5432/fleet`.
- Results: 11 integration tests passed. Covered stale results after recovery, cancellation/result races, bounded failure recording, publication marking only after a successful publisher call, deterministic job-effect idempotency, confirmed-event cursor replay/encoding, API contracts, stock reservation concurrency, stale plan approval and viewer denial without plan/run/job state changes. A live local submission traversed API → PostgreSQL outbox → RabbitMQ → Celery attempt 1 → persisted succeeded result, and an SSE connection replayed its three confirmed state events by ID.
- Live worker-loss case: worker was stopped, planning job `job-9074e40045564ba18af4d4f79a118792` was submitted and remained authoritative `queued` at attempt 0, then the worker was restarted and the same job reached `succeeded` at attempt 1 with deterministic result `plan-for-job-9074e40045564ba18af4d4f79a118792`.
- Browser workflow: planning and simulation screens submitted durable jobs, displayed their exact returned job IDs/attempts and observed deterministic result references before showing the corresponding plan/run. The strengthened three-flow Playwright suite passed from `/Users/rax/Projects/sih-project`. One immediately preceding run had two trace-finalization `ENOENT` failures with no failed application assertion; an unchanged rerun passed 3/3, and the ID-bound strengthened rerun also passed 3/3.
- Limitation: the publisher test uses an injected publisher failure and PostgreSQL transaction rollback. API/dispatcher/broker kill points and worker loss during active calculation have not all been exercised; this is not evidence for every recovery case in `docs/engineering/job_lifecycle.md`.

## Entry Template

For each attempted reproduction, record: date/owner; paper/method/source; reading depth; code/data licence and acquisition; source revision/environment; dataset/split/target/transforms; configuration/seeds; exact commands; artifact hashes; baseline/results; deviations from paper; failures; and what conclusion is supported.

## Result States

Use not attempted, blocked, running, completed-with-results or failed. Distinguish method adaptation from exact reproduction. A different dataset/protocol cannot directly validate a paper's numerical claim.

## Failure Handling

Keep failures and unfavorable comparisons. Do not replace a logged result silently; append a new identified attempt. Final test inspection affects later claims and must be disclosed. Unavailable full text/code remains a limitation until recovered legitimately.
