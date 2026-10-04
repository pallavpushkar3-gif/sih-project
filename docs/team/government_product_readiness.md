# Product assessment: PS 26249 and government readiness

Current implementation evidence supersedes the earlier software-gap snapshot below: [release acceptance ledger](release_acceptance.md) and [scientific report](../research/release_evaluation.md). Qualified crew/bay bookings, review episodes, actual-plan comparison and local recovery are now implemented/tested within the demonstrator boundary. The government/customer qualification conclusions remain unchanged.


**Assessment date:** 2026-10-05. **Source:** HEAD `b73bbef039a8f2db44401b58f5119a491a0ec6cb` plus the existing, uncommitted presentation/customer-trial changes. This assessment uses the problem-statement image supplied by the user, inspected implementation and the official sources linked below. It is not an agency acceptance, security certification or procurement opinion.

## Decision

The product is a relevant, functioning maintenance decision demonstrator. It is **not a fully accepted release, a validated military fleet product, or ready for unrestricted commercial operational use**. Completing the local customer trial means completing that bounded demonstration journey; it does not mean completing the original release or government procurement requirements.

The strongest capability is the connected workflow: entered history → actual model evidence → an explicitly identified review policy → constrained proposal → parts receipt/replanning → human approval/reservation → work completion. Immutable inputs, quality withholding, stale checks and transactional inventory give this more substance than a presentation-only dashboard.

The largest remaining gap is demonstrating that this workflow works on the intended customer's aircraft, records, resources and operating decisions. Additional visual polish cannot supply that evidence. Government selection, commercial value and hackathon placement cannot be predicted from the code or a screenshot.

## Mapping the supplied problem statement to the implementation

| Problem-statement need | Implemented behaviour | Boundary before operational use |
|---|---|---|
| Integrate fragmented health, technical and spares records | Supported history/fixture imports, aircraft/component links, provenance, maintenance tasks, inventory and deliveries share one workspace. | No demonstrated connection to a target health-monitoring system, technical-record system or maintenance agency. Agree identifiers, units, corrections, freshness and reconciliation with the customer; verify connectors and permitted data access. |
| Predict deterioration before reactive maintenance | Registered C-MAPSS FD001 engine remaining-life predictor, cutoff-bound inference, calibrated intervals and quality withholding. Model evidence is visible in the workflow. | FD001 is simulated engine data. Retained benchmark results do not establish performance on an Indian military aircraft, different subsystem or operating regime. The installed customer-trial model is registered `not_qualified`. |
| Turn predictions into executable maintenance | CP-SAT proposals, independent schedule checks, deadlines, parts/arrivals, crew capacity and commitments; fresh approval reserves actual recorded stock. | Current snapshots use fourteen eight-hour slots with configured qualified crew/bay capacity, compatibility, validity, calendars and exclusive bookings; the time grid remains coarse. Customer rosters, shifts, platform qualifications, tools, locations and operational task rules need agreement and verification. |
| Reduce downtime and improve availability | Saved SimPy scenarios, matched comparisons and separate waiting/downtime metrics. | The trial retains its separately labelled parts-ready sensitivity and now additionally replays the exact immutable saved schedule against constrained FIFO under declared duration/overrun assumptions. It does not model predicted failures or maintenance effectiveness. No observed fleet benefit has been established. |
| IoT and digital-twin opportunity | Illustrative interactive aircraft, component selection and linked evidence; supported history ingestion. | No demonstrated live aircraft telemetry connector or validated physical/operational twin. A visual aircraft is not a digital twin. Agree whether a twin is needed for the customer's decision before promising or building one. |
| Coordination and accountability | Roles, server sessions, audit/outbox records, durable jobs, explicit approval and work outcomes. | The local trial uses demo authentication and is deliberately unavailable outside development/demo mode. Operational authority, agency separation and the production evaluation environment remain to be designed/accepted. |

Evidence: [customer-trial contract](../product/customer_trial.md), [planning service](../../backend/src/fleet_maintenance/services/planning.py), [trial service](../../backend/src/fleet_maintenance/services/customer_trials.py), [demo access boundary](../../backend/src/fleet_maintenance/api/routes/demo.py), and [retained readiness evidence](../operations/production_readiness.md).

