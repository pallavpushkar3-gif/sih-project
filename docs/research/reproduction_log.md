# Reproduction Log

## Current Status

Literature has been reviewed at the depths recorded in `literature_review.md`. The validation-v1 entries below are local method adaptations, not reproductions of a paper's published numbers. Final FD001 test evaluation was subsequently performed after user approval; see the appended final-evaluation entry. Earlier entries retain their historical status.

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
- Results: 13 integration tests passed. Covered stale results after recovery, cancellation/result races, bounded failure recording, publication marking only after a successful publisher call, deterministic job-effect idempotency, confirmed-event cursor replay/encoding, API contracts, stock reservation concurrency, stale plan approval, idempotent alert review and viewer denial without plan/run/job/acknowledgement state changes. A live local submission traversed API → PostgreSQL outbox → RabbitMQ → Celery attempt 1 → persisted succeeded result, and an SSE connection replayed its three confirmed state events by ID.
- Live worker-loss case: worker was stopped, planning job `job-9074e40045564ba18af4d4f79a118792` was submitted and remained authoritative `queued` at attempt 0, then the worker was restarted and the same job reached `succeeded` at attempt 1 with deterministic result `plan-for-job-9074e40045564ba18af4d4f79a118792`.
- Browser workflow: planning and simulation screens submitted durable jobs, displayed their exact returned job IDs/attempts and observed deterministic result references before showing the corresponding plan/run. Alert review recorded `demo-engineer` while retaining the `data_unavailable` alert state. The strengthened four-flow Playwright suite passed from `/Users/rax/Projects/sih-project`. One earlier three-flow run had two trace-finalization `ENOENT` failures with no failed application assertion; an unchanged rerun passed 3/3, the ID-bound rerun passed 3/3, and the acknowledgement-expanded suite passed 4/4.
- Migration rehearsal: the first acknowledgement migration startup encountered an empty pre-existing unversioned `alert_acknowledgements` relation while Alembic still reported `9c9c7c1262e5`. After confirming zero rows, only that empty local table was dropped; the migration then applied normally and Alembic reported `2e4a7d81b6c3`. No user record was removed.
- Limitation: the publisher test uses an injected publisher failure and PostgreSQL transaction rollback. API/dispatcher/broker kill points and worker loss during active calculation have not all been exercised; this is not evidence for every recovery case in `docs/engineering/job_lifecycle.md`.

## Entry Template

For each attempted reproduction, record: date/owner; paper/method/source; reading depth; code/data licence and acquisition; source revision/environment; dataset/split/target/transforms; configuration/seeds; exact commands; artifact hashes; baseline/results; deviations from paper; failures; and what conclusion is supported.

## Result States

Use not attempted, blocked, running, completed-with-results or failed. Distinguish method adaptation from exact reproduction. A different dataset/protocol cannot directly validate a paper's numerical claim.

## Failure Handling

Keep failures and unfavorable comparisons. Do not replace a logged result silently; append a new identified attempt. Final test inspection affects later claims and must be disclosed. Unavailable full text/code remains a limitation until recovered legitimately.

## 2026-10-04 — Frozen FD001 final evaluation and backend integration

