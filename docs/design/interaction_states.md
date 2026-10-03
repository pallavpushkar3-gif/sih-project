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
