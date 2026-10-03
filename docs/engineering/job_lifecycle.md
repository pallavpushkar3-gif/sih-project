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