- State: completed-with-results for the declared prediction/interval gates; original full release remains incomplete as detailed in ../operations/production_readiness.md.
- Authorization: user selected “Freeze demonstrator targets and evaluate” after the dataset/benchmark proposal. Policy fd001-demonstrator-gates-v1 SHA-256 `e1b5e9f3f060c87c40571755f82efc5b75586afa53c85eb25ea28f5efdb7baea` was frozen before inspecting official final labels. No model or threshold tuning followed test inspection.
- Source: uncommitted workspace at `/Users/nikithakodithyala/Desktop/sih-project`; environment Python 3.13.7, locked scientific dependencies, PyTorch 2.8.0, Node 24, pinned pnpm, Docker PostgreSQL 17/RabbitMQ 4. Earlier entries retain their historical environment and status.
- Data: reacquired public FD001 files matched data/sources.yaml hashes. Training contained 20,631 rows/100 engines, lifetime minimum/median/maximum 128/199/362 cycles, seven constant columns and no nonfinite values. Reused the declared 70/15/15 engine split, seed 26249, 30-cycle window and cap 125; selected baseline/configuration were unchanged.
- Command: `PYTHONPATH=backend/src .venv313/bin/python scripts/evaluate_model.py` (shared science evaluator); repeat output compared identical. Initial entry-point attempt failed with KeyError for an incorrectly named metric key; correcting the reporting key did not change models or gates. Original result and canonical shared result are retained separately.
- Official test: 100 eligible engines, capped MAE 8.7219757093 cycles, RMSE 11.7098731530 cycles, asymmetric score 207.2660118734. Uncapped MAE/RMSE 9.7693428242/13.1815159502 cycles. Nominal 90% intervals covered 98/100; one-sided 95% exact lower bound 0.9383807996; mean width 58.2307335739 cycles. All frozen prediction/interval gates passed; small life groups are disclosed and alert acceptance was not evaluated.
- Canonical output SHA-256 `c5db04c48ced4c84a23e451071e83b8f6e9577266de21128d2ca0bf469a7a7f9`; model manifest `c75bb58323e49c64a4cdb05cf73271a274789e9a90b6e8581d8980c94d305421`; model `10eae9d0058cc765941ae8d4a921dc882ba3dd50e5651855a653165e8122506a`; calibration `5ed32d03fced03b2b737a2c6d7bb578cb94c2abe754ced53ea8ed5d8eebb5e1e`. Rebuilt model bytes differ from earlier Python 3.12 serialization; this entry identifies the actually evaluated artifact instead of claiming byte-identical cross-environment reproduction.
- Live rebuilt worker: planning job job-d72cb8ecfc0a43aa8c5595c192ca71bc and simulation job job-c65dd5c54517493bb43bf5a8de4f0412 succeeded. Assessment job job-84ea887f47dc43758a628a337f9d4f40 served FD001 test engine 1 at cutoff 31, estimate 112.817585 cycles, interval 82.269859–143.365311 with input identity and explanation available. After container recreation, an initial probe lacked its /tmp history input; copying the unchanged public input resolved that probe setup failure.
- Live approval/work job job-f39594d389c54ac5976330b49f737646: repeated approval created two work rows exactly once; completing the started filter task consumed one unit; cancelling the unstarted inspection released its kit; final plan status closed with zero active reserved units.
- Worker-loss probe: job-33d14caf831847389b79cdb58b7b0133 recovered after a running worker kill/restart on attempt two in 31.78 seconds under a 30-second test lease. This probe used labelled synthetic planner inputs in an isolated stack.
- Restore: separate fleet_restore_work_check database matched every compared source row at migration 64c201993bc1; nonempty work/reservation/audit rows and matching registered artifact hashes were verified. Dump hash and exact counts appear in production_readiness.md.
- Check setup failures retained: host pytest first could not import the editable package, then restricted local port access blocked PostgreSQL/browser startup. Explicit PYTHONPATH and authorized local-service access resolved these environment issues. Ruff flagged one import-order issue after synchronous route transaction refactoring; it was corrected. No failing application assertion was treated as passed.
- Final verification after route transaction fixes: `ruff check backend/src backend/tests scripts` passed; `mypy backend/src/fleet_maintenance` passed for 115 source files; `PYTHONPATH=backend/src FLEET_DATABASE_URL=<isolated PostgreSQL URL> .venv313/bin/python -m pytest backend/tests -q` passed 62 tests with one Starlette/httpx deprecation warning. `make web-check` passed ESLint, TypeScript, production build and six Vitest tests. `corepack pnpm --filter @fleet-maintenance/web exec playwright test workspace-ui.spec.ts` passed all nine fixture/browser checks. The build retained its chart-chunk size warning; no throughput or full live-browser release acceptance is inferred.

