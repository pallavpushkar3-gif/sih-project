# Product Scope

**Project:** Aircraft Predictive Maintenance & Fleet Availability
**Problem statement:** PS 26249
**Document status:** Initial scope specification; implementation and validation pending
**Related intent:** `intent.md`

## 1. Release Boundary

The initial release is a web-based maintenance decision demonstrator. It connects supported engine-health assessments to maintenance planning, parts and resource constraints, and simulated fleet availability comparisons.

It must demonstrate an end-to-end workflow using evaluated component predictions and explicitly identified logistics assumptions. It is not a production aircraft maintenance or clearance system.

The scope includes the eight features below and the application capabilities required to connect them. Detailed behaviour belongs in `docs/product/feature_specifications.md`; measurable completion belongs in `docs/product/acceptance_criteria.md`.

## 2. Included Features

### F01 — Unified Component and Maintenance Records

Include:

- A demonstrator fleet with aircraft-to-component relationships and clear provenance.
- Component usage and supported sensor history.
- Maintenance task records and associated resource/part requirements.
- Observation timestamps or cycle indices, source identifiers, units and data freshness.
- Links from assessments and plans to their input records.

Boundary: initial ingestion supports documented dataset formats and labelled demonstration fixtures. Arbitrary airline/MRO integrations, scanned-document extraction and automatic reconciliation of unknown schemas are outside this release.

### F02 — Remaining-Life Estimates with Uncertainty

Include:

- Component-level remaining useful life (RUL) estimation on a supported engine dataset.
- Classical and sequence-model comparisons under a common evaluation protocol.
- A chosen model accompanied by its transformation and target definitions.
- Prediction intervals or another explicitly evaluated uncertainty representation.
- Model version, assessment time/cycle and applicable data-quality status.

Boundary: predict in the dataset's supported units, initially operating cycles. Calendar projections require an explicit usage assumption. A life interval must not be labelled as an individual engine's failure probability. Architecture choice does not establish prediction accuracy.

### F03 — Prediction Evidence Card

Include:

- Relevant sensor trends and operating context.
- Model-input influences or an interpretable model explanation appropriate to the chosen predictor.
- Missing/stale data indicators and known applicability limits.
- Prediction/model/input provenance and a link to its evaluation summary.

Boundary: explanations describe model behaviour. They do not establish a physical fault cause, prescribe an aircraft-specific repair procedure or replace technical inspection.

### F04 — Stable Maintenance Alerts

Include:

- A versioned alert policy responding to supported health assessments.
- Alert history, trigger reason and review status.
- Evaluation of persistence/hysteresis or another justified stability mechanism against a simple threshold baseline.
- Explicit handling of unavailable or degraded assessments.

Boundary: alert stability must not hide overdue mandatory work or silently discard important changes. Thresholds and margins require documented configuration and validation; they are not certified maintenance limits.

### F05 — Resource-Constrained Maintenance Planner

Include:

- A finite planning horizon with documented time units.
- Maintenance tasks with duration, deadlines, resource needs and applicable ordering constraints.
- Workshop/bay capacity, qualified technician availability and parts availability assumptions.
- Fixed or committed tasks preserved according to defined planning rules.
- A constraint-based proposed schedule and a simple scheduling baseline.
- Visible solver status and an explanation of known bottlenecks or unmet requirements.

Boundary: the planner respects mandatory constraints. It does not relax them merely to produce a schedule. A feasible solution must not be described as proven optimal without solver evidence. No feasible solution, no solution found within the time limit and invalid input are distinct outcomes.

### F06 — Compatible Maintenance Grouping and Parts Bottlenecks

Include:

- Identification of compatible tasks that can share a grounding within permitted windows.
- Visibility of required parts, stock, lead-time assumptions and shortages.
- Reservation of parts/resources during plan approval with consistency checks.
- Evaluation of fewer groundings against early-maintenance penalties or useful life discarded.

Boundary: grouping requires explicit compatibility and task constraints. Synthetic task/component examples do not establish validated brake, avionics or structural predictions. Initial inventory behaviour uses supplied stock and lead times; learned spare-demand forecasting and automatic procurement are excluded.

### F07 — Fleet Availability What-If Simulation

Include:

- Named scenarios with explicit usage, capacity, logistics and maintenance-effect assumptions.
- Comparison of baseline and proposed maintenance policies on common scenarios.
- Changes to selected inputs, such as spare arrival or workshop capacity.
- Projected downtime, resource queues, stockouts and other defined scenario metrics.
- Repeated stochastic runs where applicable, with seeds and variability retained.
- Scenario and result provenance.

Boundary: availability is defined by the simulation's states and assumptions. It is not synonymous with operational readiness or airworthiness. Effects of maintenance, replacement and usage must be explicitly modelled when not observed in the dataset. A calendar-based simulation requires a documented conversion from engine cycles to calendar usage.

### F08 — Data-Quality and Robustness Controls

Include:

- Checks for missing, invalid, out-of-order and stale observations where meaningful.
- Visible handling of operating conditions outside evaluated support.
- A documented policy for qualifying or withholding an assessment.
- Robustness experiments using missing values, contiguous outages, noise and relevant regime changes.
- Explicit distinction between observed and imputed values when imputation is used.

Boundary: imputation must not be presented as recovered ground truth. Withholding a prediction must produce an understandable state, not an invented healthy status. An unsupported-regime warning itself requires a defined detection method and evaluation.

## 3. Supporting Application Capabilities

The following capabilities are included to make the eight features usable and coherent:

