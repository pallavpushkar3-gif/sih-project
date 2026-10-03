# Acceptance Criteria

**Project:** Aircraft Predictive Maintenance & Fleet Availability
**Problem statement:** PS 26249
**Repository location:** `docs/product/acceptance_criteria.md`
**Status:** Initial acceptance specification; no checks claimed as passed
**Related documents:** `intent.md`, `scope.md`, `docs/product/feature_specifications.md`

## 1. How Acceptance Works

This document defines evidence required to accept the scoped demonstrator. Planned capability, implemented capability and validated capability are distinct.

Each criterion receives one status: **not run**, **passed**, **failed**, or **blocked**. A blocked or unrun required criterion does not count as passed. Associate results with a source revision and the exact input/configuration versions used.

Passing functional checks does not establish predictive accuracy, simulation validity or operational suitability. Scientific claims require their own evaluations. The release remains a demonstrator using supported engine data and labelled logistics assumptions.

### Evidence record

For each criterion, retain:

- Criterion identifier and status.
- Source revision, environment and relevant versions.
- Input/fixture/dataset/configuration identifiers and hashes where applicable.
- Test or evaluation command and output artifact.
- Actual outcome and comparison with the required condition.
- Limitations, failures or unresolved dependencies.

Machine-verifiable checks should retain machine-readable results. Screenshots or walkthrough recordings demonstrate interface behaviour but do not substitute for constraint, concurrency or leakage checks.

## 2. Evaluation Decisions Required Before Testing

The following values are not invented here. Define them in the referenced protocol, version that decision, and freeze it before the corresponding final evaluation.

| Decision | Required specification | Owning document |
|---|---|---|
| Dataset support | Subsets/regimes, engine partitions, target definition/capping, cutoff/window rules and preprocessing. | `docs/research/dataset_protocol.md` |
| Prediction acceptance | Baselines, error metrics, late-prediction penalty, aggregation, repetitions and an application-relevant acceptable error bound. | `docs/research/evaluation_protocol.md` |
| Uncertainty acceptance | Nominal interval level, calibration procedure, coverage tolerance, acceptable width, groups and sufficient sample criteria. | Evaluation protocol |
| Alert acceptance | Policy thresholds/margins, event definition, warning horizon, false/missed-event budgets and schedule-change comparison. | Evaluation protocol and alert configuration |
| Planner acceptance | Instance families, units/discretization, objectives, baseline, time limit and required quality/runtime. | Evaluation protocol and scheduling configuration |
| Simulation acceptance | State definitions, usage/repair/logistics assumptions, replications, comparison metrics and sampling procedure. | `docs/research/simulation_assumptions.md` and evaluation protocol |
| Responsiveness | Target hardware/browser, dataset/visible-chart size, user concurrency, concurrent jobs and latency/resource budgets. | Acceptance benchmark configuration linked from evaluation protocol |

Decisions may be informed by training/validation experiments or stakeholder needs. Do not choose thresholds after inspecting the final test outcomes merely to make a result pass. A changed protocol requires a separately identified evaluation and an honest account of previously inspected data.

## 3. F01 — Unified Records

| ID | Required condition | Evidence |
|---|---|---|
| AC-F01-01 | Supported valid imports produce correct component/observation/task relationships and source/unit metadata. | Import fixture checks and database/API assertions. |
| AC-F01-02 | Reimporting an identical source/version does not duplicate observations or tasks; conflicting existing values follow the documented correction policy. | Repeated/conflicting import tests and provenance history. |
| AC-F01-03 | Malformed identities, invalid cycles/times and unsupported units are rejected or explicitly reported under the configured partial-import policy. | Invalid-input cases and accepted/rejected counts. |
| AC-F01-04 | A displayed assessment or proposal links to its actual input snapshot; later corrections do not silently rewrite historical evidence. | Versioned correction and retrieval checks. |

## 4. F02 — Life Prediction and Uncertainty

| ID | Required condition | Evidence |
|---|---|---|
| AC-F02-01 | Engine identities do not leak across required disjoint partitions; fit transformations use only permitted training data. | Split manifests, transformation provenance and leakage checks. |
| AC-F02-02 | Training and serving apply the same versioned transformation, feature ordering, units and target definition. | Parity check on a fixed input with an explicit numerical tolerance. |
| AC-F02-03 | Historical replay cannot consume observations beyond the selected cutoff or future target labels. | Cutoff tests, including modifications to future observations that leave current inputs unchanged. |
| AC-F02-04 | Classical and sequence candidates are evaluated under the same protocol; the selected model meets the predeclared error requirements. | Held-out metrics and subgroup/repeated-run results where specified. |
| AC-F02-05 | Intervals meet the predeclared coverage/width requirements on eligible evaluation groups; insufficiently supported groups are disclosed. | Coverage, width and sample-count reports with calibration provenance. |
| AC-F02-06 | Results contain model/input/calibration versions and quality state; invalid or unsupported results are qualified/withheld by the defined policy. | API/output validation and model-support cases. |

