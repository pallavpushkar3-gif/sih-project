# Access and Permissions

Status: initial application permission model for the demonstrator; identity provisioning and session implementation pending.

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

## Audit

Record actor/time/version/reason for material adjustments and approvals. Do not treat technical review as aircraft certification. Account provisioning, external identity integration and real operations require separate explicit authorization.
