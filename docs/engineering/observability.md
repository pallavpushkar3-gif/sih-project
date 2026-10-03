# Observability

## Correlation

Propagate request, job, attempt and result identity plus source revision/configuration version through API, dispatch and workers. Record material transitions and conflicts in structured logs. Avoid leaking credentials, raw private records or full sensitive payloads.

## Measurements

Track API latency/error rate, database conflicts/query latency, queue wait/dispatch failures, worker runtime/heartbeat/retries, artifact failures and independent-validation failures. Scientific error/coverage belongs in evaluation reports, not an unexplained operational health counter.

## User Errors

Expose stable codes and actionable messages. Keep stack traces in appropriately controlled logs, not API responses. Distinguish invalid input, inaccessible record, stale state, no solver result and runtime failure.

## Health and Readiness

Liveness means the process runs; readiness checks required dependencies/configuration. Neither asserts a model is accurate. Model registrations need their own validity/support state.

## Verification

Test cross-process correlation and fault cases. Alert budgets/resource targets must be configured from the declared workload; no production SLO is claimed before measurement.