Do not require a neural model to beat a classical model. If the baseline is stronger, it may be selected. If no candidate meets the declared quality requirements, this feature is blocked for its claimed support boundary; revise the scope or method explicitly rather than fabricate success.

## 5. F03 — Prediction Evidence

| ID | Required condition | Evidence |
|---|---|---|
| AC-F03-01 | Evidence charts, influences, cutoff and provenance belong to the same assessment/input version. | Version-alignment assertions and a reviewed evidence card. |
| AC-F03-02 | Units, missing/imputed values and known limitations are visible; unknown physical sensor mappings remain labelled as such. | Interface walkthrough and metadata cases. |
| AC-F03-03 | The chosen explanation method is evaluated under the declared stability/fidelity checks and its limitations are recorded. | Explanation evaluation, reference/baseline definition and examples. |
| AC-F03-04 | Unsupported/failed explanation generation produces an explicit unavailable state without invented fault causes or a misleading narrative. | Failure/unsupported cases. |

## 6. F04 — Stable Alerts

| ID | Required condition | Evidence |
|---|---|---|
| AC-F04-01 | Alert state changes match the versioned policy, including persistence/hysteresis and chronological input rules. | Fixed-history reference cases. |
| AC-F04-02 | Repeated assessment/event delivery does not duplicate transitions; acknowledgement does not resolve deterioration. | Deduplication and review-state tests. |
| AC-F04-03 | Invalid/withheld assessments do not silently clear an active health concern; overdue mandatory work stays visible. | Degraded-data and mandatory-task cases. |
| AC-F04-04 | The selected policy meets the frozen alert budgets and is compared with a threshold baseline. | Warning time, missed/false-event and recommendation-change reports. |

Alert stability alone is insufficient: reducing changes while increasing missed events beyond the accepted budget fails the policy requirement.

## 7. F05 — Maintenance Planner

| ID | Required condition | Evidence |
|---|---|---|
| AC-F05-01 | Every proposal presented as usable passes independent checks for mandatory deadlines, capacity/qualifications, precedence, parts timing and fixed commitments. | Validator outputs for representative and boundary instances. |
| AC-F05-02 | Invalid inputs are distinguished from mathematical infeasibility, execution failure and time-limit/unknown outcomes. | Controlled cases for each exposed outcome. |
| AC-F05-03 | Feasible and optimal labels match solver status; objective/bounds and settings are retained when available. | Solver-result contract checks. |
| AC-F05-04 | Revising a task/resource/assumption creates a new proposal version; editing a timeline cannot bypass validation. | Revision and edit/revalidation tests. |
| AC-F05-05 | The planner meets its declared runtime/quality requirements and is compared against a defined baseline on common instances. | Benchmark manifest, objectives, statuses and runtimes. |

Hard-constraint violations in any accepted proposal fail acceptance. A small-instance feasibility check does not prove all possible schedules are correct; retain the tested scope and use validation on every returned proposal.

## 8. F06 — Grouping and Inventory

| ID | Required condition | Evidence |
|---|---|---|
| AC-F06-01 | Grouped tasks satisfy documented compatibility, windows, duration and resource constraints; grouping benefits/tradeoffs are reported honestly. | Grouping reference cases and comparison with separate work. |
| AC-F06-02 | Unapproved proposals do not consume/reserve stock; approved plans reserve exactly their required quantities. | Stock/reservation assertions before and after approval. |
| AC-F06-03 | Concurrent requests for insufficient shared stock cannot double-reserve it; failed approval does not leave a partial commitment. | Concurrent transaction and rollback tests. |
| AC-F06-04 | Cancellation/revision releases only eligible reservations; previously consumed parts are not automatically recreated. | Reservation lifecycle cases. |
| AC-F06-05 | Shortage quantities, arrivals and inventory corrections are traceable to actual fixture/record versions and authorized changes. | Bottleneck and audit checks. |

## 9. F07 — Availability Simulation

| ID | Required condition | Evidence |
|---|---|---|
| AC-F07-01 | Small deterministic reference cases produce expected grounding/waiting/completion states and metrics within defined tolerances. | Analytically understandable cases and event traces. |
| AC-F07-02 | Resource occupancy respects capacity and aircraft/component state transitions remain consistent. | Simulation invariants, including simultaneous-event cases. |
| AC-F07-03 | Each run records scenario/policy/model versions, horizon, state/metric definitions, usage conversions and sampling settings. | Run manifest inspection. |
| AC-F07-04 | Alternative policies use comparable inputs and the declared sampling procedure; mismatch is blocked or prominently qualified. | Comparison contracts and paired-scenario checks. |
| AC-F07-05 | Stochastic results report the declared replication summaries/variability; deterministic results have no fabricated uncertainty. | Per-run and aggregated outputs. |
| AC-F07-06 | Outputs are labelled simulated projections; repair/reset effectiveness and synthetic logistics assumptions are inspectable. | Interface review and assumption links. |

