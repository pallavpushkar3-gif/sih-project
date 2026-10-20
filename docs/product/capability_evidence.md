# AeroCare capability and verification index

Reviewed 21 October 2026 against source baseline `1908a94`, plus the documentation changes
introducing this index. This page makes implemented capabilities discoverable; it is not a
new whole-product test run, independent assessment or aircraft qualification.

## Review the product

Start with the [public demonstration](https://sih-34-56-39-7.sslip.io/),
[recorded walkthrough](https://www.youtube.com/watch?v=HlYxblGJHEs) and
[README](../../README.md). The video is a presentation aid; it is not asserted to cover every
current capability. For local reproduction, use the [setup guide](../operations/local_setup.md).
Research data, trained artifacts and optional model services need separate installation.

| Capability | Implementation and test sources | Retained evidence and boundary |
|---|---|---|
| Workspace-first entry, signup and role homes | [Entry gate](../../apps/web/src/features/access/RoleEntryGate.tsx), [account browser tests](../../apps/web/tests/e2e/account-onboarding.spec.ts), [workspace API tests](../../backend/tests/unit/test_workspace_login.py) | [Project status](../team/project_status.md) records the public four-workspace check and the later signup correction. Public demo permissions differ from assigned production roles; historical checks do not establish current login availability. |
| Aircraft onboarding and source records | [Registration service](../../backend/src/fleet_maintenance/services/registration.py), [registration tests](../../backend/tests/unit/test_registration.py) | [Contract](../engineering/aircraft_registration.md): validated, previewable/idempotent records with explicit unknown health. No fabricated score or automatic addition to the monitored fleet's denominator. |
| Connected findings, cases, work and supply | [Case routes](../../backend/src/fleet_maintenance/api/routes/cases.py), [operational approval tests](../../backend/tests/integration/test_operational_case_approval.py) | [Product audit](../team/product_audit_two_pass_2026-10-20.md) covers review, case scope, supply and work transitions. The operational fleet board and research scheduling workflow remain distinct. |
| Guided input-to-completion trial | [Trial browser tests](../../apps/web/tests/e2e/customer-trial.spec.ts), [trial API tests](../../backend/tests/integration/test_customer_trials.py) | [Walkthrough](customer_trial.md): actual supported history input, assessment, constrained schedule, saved-plan comparison, receipt/replan, approval, execution and verification. Requires the installed trial catalogue/model; synthetic logistics and unqualified demonstration data. |
| Multi-subset engine research | [Evaluator](../../scripts/evaluate_research_subsets.py), [frozen configuration](../../configs/multidataset_benchmark.json) | [Protocol](../research/multidataset-demo-protocol.md) retains FD002–FD004 split, withheld-count, calibration and exact reproduction results, separately from historical FD001. Research results do not qualify serving on arbitrary aircraft. |
| Checked research planning and reservations | [Approval service](../../backend/src/fleet_maintenance/services/approvals.py), [stale approval test](../../backend/tests/integration/test_plan_approval.py), [resource tests](../../backend/tests/integration/test_postgres_resources.py) | [Acceptance ledger](../team/release_acceptance.md): independently checked constraints and real PostgreSQL stock/resource contention. Representative calendars, qualifications and operational limits remain external acceptance gates. |
| Snapshot-bound telemetry replay and visual evidence | [Telemetry routes](../../backend/src/fleet_maintenance/api/routes/telemetry.py), [transport tests](../../backend/tests/unit/test_telemetry.py), [live browser test](../../apps/web/tests/e2e/telemetry-live.spec.ts) | [Contract and checks](../engineering/live_telemetry_demo.md): authenticated archived-cycle transport, duplicate/order/freshness handling and shared assessment jobs. Live HTTP replay is not a real aircraft feed; geometry is illustrative. |
| Contextual Ask AI | [Tool registry](../../backend/src/fleet_maintenance/services/assistant/tools.py), [conversation/context provider](../../apps/web/src/features/assistant/AssistantProvider.tsx), [grounding tests](../../backend/tests/unit/test_assistant.py), [privacy tests](../../backend/tests/unit/test_assistant_privacy.py) | [Copilot guide](../operations/ai_copilot.md): selected-record/date context, direct-service answers, optional Qwen inference, linked evidence and role-gated scenarios. Tools do not replace authoritative predictions or human approval. |
| Copilot answer delivery and bounded failure handling | [Stream browser tests](../../apps/web/tests/e2e/assistant-stream.spec.ts), [latency regressions](../../backend/tests/unit/test_assistant_latency.py), [opt-in real-model tests](../../backend/tests/integration/test_assistant_model_live.py) | Final checked text replaces drafts; truncation/errors/cancellation cannot be presented as completed answers. [Local audit](../team/product_audit_two_pass_2026-10-20.md) includes actual cited record answers, with generative inference unavailable in that audit. Later bounded Qwen checks have their own scope; public latency targets remain unaccepted. |
| Durable jobs, retries and event recovery | [Job recovery tests](../../backend/tests/integration/test_job_recovery.py), [job contract](../engineering/job_lifecycle.md) | [Acceptance ledger](../team/release_acceptance.md) records interrupted worker, duplicate/stale result, cancellation and SSE recovery exercises. This is bounded recovery, not exactly-once execution or multi-host failover. |
| Deployment, backup and restore | [Release checker](../../scripts/release_check.sh), [backup/restore runbook](../operations/backup_and_restore.md) | [GCE validation](../operations/gce_validation.md) separates isolated local rehearsal from public VM checks. Local restore matched 49 table fingerprints and artifact hashes; it is not an operational-host recovery SLA. |

## What the recorded checks establish

The [20 October local audit](../team/product_audit_two_pass_2026-10-20.md) retains a corrected
155/155 compiled-browser pass with zero skips/retries, plus two live matrices totalling 336
page inspections and 40 interaction groups. It also records 78 isolated PostgreSQL integration
checks and four-role record-answer agreement with the authoritative API. Some browser cases use
API fixtures; others exercise actual local services, model jobs and worker workflows. The audit's
generative model was unavailable. These facts must be read together.

Subsequent changes have their own scoped results: [project status](../team/project_status.md)
records 303 unit/verification, 24 focused signup/security API and 23 entry/account browser checks
for the workspace correction. Do not add historical counts into an invented current-suite total,
or imply the whole 155-case run was repeated after every later change.

Scientific reproduction is separate from UI regression. The
[selected FD001 evaluation](../research/release_evaluation.md) includes historical test-inspection
disclosure, interval width/coverage and an unpromoted candidate. The
[FD002–FD004 work](../research/multidataset-demo-protocol.md) has its own frozen protocol,
withheld histories and matching reproduction hashes. Neither is observed operational downtime
reduction. Runtime research views need installed evidence bundles rather than Git-tracked weights.

## Current deployed Ask AI versus historical local checks

On 21 October the owner reported that generative Ask AI is fixed and responsive on the public
installation. The recorded local model outage and historical cold-start timings concern their
specific environments and dates; they are not evidence that today's deployed assistant is slow
or unavailable. The code and capability descriptions are published; the local recording is
explicitly a direct-record demonstration. A new deployed generative recording, timed workload
and exact runtime revision/model/configuration comparison remain separate verification work.

## Current release priorities

Use the [release gates](../plan.md#current-release-direction--21-october-2026) to verify the
actual deployed revision before presentation: fresh account/role entry, connected maintenance
transitions, fixed-query copilot correctness and cold/warm latency, and isolated recovery.
Current read-only endpoint results alone cannot establish these authenticated journeys or uptime.

At **2026-10-20 21:20 UTC (21 October IST)**, trusted-HTTPS requests to `/`,
`/api/health/live`, `/api/health/ready` and `/api/access/registration` returned HTTP 200;
readiness reported `ready`/database `ok`, and registration reported enabled. These are fresh
read-only observations, not a new authenticated journey, deployed-revision check or copilot test.

The documented shared demo account was rejected during the 21 October contrast-preview attempt.
That observation does not establish failure of all accounts or signup; it means the old credential
must not be advertised as freshly verified. Preserve the distinction between prior public signup
evidence and present access until a new authorized end-to-end check is completed.

## Evidence publication and repository completeness

The audit found the source baseline and `origin/main` identical after fetching the remote.
No application source changes or unpushed source commits were discovered; the pending changes
were the plan and project-status documentation. This index and README additions expose existing
implementation rather than announcing new runtime features.

Raw evidence under `artifacts/` is intentionally ignored: it can include credentials, browser
state, generated data, model weights and bulky traces. Its absence from GitHub is not a reason
to force-add the directory. Publicly tracked summaries, test sources, protocols, source hashes
and reproduction instructions provide reviewable evidence; they are not substitutes for an
independent rerun. Do not promise that every retained local artifact is publicly downloadable.

Competitor clones/launchers live outside this repository. The contrast comparison was a temporary
isolated preview, not an implemented or deployed colour change. Neither belongs in the application
commit. No superiority, fastest-assistant or competition-ranking claim follows from this audit.