## Relevance and innovation

The problem remains commercially relevant: Airbus documents deployed predictive-maintenance and health-monitoring products, including their selection by Philippine Airlines in 2024. This establishes that the category exists; it does not establish equivalence with this demonstrator or military suitability. [Airbus announcement](https://aircraft.airbus.com/en/newsroom/press-releases/2024-11-philippine-airlines-selects-airbus-for-predictive-maintenance).

AI, dashboards and a 3D aircraft alone are not demonstrated novel contributions. A credible differentiation hypothesis is a customer-approved deployment that connects heterogeneous fleet records to uncertainty-aware, resource-feasible and auditable maintenance decisions across the intended agencies. Test that hypothesis against existing systems, manual/reactive planning and simpler baselines. Sovereign deployment, disconnected operation and multiple bases are potential requirements, **not claims that those capabilities are already validated**.

Prioritize model suitability, calibrated support boundaries, alert usefulness and decision outcomes over adding an LLM or a newer neural architecture. Keep supported dependency versions locked; review security advisories, compatibility and lifecycle support before changes. This assessment has not performed a dependency vulnerability audit and makes no claim that particular dependencies are insecure.

## What each stakeholder needs

| Stakeholder | Decision and evidence needed |
|---|---|
| Daily user: engineer, planner, logistics coordinator, supervisor | Identify what needs attention; inspect the evidence; understand the blocking part/resource; propose/revise work; approve within authority; record outcomes. Test those role-specific tasks with intended users, including uncertain/infeasible/stale outcomes and intended devices. |
| Customer/buyer | A defined initial fleet/component use case, integration effort, attributable operational value, total ownership cost, support/service commitments, licensing/IP terms, data ownership and exit/export arrangements. A demonstration is not an accepted business case. |
| Government/user agency | Ratified requirements and acceptance tests, approved deployment/data-access conditions, operational authority, platform-specific validation and trials, security assurance, reproducible installation/restore and accountable vendor support. The agency must determine the applicable standards and procurement route. |
| Hackathon evaluators | A traceable response to the supplied PS, working input-driven demonstration, clear technical contributions, honest evidence/limitations and a feasible adoption plan. Demonstrate changed data and adverse cases, not just explanatory copy. |

The official iDEX product-management guidance addresses user utility, buyer value, operational constraints, measurable performance and integration. It is useful planning guidance, not automatic acceptance of this product. [iDEX product-management guidance](https://idex.gov.in/uploads/resources/1700215966_01115b225ef4d436c635.pdf).

## Prioritized productization backlog

These priorities extend the original demonstrator; they are not newly accepted requirements or a fixed delivery estimate.

| Priority | Work | Completion evidence |
|---|---|---|
| P0: agree the operational product | Choose one customer fleet/component and maintenance decision. Obtain approved requirements, maintenance policies, data permissions, representative inputs and success/error budgets. Define purchase/deployment/support expectations. | Ratified requirement-to-acceptance matrix, documented support boundary and agreed baseline. |
| P0: integrate the actual information | Build agreed health/history/logistics connectors and reconcile aircraft/component identities, units, configuration changes and record corrections. Expose data freshness and provenance. | Representative end-to-end imports and reconciliation; invalid/stale/conflicting sources produce defined outcomes. |
| P0: make the decision chain operationally valid | Accept the implemented qualified-bay/crew/calendar model against actual customer resources. Have domain reviewers approve the prediction-to-task policy. The exact-plan comparison is implemented; qualify its downtime and any later failure/repair assumptions against representative customer evidence. | Independently checked representative schedules, races and commitments; a traceable plan-to-simulation comparison that beats or explains tradeoffs against its declared baseline. |
| P0: establish safe operational access | Validate existing session/role/CSRF controls in the intended environment. Agree whether federation/MFA, agency/base isolation and stronger audit protection are required. Separate a customer evaluation sandbox from operational stock and authority. | Threat review and agreed security tests; denied cross-scope access; accountable approvals; development demo routes remain disabled in operational production. |
| P0: prove the user flow | Keep a guided seller/customer case, then provide role-appropriate operational queues and actions. Make freshness, uncertainty, missing parts, infeasibility and job failure understandable. Provide useful review/export/handover outputs. | Intended users complete tasks without coaching and correctly interpret uncertainty and projections; keyboard, zoom and agreed devices pass. Current browser tests do not establish this. |
| P1: qualify the AI and alerts | Use permitted representative histories with independent partitions; freeze error, interval, warning-time and false/missed-alert budgets. Complete explanation/robustness gates and define drift/OOD monitoring and fallback. | Retained independent evaluation and shadow-operation evidence within a specific fleet/component support boundary. Do not relabel already inspected final-test data as untouched. |
| P1: scale and recover | Replace broad collection polling with scoped/paginated retrieval where the agreed workload requires it. Measure chart/3D cost on intended devices. Complete fault/reconnect coverage, event retention and supported job/runtime limits. Design redundancy if required. | Frozen workload/hardware budgets and API/worker/UI measurements; demonstrated recovery at agreed failure points and acceptable data-loss/recovery limits. |
| P1: package and support a paid release | Pin the reviewed release and every required artifact; retain dependency/asset notices and an SBOM. Validate installation, migration, database-plus-artifact backups/restore, secrets, HTTPS, upgrades and rollback on the approved target. Define support and commercial obligations. | Reproducible release evidence index, operator runbook, successful target-environment acceptance/restore and agreed license/support terms. Existing CI and deployment templates are preparation, not proof of deployed acceptance. |

The aircraft/font sources and notices are already recorded in the [asset register](../design/asset_register.md). Commercial release should extend this provenance to the complete software/data/model supply chain rather than assume all licensing work is absent.

## Government and hackathon route

Government interest in this category is plausible, and iDEX explicitly includes software/AI challenges. Its FAQ places requirement validation, trials and acceptance with the concerned agencies and states that DIO does not assure a pilot order or commercial quantity. This does not determine the route for PS 26249 or guarantee a contract. [Official iDEX FAQ](https://idex.gov.in/faq).

For this project, the practical sequence is: bounded working demonstration → agreed user-agency requirements and data → shadow evaluation → contracted/authorized pilot if selected → production acceptance and support. These are proposed gates, not awarded stages or a claim that hackathon success purchases the product. Platform-use authorization remains separate from an application supervisor approving a plan; the product does not grant aircraft clearance.

The supplied image is the basis for this PS assessment. An official 2026 evaluation rubric was not confirmed during this review. The published SIH **2024** guidance includes novelty, feasibility, usability and impact; use it as historical context only and obtain the organizer's actual 2026 rubric before claiming compliance. [Official historical SIH guidance](https://sih.gov.in/letters/Guidelines-College-SPOC.pdf).

## Remaining work and verification

The [current acceptance ledger](release_acceptance.md) tracks eight workstreams with bounded local checks and unresolved original acceptance gates. Resource planning, exact-plan replay and recovery mechanisms now have evidence; independent operational alerts, explanation/robustness acceptance, intended-user/workload qualification and public deployment remain incomplete. The commercial priorities above add customer-specific integration, operational qualification, deployment/security and business/support obligations. These are substantial productization work, not a count of cosmetic fixes. No defensible percentage or completion date exists until the customer requirements, data and acceptance workload are agreed.

During the earlier documentation assessment, `COREPACK_HOME=/tmp/fleet-corepack make web-check` was rerun: lint, TypeScript, production build and all six Vitest tests passed. The build still reports large lazy chart and aircraft chunks: approximately 542 kB and 1,004 kB minified (184 kB and 269 kB gzip). Those sizes are not measured load times. Review target-device performance before choosing optimizations.

In that earlier documentation assessment, backend/live-browser/scientific records were reviewed, not rerun. The new implementation assignment reran them; its evidence is in the current acceptance ledger. They retain their original conditions, failures and support boundaries. No new model qualification, operational trial, security audit, government contact or deployment occurred. The earlier assessment changed documentation only. The subsequent implementation changed application behavior as detailed in the current ledger.
