# Access and Permissions

Status: demonstration-header role enforcement implemented for current mutations; identity provisioning, record scoping and cookie-session implementation pending.

## Role Responsibilities

| Role | Permitted responsibilities |
|---|---|
| Viewer | Read records/results within assigned scope. |
| Technical reviewer | Viewer plus request assessments and acknowledge/review alerts. |
| Planner | Viewer plus create/revise planning and simulation scenarios/proposals. |
| Logistics coordinator | Viewer plus authorized stock/arrival corrections and bottleneck review. |
| Maintenance supervisor | Read applicable evidence and approve/reject/cancel plans or record authorized work outcomes. |
| Administrator | Account/role/configuration administration; operational approval is a separately granted permission. |

An account may hold multiple responsibilities. Dataset import, model registration and policy activation are explicit controlled permissions assigned to appropriate maintainers, not implicitly granted by read access. Final record scoping follows actual deployment needs; do not invent tenant isolation claims.

## Enforcement

Authenticate every protected command/query and check operation plus record scope on the server. Verify expected versions for material edits. Hiding a button does not enforce access. Test denial leaves state unchanged.

## Session Design

For the single-origin browser demonstrator, prefer a maintained server-side session/auth library with opaque session cookies. Configure HttpOnly, appropriate Secure/SameSite, expiry and CSRF protection for state-changing requests. Define local development exceptions explicitly. Do not write a custom cryptographic scheme or put session secrets in fixtures.

The current local-only build reads `X-Demo-User` and `X-Demo-Role` headers and labels the session authentication mode accordingly. This is test/demo identity injection, not deployable authentication. Planning, approval, scenario-run, durable-job submission and cancellation mutations enforce the planner/supervisor role on the server; tests verify viewer denial leaves plans, runs and jobs unchanged.

## Audit

Record actor/time/version/reason for material adjustments and approvals. Do not treat technical review as aircraft certification. Account provisioning, external identity integration and real operations require separate explicit authorization.
