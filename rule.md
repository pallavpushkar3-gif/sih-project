# Project Engineering Rules

Status: initial canonical project rules. These rules describe implementation expectations, not completed checks. Read with `intent.md`, `scope.md` and `design.md`.

## 1. Evidence and Status

Distinguish planned, implemented and validated behaviour. Never invent model outputs, research results, passed checks or operational benefits. Label synthetic fixtures and simulated projections. Cite paper methods and distinguish accessible full-text review, abstract review and reproduction. Model attribution is not confirmed mechanical causation.

## 2. Units and Time

Use explicit units in contracts, records and charts. RUL uses supported dataset units, initially cycles. Calendar projections require a versioned utilisation assumption. Store actual timestamps with timezone-aware UTC semantics; display timezone separately. Dataset cycles are not wall-clock timestamps. Specify scheduling time granularity and rounding. Display transformations must not change inference inputs.

## 3. Scientific Data

Partition by engine according to the dataset protocol. Namespace identities by dataset/subset/source partition; a train engine numbered 1 is not automatically the test engine numbered 1. Fit transformations on permitted training data only. Freeze test usage. Preserve input cutoff boundaries and transformation parity. Record target/capping definitions; they are modelling choices, not physical limits. Imputed values remain identified.

## 4. Model and Uncertainty

Version weights with preprocessing, feature order, units and calibration artifacts. Validate numerical outputs. Do not equate nominal interval coverage with an individual failure probability. Report coverage and width on declared groups. Unsupported or insufficient evidence must produce a documented warning/withheld state. Compare models fairly; a classical model may be the chosen predictor.

## 5. Domain Boundaries

Routes call services. Scientific modules calculate typed results without committing stock or approvals. Shared packages own transformations and business rules; scripts/workers do not duplicate them. Simulation uses immutable scenario inputs and must not mutate live operational records. One Python package can run in several isolated processes.

## 6. Maintenance Constraints

Mandatory deadlines, qualification, capacity, parts and commitments remain hard constraints. A prediction policy cannot override them. Independently validate usable schedules. Preserve solver status; feasible is not optimal, unknown is not infeasible. Diagnose bottlenecks using implemented checks, not invented explanations. Unapproved proposals do not reserve stock.

## 7. Transactions and Approval

Check authorization and current versions on the server. Plan commitment, reservations and audit/outbox records must be consistent. Protect shared stock/resources against concurrent approvals. Repeated commands are idempotent where material effects could duplicate. Do not hold database transactions open during long scientific calculations. Completed consumption is not undone by deleting a plan.

## 8. Jobs and Artifacts

Long calculations run outside API handlers. Design for duplicate delivery, retries, interruption and stale results. Persist results before announcing success. Cancellation request and termination are different. Artifacts require manifests/hashes and resolvable references. Database/filesystem/broker operations do not automatically share atomicity; use the documented outbox/completion design.

## 9. Interface Behaviour

Implement loading, empty, error, denied, stale and degraded states. Do not substitute fake healthy/zero values for unavailable data. Use text with colour indicators. Keep component/cutoff selection consistent across linked views. Runtime-validate API inputs/outputs; generated TypeScript does not validate network bytes. Relevant provenance/assumptions must be inspectable without overwhelming every screen.

## 10. Repository and Configuration

Commit authored code, docs, small labelled fixtures, reviewed migrations and dependency locks. Keep secrets, bulk datasets, weights, generated numerical outputs, dependencies and caches outside source control. Preserve split/artifact versions outside Git with hashes; ignored does not mean disposable. Do not manually edit generated clients or fabricate locks/migrations.

## 11. Verification and Changes

Run checks appropriate to changed behaviour. Prioritize leakage/parity, constraints, reservations, stale approvals, retry recovery, reference simulation cases and principal workflows. Do not add tests mirroring trivial implementation. Update contracts/specifications when behaviour changes and retain honest check results. Architecture/scope changes require a decision record where material; routine choices within agreed scope do not require invented approval rituals.

## 12. Document Ownership

This is the canonical engineering-rule file. `AGENTS.md` references it rather than maintaining a duplicate rule set. User instructions and applicable system/tool instructions govern assistants; this document does not grant external-action permissions. Resolve internal conflicts explicitly and keep planned scope separate from implementation status.

## Release evidence application — 2026-10-05

A new engine-disjoint retraining experiment does not erase earlier use of the same FD001 engines. Label its lifecycle holdout relative to that new model and retain the historical inspection disclosure. Deterministic scenario envelopes have no probabilistic confidence interval. A FIFO placement failure is not a mathematical infeasibility proof. Legacy active work without crew/bay identities must be reconciled or explicitly completed/cancelled before new scheduling; never invent historical reservations. A passing local functional journey cannot substitute for unresolved scientific, human, deployment or customer gates.
