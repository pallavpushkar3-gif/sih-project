# Users and Workflows

## Intended Responsibilities

Maintenance planners construct proposals; technical reviewers inspect assessment evidence; logistics coordinators maintain stock/arrival information; supervisors approve plans and compare projected outcomes. Exact permissions are defined separately.

## Main Workflow

1. Browse labelled fleet/component records.
2. Select a supported component and historical cutoff.
3. Inspect quality, estimate/interval and model evidence.
4. Review the alert history and mandatory tasks separately.
5. Select tasks/horizon and request a proposal.
6. Inspect resource/parts constraints and grouping tradeoffs.
7. Revise assumptions as a new version where needed.
8. Compare proposals/policies in a named simulation scenario.
9. Review the exact proposal and approve with current-state checks.
10. Record work/consumption/completion and retain historical evidence.

## Alternative Flows

- Insufficient history: show why prediction is unavailable; existing mandatory tasks remain visible.
- Parts shortage: show quantity/arrival assumptions; do not fabricate stock or silently relax deadlines.
- No solver result: distinguish infeasible, unknown/time-limit and execution failure.
- Stale proposal: require refreshed review; approval cannot silently change the submitted plan.
- Interrupted job: retrieve authoritative state after reconnect/recovery.

## User Success

A user understands the recommendation, its limitations, the proposed action and its constraints. This is not proof that the recommended plan improves actual fleet operations.
