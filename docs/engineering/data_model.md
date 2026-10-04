# Data Model

Status: implemented ORM/migrations with conceptual relationships below; see the resource/policy extension and release ledger for verified boundaries.

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

## Bounded local trial manifests

Customer trials reserve `trial-<uuid>` record identities. A tagged immutable Scenario assumptions object holds the trial manifest/request hash and component/part/import/model/comparison references; it is not exposed as a runnable scenario. Two separate numerical Scenario records hold matched projections. Scoped plans retain `scope_component_id` and the advisory policy/evidence in their JSON snapshots. No migration is required by this JSON extension. Dedicated synthetic trial resources are excluded from ordinary fleet snapshots/commitments; they do not create extra real shared capacity. See ADR 0005. Production tenancy and scaled collections remain outside this local design.

## Implemented resource/policy extension — 2026-10-05

ORM and reviewed migrations are implemented; the earlier conceptual status above is historical. Head `f537880a4c71` adds resource tables and episode/comparison provenance. `maintenance_resources` own kind, label, capabilities, available half-open windows, capacity, qualification bounds, aircraft restrictions, version and optional trial scope. `resource_bookings` link plan/task/resource/unit/window; `resource_slots` uniquely claim resource/unit/slot. Completion/cancellation releases active slots and retains booking history. Nonnegative free stock/reservations are database constraints. Alert episode context and simulation timestamps are nullable/new where historical facts do not exist. Base maps datetime to timezone-aware SQL timestamps; earlier UTC migration remains authoritative. SQLite uses UTC by convention. Model imports and simulation inputs stay immutable; configuration edits increment versions and invalidate old approval inputs.
