# ADR 0004: Aircraft inspection as the entry workspace

Date: 2026-10-04. Status: accepted for the demonstrator implementation; user-study and performance acceptance are separately evidenced.

The previous record-oriented fleet surface did not provide immediate spatial selection and a connected evidence-to-decision path. The user authorized the supplied aircraft redesign direction and the complete attached brief.

Keep React/TypeScript/Vite and FastAPI. Add React Three Fiber 9, Drei and Three.js, a locally licensed Cesium aircraft GLB and locally served Inter. Use a compact neutral shell and make `/fleet` an aircraft inspection surface; retain the existing fleet register at `/fleet/register`. Geometry communicates location/selection only. Scientific evidence, maintenance constraints, approval and comparisons stay in 2D and use real backend results.

Add read-only component maintenance context from authoritative task/free-stock records. Add explicit global synthetic part-availability time to immutable scenario revisions and the shared SimPy calculation, retaining separate part wait and bay queue wait. This assumed common supply time is not an inventory forecast or an operational lead-time estimate. It does not mutate deliveries, reservations or previously saved outcomes.

Preserve role checks, durable jobs, model/input provenance and exact-version transactional approval. Do not change scientific gates or label source textures/airframe shape as operational fleet data. Unknown/unmapped geometry remains Not assessed. No working scientific output is replaced with display fixtures; fixtures exist only in named tests.

Consequences: the 3D runtime increases browser assets, so it is lazy loaded, bounded and demand rendered. Keyboard component selection and a model poster provide functional fallback. The source asset has only two illustrative engine positions and does not support a meaningful maintenance explode view. Published research motivates the design but does not validate this prototype. External deployment, independent complete-history alert evaluation and operator-approved alert/cost targets remain blocked by their stated prerequisites.

The final approval-to-history presentation adds an authenticated read-only plan commitment endpoint over existing reservation/work tables. It requires no schema or transactional mutation change. The UI shows exact-plan retained rows rather than treating aggregate stock totals as per-plan history.
