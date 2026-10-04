# Job Lifecycle

## Authoritative States

`queued`, `running`, `succeeded`, `failed`, `cancellation_requested`, `cancelled`. Supersession is tracked through input/result applicability and may mark a job obsolete; do not overwrite history with a new request.

An attempt has its own identity, worker ownership/lease and timestamps. A retry creates a new attempt according to a bounded, configured policy. A terminal attempt does not necessarily mean the overall job is terminal if a retry is pending.

## Submission and Dispatch

Validate/snapshot inputs, then save job and outbox entry in one PostgreSQL transaction. A dispatcher publishes job references with publisher confirmation. Mark dispatch separately. Interrupted publication can duplicate delivery; consumers claim attempts atomically. Large bytes are artifact references.

## Execution

Validate that the job/attempt is eligible before calculation. Run outside long transactions, heartbeat where needed, report measured/indeterminate progress honestly and retain correlation/version information. Separate worker resources for inference/planning/simulation as needed.

## Completion

Persist output bytes/manifests before registering a usable result. Transactionally accept completion only from the current eligible attempt and applicable job. Persist update/outbox state with accepted result metadata. Reject late results from cancelled/superseded attempts; reconcile orphaned artifacts separately.

## Retry and Failure

Classify transient transport/resource failure separately from invalid input/model and scientific infeasibility. Retry only eligible errors with configured bounds/backoff. Avoid retries duplicating approvals, reservations or result registration. Capture failure codes without sensitive stack details in user responses.

## Cancellation and Recovery

A cancellation request transitions state and signals cooperation. Confirm `cancelled` only when the policy establishes no further result will be accepted. A worker may still consume compute after logical cancellation; document termination mechanics. Reclaim expired attempts only under defined lease/retry rules, and prevent old attempts from later becoming authoritative.

## Required Race Cases

Duplicate message; publish-before-dispatch-mark failure; worker loss before/after artifact write; completion-before-ack loss; cancellation versus completion; new attempt versus old result; API restart; reconnect after event retention gap. Evidence belongs in acceptance records.

## Implemented recovery boundary (2026-10-04)

A job stores owner, current attempt number, lease and start/finish timestamps; durable job_attempts now retain each newly claimed attempt from migration eab4b05e021f. Older absent attempt records are not fabricated. Default leases are 300 seconds and recovery is bounded to three attempts. The dispatcher regularly requeues expired running attempts and publishes their new outbox entries; exhausted attempts fail explicitly. Expired cancellation requests become cancelled. Celery uses late acknowledgements, worker-loss rejection, prefetch one and soft/hard time limits shorter than the lease. No lease-extension heartbeat is implemented; configure leases above supported calculation runtimes.

Workers copy immutable inputs, end the read transaction, calculate through shared science modules, then register results and accept the current eligible attempt in one transaction. Cancellation/expired ownership causes rollback of unaccepted result rows. The main browser uses queued planning and simulation APIs. Legacy synchronous proposal/run routes remain available for small reference fixtures; their calculations also release read transactions first and are not the recommended long-running interface.

A real running worker was killed and restarted in the isolated local test stack; the recorded job recovered on attempt two. Transactional tests cover stale completion, duplicate results, cancellation and publication failure. This does not establish all broker/API kill points, event-retention gaps or high availability. The single-host deployment has no automatic host failover.


### Attempt retention contract

Each claim creates a unique `(job_id, number)` row with the worker hostname/process ID and UTC lease/start times. Success, failure, explicit recovery, expired-lease recovery and confirmed cancellation retain an outcome/state/finish time in the same job transaction. Active leases are preserved on historical attempts after the Job lease is cleared. GET `/api/jobs/{id}/attempts` returns numbered history. Duplicate/stale completion cannot modify an older closed attempt. No worker identity alone grants ownership; job number/state/lease checks remain authoritative. The live kill/restart rehearsal retained expired then succeeded attempts, and the new table was restored with all rows intact.

## Additional recovery behavior — 2026-10-05

Transient database/time-out failures requeue with recorded interrupted attempts, bounded by the configured attempt maximum; invalid inputs fail permanently. Workers check cancellation before computation and fence acceptance afterward. Native computation is bounded by solver/Celery time limits; cancellation is not immediate interruption. `plan_simulation` calculations use the shared science module and exact immutable inputs, with per-job result identity and serialized per-plan scenario registration. Real fault-injection evidence is in the release ledger; no exactly-once or host failover guarantee is made.
