# API Contracts

Status: proposed API semantics. Generate final OpenAPI from implemented FastAPI routes and keep this document aligned.

## Conventions

Prefix application routes with `/api/v1`. Use opaque identifiers, explicit versions/units, timezone-aware timestamps and structured quality/provenance. Paginate collections and bound history windows. A success response must not imply unperformed validation.

Errors include a stable `code`, readable `message`, optional field/details and `request_id`, without secret/internal trace disclosure. Distinguish unauthenticated (401), forbidden (403), missing (404), version/stock conflict (409), invalid input (422), temporary service failure (503) and unexpected failure (500). Use 202 for accepted long jobs; distinguish accepted work from completed results.

## Proposed Endpoint Groups

| Operation | Proposed route | Semantics |
|---|---|---|
| Session | `POST /session`, `GET /session`, `DELETE /session` | Auth/session identity/logout. |
| Fleet | `GET /fleet`, `GET /fleet/{id}` | Permitted records and provenance. |
| Components | `GET /components/{id}` | Component and linked current/history metadata. |
| Observations | `GET /components/{id}/observations` | Bounded cycle/time query with units/quality. |
| Imports | `POST /imports`, `GET /imports/{id}` | Authorized supported-format import and outcome. |
| Assessment request | `POST /components/{id}/assessments` | Cutoff/model/input version; returns existing exact result or job reference. |
| Assessment retrieval | `GET /assessments/{id}` | Estimate/interval/quality/provenance. |
| Evidence | `GET /assessments/{id}/evidence` | Same assessment version and explanation availability. |
| Alerts | `GET /alerts`, `POST /alerts/{id}/acknowledgements` | Review signal/history; acknowledgement is not resolution. |
| Tasks/resources | `GET /tasks`, `GET /resources` | Planning records, capacities and permissions. |
| Proposals | `POST /proposals`, `GET /proposals/{id}` | Versioned planning request/result; no reservation. |
| Revision | `POST /proposals/{id}/revisions` | New input version/request, never hidden mutation of old result. |
| Approval | `POST /proposals/{id}/approvals` | Expected version and idempotency identity; atomic current-state checks. |
| Plans/work | `GET /plans/{id}`, `POST /work-records/{id}/updates` | Approved records and authorized actual progress/consumption. |
| Inventory | `GET /inventory`, `POST /inventory/adjustments` | Quantities/arrivals; traceable corrections. |
| Scenarios | `POST /scenarios`, `POST /scenarios/{id}/revisions` | Versioned assumptions. |
| Simulation | `POST /scenarios/{id}/runs`, `GET /simulation-runs/{id}` | Durable run/result with comparison context. |
| Jobs | `GET /jobs/{id}`, `POST /jobs/{id}/cancellation` | Authoritative lifecycle; request not guaranteed termination. |
| Updates | `GET /events` | Authorized SSE with cursor/replay policy. |
| Health | `GET /health/live`, `GET /health/ready` | Process and dependencies; no scientific reliability claim. |

## Contracts by Result

Assessment identifies component, input cutoff/snapshot, model/calibration, unit, point/interval, support/quality and evaluation reference. Proposal identifies tasks/input versions, horizon/unit, solver status, assignments, validation result and objective/bounds when available. Simulation identifies scenario/policies, horizon/state definitions, sampling/replications and metric units. Job identifies type/attempt/state/timestamps, optional measured progress and result/error reference.

## Mutation Consistency

Approval/revision/correction submits the expected record version. Use an idempotency key where retries could duplicate effects; identical keys with different request bodies are conflicts. A client confirmation dialog is not authorization. Job creation requires valid immutable input identity before enqueueing.

## Generated Client

Export OpenAPI from implemented code and generate the TypeScript client through the configured tool. Check regeneration in CI once implemented. Do not maintain a contradictory handwritten schema or invent executable routes before implementation.