## 2026-10-04 — Explanation diagnostics, workload and attempt retention

- Source: same uncommitted workspace; no release commit or deployment. Method/configuration/module/model/data hashes are retained with diagnostic artifacts. Original FD001 final evaluation and its frozen targets were not changed; new explanation diagnostics loaded training histories and the original validation-engine IDs only.
- New shared explanation method validates finite/aligned intervention outputs and preserves valid numerical predictions when expected sensitivity calculation fails. API metadata now distinguishes unavailable explanation content. Analytic linear-reference, invalid-output, isolated explanation failure and API-state regression cases were added.
- Protocol configs/explanation_evaluation.yaml: 15 validation engines, one seeded cutoff each, seed 26249, 20 engineered-feature perturbations per engine at 0.01 fit-standard-deviation. Constant fit features and dataset cycle are held fixed. This perturbation is a diagnostic choice, not scientifically calibrated operational noise.
- Results: exact-input replay maximum difference 0 cycles; maximum independent intervention discrepancy 0 cycles; 300 probes mean top-ten Jaccard 0.9442424, fifth percentile 0.8181818; mean vector cosine 0.9956773; mean sensitivity change 0.0165502 cycles; mean prediction change 0.4075805 cycles. Cosine values are numerically clipped to their mathematical bounds. Canonical diagnostic artifact hash a3ec8e75a6607c3eef6a738ecbb1c5ae96f31e06c7507b717e3610b743d2d31d; a repeated evaluator output compared byte-identically. No validated stability acceptance threshold exists, so the result remains diagnostic.
- Workload entry point scripts/benchmark_workload.py delegates to the shared verification module. Five readers completed 200 endpoint reads alongside planning/simulation submissions. First-run p95/p99 37.50/169.44 ms, second-run 47.08/220.92 ms; both had zero non-200 reads. Updated run observed 21 active-job samples; both submitted jobs succeeded. Client platform, configuration/module hashes and per-response timing are retained; Docker allocation was eight CPUs/8,319,770,624 bytes RAM/aarch64. Small synthetic records, demo headers and a short run cannot establish production-session, large-fleet, sustained-load or browser-interaction acceptance. Artifact hashes appear in ../operations/production_readiness.md. Intended workload was requested while independent checks continued; no unstated user response or frozen acceptance budget is assumed.
- Actual generated/reviewed migration eab4b05e021f creates durable attempt history. PostgreSQL and SQLite upgrades passed; PostgreSQL Alembic check reported no schema drift. Attempt state/times/worker/lease/outcome are committed with authoritative job transitions. Historical pre-migration attempt data are not invented.
- Live synthetic 1,000-task fault probe job-676fc1b0a91a4243af425770b4db00aa: running isolated worker killed/restarted; job succeeded on attempt two in 30.93 seconds. API attempt history retained expired/lease_expired then succeeded rows with timestamps. New database fleet_restore_attempt_check matched all compared rows at the new migration head, including four attempt records. Coordinated dump SHA-256 c2675674c08eb77252c8a8f37a707f189f437e9f1360a352d42c6445d798741c.
- Commands: PYTHONPATH=backend/src .venv313/bin/python scripts/evaluate_explanations.py; PYTHONPATH=backend/src .venv313/bin/python scripts/benchmark_workload.py; real Alembic generation/upgrade/check; isolated Docker worker kill/start and quiesced PostgreSQL dump/restore. Final Ruff check passed; full mypy passed 118 source files; all 68 backend tests passed against the local PostgreSQL integration environment including Torch science tests; regenerated OpenAPI/TypeScript schema and make web-check passed six Vitest tests plus lint/types/build. One Starlette/httpx deprecation warning and the pre-existing chart bundle warning remain. Earlier authoring checks caught line-length/import/type errors and they were corrected before final verification.
- Limitations: no new operational data, complete independent held-out alert trajectories, validated stability cutoff, production latency budget or deployment is supplied by this work. See the readiness record for remaining original acceptance items.