| Capability | Initial boundary |
|---|---|
| Access and permissions | Authenticated demonstrator access and documented permissions for viewing, editing and approving. Detailed role definitions belong in `docs/engineering/permissions.md`. |
| Human approval | Review a proposal, recheck current constraints, approve/reject it and record the decision. Approval changes demonstrator records; it does not authorize real aircraft service. |
| Work records | Track approved work and record completion/outcomes manually or through labelled demonstration events. Physical execution is outside the software. |
| Durable jobs | Track queued/running/completed/failed/cancelled calculations, handle retries and reject stale or superseded results. |
| Live progress | Show calculation progress and relevant updates without forcing the user to keep a long HTTP request open. |
| Audit history | Preserve material changes, approvals, record sources and model/policy/scenario versions. This is traceability, not a claim of regulatory certification. |
| Reproducible evaluation | Retain configurations, dataset/split identifiers, artifact hashes and comparison results. |

## 4. Initial Data Contract

### Supported scientific data

Use a documented public engine-degradation dataset, initially NASA C-MAPSS, to evaluate engine-level life estimation. It contains simulated histories; their origin must remain visible in documentation and the demonstration.

Supported subsets and operating regimes are chosen and recorded in `docs/research/dataset_protocol.md`. A release claiming support for a subset must evaluate it. Do not imply all C-MAPSS subsets or unseen operating conditions are supported merely because the parser accepts them.

Training, validation, calibration and test partitions must be separated by engine as appropriate to the evaluation protocol. Test outcomes must not be used to tune preprocessing, thresholds or models. Preserve the split and target definitions with results.

### Demonstration logistics

Small synthetic fixtures may supply aircraft mappings, maintenance jobs, stock, lead times, technician availability and workshop capacity. Identify these as assumptions, not real service records.

Simulation outcomes based on those fixtures are projected demonstration results. The source dataset does not establish repair duration, actual spare demand, maintenance effectiveness or whole-aircraft availability.

### Required provenance

Every material result must be traceable to the applicable input snapshot and model/policy/scenario version. Units, synthetic inputs, imputation and cycle-to-calendar assumptions must be identifiable.

## 5. Explicit Exclusions

The initial release does not include:

- Whole-aircraft physics twins or validated models of all aircraft subsystems.
- Actual military telemetry integration or claims of military deployment validation.
- Cross-system fault diagnosis, confirmed mechanical root-cause analysis or aircraft-specific repair instructions.
- Automatic airworthiness clearance, safety certification or dispatch approval.
- Exact failure dates derived without supported usage assumptions.
- Learned spare-demand or procurement forecasts without suitable historical data.
- Automatic purchases, supplier communications or other external operational actions.
- Reinforcement-learning scheduling as the default planner before a constraint-based baseline exists.
- Flight/mission assignment optimization or tactical operational planning.
- VR/game environments or decorative 3D as required product features.
- LLM-generated numerical predictions or authoritative schedules.
- A separate Rust/Go/Node backend without a measured requirement.
- Distributed streaming infrastructure, Kubernetes or an additional database without an established workload need.

These exclusions define the release; they do not establish that every excluded technology is unsuitable for future work.

## 6. Extension Gates

| Proposed extension | Evidence required before adding it |
|---|---|
| Additional component predictions | Relevant component data, target/fault definitions and held-out evaluation. |
| Actual aircraft/fleet integration | Authorized data access, documented interfaces, validated record mappings and deployment requirements. |
| Physics-informed model/twin | Supported physical parameters, subsystem assumptions and validation against appropriate measurements. |
| Learned spare-demand forecasting | Demand, repairs, stock and lead-time histories plus a fair forecasting/inventory baseline. |
| Reinforcement-learning planner | Credible simulation environment, hard-constraint handling and comparison with existing policies/solvers. |
| Rust/native acceleration | Profiling identifies a meaningful bottleneck; an equivalent implementation demonstrates a worthwhile improvement. |
| More elaborate infrastructure | Measured scale, retention, reliability or deployment requirements justify its role. |

Record a scope change and its architecture/evaluation consequences before treating an extension as part of the release. Avoid silently expanding the product through implementation details.

## 7. Completion Boundary

The release is complete when all eight features form a coherent demonstrated workflow and the following evidence exists:

1. A documented, validated input and provenance path.
2. Held-out prediction and uncertainty evaluation against defined baselines.
3. Evidence cards and visible data-quality limitations.
4. An evaluated alert policy and traceable alert history.
5. A planner whose returned schedules pass independent constraint checks.
6. Consistent reservations and human approval with stale-plan handling.
7. Reproducible availability comparisons with explicit assumptions.
8. Verified calculation recovery/result consistency and the principal end-to-end user flows.

Numerical targets, supported workloads and pass/fail criteria must be specified before the corresponding evaluation in `docs/product/acceptance_criteria.md` and the research protocols. Do not invent thresholds or claim checks have passed before running them.

## 8. Scope Ownership

`intent.md` explains why the product exists. This file defines its release boundary. Feature specifications define behaviour; acceptance criteria define evidence of completion; `design.md` defines how the system is organized.

If a requested feature changes this boundary, update the relevant specifications and decision records deliberately. Keep implemented status separate from planned scope.

## Current bounded implementation — 2026-10-05

Resource-aware scheduling supports fourteen eight-hour relative slots, crew skill and bay/component compatibility, capacity units, aircraft restrictions, qualification validity, excluded shift/closure windows, precedence, fixed bookings and mandatory deadlines. UTC/calendar conversion rounds available windows inward; the browser configures the relative grid. Exact saved-plan simulation compares matched FIFO/duration assumptions. Expected deliveries remain provisional; received usable stock is required for approval. Quarantine/rejection add no usable stock. Only isolated single-agency deployment is supported. These are demonstrator capabilities; real rosters, telemetry, approved policies and operational validation remain external.
