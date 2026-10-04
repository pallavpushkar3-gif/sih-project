# ADR 0005: Persistent local customer trials through shared services

Accepted implementation decision, 2026-10-05.

Customers need to test entered data through the connected maintenance workflow. A static tour or independent browser calculators would conceal whether the integration works. Trials therefore compose the existing immutable ingestion, registered-model inference, durable jobs, planning, simulation, audited approval and stock/work services.

Each trial owns `trial-<uuid>` synthetic aircraft, component, task, stock and dedicated crew scope. Ordinary fleet plans exclude the reserved trial prefix; trial snapshots retain `scope_component_id`, and approval/revisions select and revalidate the same scope. Real delivery and reservation invariants remain authoritative. This models independent rehearsal resources, not extra capacity in a shared operational fleet.

A tagged immutable `Scenario` JSON record stores the trial manifest/request hash and its input/record references without a new relational table. It is excluded from selectable simulation scenarios. Two distinct ordinary Scenario records retain matched supply comparisons. This use is local and bounded; general customer tenancy, pagination and a dedicated trial entity require further design before production expansion.

The routes require development environment plus demo authentication and ordinary planner/supervisor authorization. Production/session deployments reject these routes. Model installation remains an offline administrator process with hash/manifest validation. Browser roles are governed by the existing demo/session contract.

The visible `trial-lower-bound-window-v1` policy converts calibrated interval lower endpoint cycles to hours with entered cycles/day, floors to eight-hour slots and caps at the mandatory deadline. Its assumption and provenance are stored in the plan. This policy is a synthetic demonstration bridge; its clinical/operational decision quality is not an accepted scientific claim. Missing/mismatched assessments block the evidence-informed trial recommendation; impossible windows remain unusable. Standard fleet planning still schedules independently recorded task windows.

This decision preserves existing application/science/persistence boundaries. Atomic creation extends shared fixture/history/delivery services with caller-owned commit support. Approval remains the existing locked transactional service. Evidence: integration tests cover isolation, units/window bounds, withholding/matching requirements, idempotency, receipt staleness and stock/work lifecycle; live browser verification and remaining limitations are recorded in `docs/design/ui_verification.md`.