## 2026-10-04 — delivery workflow and user-directed release boundaries

Implemented time-dependent delivery constraints and independent cumulative-inventory validation, audited/idempotent delivery receipt/cancellation, browser delivery controls, grounding-versus-early-maintenance reference metrics, confirmed-prefix SSE replay/resync and session revalidation. Generated migration `c2ceb7b6aa9b` was reviewed and applied to the isolated PostgreSQL stack.

The backend suite passed 76 tests and the fixture browser suite passed 10 cases. The first delivery browser locator was ambiguous because a nested label included option text; corrected the accessible combobox locator and reran successfully. A solver test initially asserted one of multiple optimal start assignments; changed it to assert timing constraints and the optimal objective, then reran successfully. Web checks passed with six Vitest tests and chart splitting removed the prior oversized-chart warning.

Real-service public/synthetic walkthrough completed; retained `artifacts/evaluations/full-workflow-v1.json`. Holdout audit found no untouched FD001 complete training engines: all 100 were previously used. Exact identities/input hashes are retained in `artifacts/evaluations/fd001-alert-holdout-audit-v1.json` and explained in `fd001_alert_holdout_audit.md`. No complete-trajectory held-out alert result or operational cost acceptance is claimed. EC2/Nginx preparation parameterizes `DEPLOYMENT_DOMAIN`; public host/certificate acceptance remains blocked. No paid resources or external publication were authorized or performed.

EC2 configuration and both Nginx templates validated locally. A loopback test using a one-day self-signed localhost certificate returned HTTPS 200 and HTTP 308; this certificate is exclusively a local fixture. Full PostgreSQL restore at `c2ceb7b6aa9b` matched all compared records (backup SHA-256 `f4a5f745a356e7180628c347399d1ea2e0c0c3f41b918f206f6833a9e0bde0af`). A redundant host verification run stalled during installed dependency reads/imports: pytest collection was interrupted; mypy produced an internal error and isolated-cache retry stalled. Preserve the earlier successful checks; do not count interrupted repetitions as passed. No backend source changed during this deployment/audit follow-up.

## 2026-10-04 — aircraft inspection redesign and synthetic supply assumption

Added a licensed local Cesium aircraft asset with a recorded hash/notice and a real rendered fallback poster; React Three Fiber 9/Drei/Three.js, local Inter, semantic token shell, mapped selection and evidence integration. Added the authoritative read-only inspection task endpoint and exported actual OpenAPI/generated TypeScript using the implemented generator. Added `part_available_hours` to the shared deterministic SimPy input, immutable scenario revisions and saved metrics; part wait and bay wait are separately measured. New integration tests verify unchanged parent/saved baseline, horizon/version rejection and actual altered outcome; verification tests check wait accounting.

Docker full-dependency/PostgreSQL backend run: 81 passed; Ruff passed; mypy 121 source files passed after type-only NumPy/Torch stub fixes. Fresh frozen-lock browser dependencies in `/tmp/fleet-ui-verification` avoided host read timeouts; source remains in the actual repository. Web six Vitest tests, lint/types/build passed; browser/check/capture details and retained failures are in `docs/design/ui_verification.md`. No new FD001 model fitting, calibration, test tuning or engine holdout allocation occurred. Prior final-test and all-used-engine audit evidence remains unchanged. Device/user-study/public deployment/independent operational validation are not inferred from this implementation.

## Release-v2 reproduction — 2026-10-05

The selected customer-trial-v1 endpoint benchmark, explanation diagnostics and validation-only intervention diagnostics were rerun under the locked Python 3.13 container. A separately retrained lifecycle experiment was run twice under the same frozen configuration; reports and fitted-artifact hashes matched. Early cached-image/lint/argument failures were retained and corrected, not counted as passes. See `docs/team/release_acceptance.md` and ignored `artifacts/release-v2/` for final commands/logs/reports. Preserve this directory, learned-model directories and source evidence manifest outside Git; ignored artifacts are required evidence.
