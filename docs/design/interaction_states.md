# Interaction States

| State | Required response |
|---|---|
| Loading | Identify what is loading; keep known context where safe. |
| Empty | Explain absence of records/results and permitted next action. |
| Failed/unavailable | State the operation/problem; offer retry when appropriate; no fake output. |
| Denied | Explain the action is unavailable under current access; preserve other permitted views. |
| Stale | Show version/freshness and refresh/review action. |
| Qualified | Show valid output with explicit limitations. |
| Withheld | Show why no prediction is available; no numerical substitute. |
| Queued/running | Link to job state; progress may be indeterminate. |
| Cancellation requested | Distinguish request from confirmed termination. |
| Conflict | Explain changed state; reload/review without silently losing edits. |

## Mutations

Disable repeated UI submission while pending but enforce idempotency server-side. Do not optimistically show stock reservation/plan approval as final before server confirmation. Keep failed unsaved edits recoverable where possible.

## Versioned Results

Revised inputs create a new result request. A late result for an older selection must not replace the current view without identification. Live events invalidate/refetch authoritative records and are deduplicated by event identity.

## Historical Replay

Keep the cutoff visible; changing it changes assessment/evidence context. Future data must not appear as if available at that cutoff. Explanations and plots must refer to the displayed assessment version.

## Aircraft inspection and scenario revisions

Fleet loading/error/empty states are driven by requests; a retry never inserts fallback aircraft counts. Aircraft changes reconcile the selected component. Component records must match both aircraft and component ID before display. Missing/mismatched evidence is explicit. Only verified engine identities receive installation controls. Remaining geometry is Not assessed. Model loading is bounded; renderer/asset/context failure leaves the poster, mapped list and 2D evidence/actions available. The list and annotations use the same selection callback. Camera actions have names, bounded distance and immediate changes.

Scenario revision form labels supply time in hours from scenario origin, capacity, and a new revision name. A supply time must be nonnegative and before the horizon. Existing maintenance demand/horizon are retained in the revision request; missing demands cannot be invented. Submission/errors/success are separate from simulation job state. The saved revision does not mutate its parent or deliver physical inventory. A comparison requires two distinct saved runs with matching retained horizon, aircraft count and maintenance events; mismatched or absent assumptions show a reason instead of a projected improvement.