No fixed availability improvement is assumed. A worse-performing plan must remain visible as such. If claiming improvement, report the baseline, scenarios, repetitions, variability and scope supporting the claim; do not generalize it to an actual fleet.

## 10. F08 — Data Quality and Robustness

| ID | Required condition | Evidence |
|---|---|---|
| AC-F08-01 | Declared checks detect their defined missing/invalid/stale/out-of-order conditions and retain interpretable findings. | Quality-rule fixtures, including valid edge cases. |
| AC-F08-02 | Imputed values remain distinguishable from observations; qualified/withheld states match the policy. | Transformation and assessment-output checks. |
| AC-F08-03 | A withheld assessment cannot silently provide numerical planning input or healthy status; mandatory tasks remain actionable. | Cross-feature degraded-data workflow. |
| AC-F08-04 | Missingness/noise/regime robustness experiments meet the declared support requirements or explicitly narrow the support boundary. | Error/coverage/withholding results for each intervention. |

Do not claim universal out-of-distribution detection. The supported checks, their evaluation and limitations define the feature's acceptance boundary.

## 11. Supporting Workflow and Reliability

| ID | Required condition | Evidence |
|---|---|---|
| AC-S01 | Permissions are enforced server-side; unauthorized viewing/editing/approval is rejected without unintended state changes. | Permission matrix cases. |
| AC-S02 | Approval rechecks current plan/task/stock/resource versions. Stale proposals produce a conflict, not silent approval of changed content. | Competing edit/approval cases. |
| AC-S03 | Repeated approval requests do not duplicate work records or reservations; material decisions retain user/time/version evidence. | Idempotency and audit assertions. |
| AC-S04 | Partial work completion, part consumption and remaining tasks are represented correctly; historical assessments remain unchanged. | Completion lifecycle cases. |
| AC-S05 | Killing/restarting an API or worker produces a recoverable job or explicit failure, with no silently lost recorded job. | Fault-injection recovery record. |
| AC-S06 | Repeated messages/retries cannot duplicate accepted effects; superseded attempts cannot replace the authoritative result. | Retry/deduplication/stale-result cases. |
| AC-S07 | Interrupted dispatch is recoverable under the outbox design; success is announced only after durable result persistence. | Dispatch interruption and completion-order tests. |
| AC-S08 | Cancellation-requested and cancelled states are distinct; late results follow the declared cancellation policy. | Cancellation race cases. |
| AC-S09 | Reconnecting clients can retrieve authoritative job/results independently of live events; replay does not duplicate UI state. | Connection interruption and state-retrieval tests. |

## 12. Interface, Reproducibility and Responsiveness

| ID | Required condition | Evidence |
|---|---|---|
| AC-X01 | Principal screens handle loading, empty, error/unavailable, stale and denied states without plausible-looking substitute outputs. | State walkthrough and applicable E2E checks. |
| AC-X02 | Core actions work with keyboard navigation; focus is usable; warnings/statuses have text labels and are not colour-only. | Keyboard/focus review and automated checks where useful. |
| AC-X03 | Chart units, cutoffs, selected components and provenance stay consistent across linked views. | Linked-interaction checks. |
| AC-X04 | Repeated evaluation with the retained environment/configuration reproduces required outcomes within declared tolerances. | Reproduction commands and comparison outputs. |
| AC-X05 | API/worker isolation and UI responsiveness meet the declared budgets under the declared workload/hardware. | Latency/resource/error reports while calculations run. |
| AC-X06 | Public API/client contracts match the implemented schema; migrations and a representative restoration preserve required relationships/results. | Contract generation checks, migration/restore record. |

Reproducibility is evaluated within the declared environment. Do not promise identical floating-point outputs across every machine or library release. A restored database must retain resolvable artifact references; database backup alone may not preserve model/data files.

## 13. End-to-End Release Gate

The release walkthrough must complete these connected cases using the tested source revision:

1. Import supported engine history and labelled fleet/logistics inputs.
2. Replay a held-out engine without future-input leakage.
3. Inspect assessment, interval, evidence and alert history.
4. Generate a checked proposal exposing a known parts/resource constraint.
5. Revise one logistical assumption and retain separate proposal versions.
6. Compare alternatives through reproducible, labelled simulation results.
7. Approve a plan with current-state checks and consistent reservations.
8. Record work/completion without rewriting historical evidence.
9. Inject degraded sensor input and observe the specified quality response.
10. Interrupt/recover a calculation and retrieve its authoritative state/result.

Required functional criteria must pass, evaluation decisions must be frozen, and scientific criteria must meet those decisions. Any unrun/blocked requirement must remain explicitly incomplete. A narrowed demonstration requires a deliberate scope/specification change; it must not be labelled the original full release.

## 14. Claims Allowed by Acceptance

Acceptance may support statements about tested records, supported simulated engine predictions, constraint-checked proposals and scenario-specific simulation outcomes.

It does not establish real military fleet improvements, regulatory certification, whole-aircraft diagnosis, guaranteed failure prevention or airworthiness clearance. Competition presentation and documentation must stay within the evidence actually retained.
