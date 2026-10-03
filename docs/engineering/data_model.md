# Data Model

Status: conceptual contract for implementation; ORM/migration files pending.

## Identity and Versioning

Use stable opaque record identifiers, separate human-readable labels and explicit revision numbers for mutable proposals/scenarios. Engine scientific identity includes dataset, subset, source partition and engine number. Observation identity includes source/version, engine and cycle plus sensor identity where normalized.

| Entity | Required meaning/relationships |
|---|---|
| Aircraft | Demonstrator identity, provenance and component mappings. |
| Component/mapping | Component type, aircraft installation/mapping context and effective version/time when available. |
| Source/import | Format, provenance, hash/version, acceptance policy and validation outcome. |
| Observation | Component/engine context, cycle/time, sensor/value/unit and observed/imputed provenance. |
| Model registration | Artifact manifest, supported inputs, transformation and calibration references. |
| Assessment | Input cutoff/snapshot, model version, estimate/interval and quality status. |
| Explanation | Assessment identity, method/reference version, output and availability. |
| Alert/transition | Component, assessment, policy, state and review history. |
| Maintenance task | Required work, duration/window/deadline, precedence and resources/parts. |
| Resource/calendar | Capacity, type, qualifications/compatibility and availability. |
| Part/stock/arrival | Identity, quantities, recorded arrivals and provenance. |
| Proposal/assignment | Immutable input version, solver result and scheduled tasks. |
| Approval/work record | Exact proposal, actor/time, committed assignments and actual completion status. |
| Reservation/consumption | Part/resource, plan/task, quantity/window and lifecycle; consumption is distinct. |
| Scenario/run | Versioned assumptions, policies, seed manifest and metric definitions/results. |
| Job/attempt | Input identity, type/state, attempt/lease, result and error references. |
| Outbox/event/audit | Dispatch/update identity, actor/correlation/version and material transition. |

## Invariants

Validate nonnegative stock where applicable, positive durations, valid windows and referential relationships. Public life units remain explicit. Plan/resource conflict protection needs transactions and domain validation as well as database constraints. No proposal changes inventory by existing. Preserve actual consumption even if a plan is later cancelled.

## Snapshot and Storage

Operational relationships are relational. Versioned metadata may use validated JSONB. Large scientific arrays/weights/traces use artifact references and hashes. A result snapshot resolves the exact versions used. Keep history instead of cascading deletion that destroys evidence; define retention/deletion policy before any production data use.

## Concurrency

Use version tokens for mutable commands, idempotency identity for approval/jobs and consistent transaction scopes. Define lock/isolation strategy during persistence implementation and verify conflicting approvals. Do not hold transactions throughout optimization.

## Schema Changes

Implement reviewed Alembic migrations. Test a representative upgrade and restore. The conceptual table list is not permission to invent unneeded tables or duplicated state; refine fields against implemented workflows and document material changes.
