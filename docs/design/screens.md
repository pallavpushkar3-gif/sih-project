# Screen Specifications

## Navigation

Primary navigation: Start, Fleet, Planning. More tools opens Alerts, Parts & deliveries, What-if comparisons and AI & evidence in the shared accessible navigation dialog. `/` opens `/overview`; Fleet navigation opens the searchable `/fleet/register`. The existing `/fleet` illustrative inspection view remains an alternative. Component details are reached from aircraft records/alerts. Jobs appear contextually in planning/scenarios; approval/work history is available from the exact selected plan. See [user flow](../product/user_flow.md).

| Screen | Principal content | Actions |
|---|---|---|
| Start | Brief offer, three decision phases and API-backed aircraft with open work. | Start with fleet; review a component; learn how AI helps. |
| Fleet | Searchable aircraft/component records, maintenance status, freshness and provenance. | Open component; filter. |
| Component | Usage/sensor histories, assessment, quality, alerts and work history. | Choose cutoff; request assessment; inspect evidence. |
| Evidence | Life estimate/interval, trends, influences and model/input versions. | Inspect provenance/evaluation. |
| Alerts | Review state, reason, age/cycle and affected record. | Acknowledge; open evidence/tasks. |
| Planning | Task/horizon inputs, proposal timeline, solver status and constraints. | Compute; revise; open approval. |
| Inventory | Available/reserved/consumed quantities and arrival assumptions. | Authorized correction; inspect shortages. |
| Scenarios | Inputs, alternatives, run state, metrics and variability. | Create revision; simulate; compare. |
| Approval | Exact proposal/version, warning status, resources and audit trail. | Approve/reject according to permission. |

## Content Hierarchy

Prioritize decision context, quality/status, proposed action and constraints. Put detailed manifests/research behind inspectable links. Do not mix predicted health, mandatory task status and simulated availability into an unexplained readiness score.

## Layout

Use an application shell, readable tables and coordinated detail panels. Dense desktop workflows may use side panels; smaller screens stack content and retain essential labels. An editable timeline must have equivalent accessible task forms. Implementation screens must match supported behaviour rather than inventing unvalidated widgets.

## Aircraft inspection redesign (2026-10-04)

`/fleet` opens aircraft inspection: fleet selector, selected aircraft identity, large illustrative GLB, mapped engine annotations/list and an evidence panel. Evidence shows the actual estimate/bounds or unavailable reason, data quality, open task requirements, skill/deadline/part availability and recent alert records. Synthetic aircraft mappings are identified. `/fleet/register` retains searchable records. URL identities retain aircraft/component context when returning from `/components/:id`; planning receives the inspection context but explicitly explains its fleet-wide solver scope.

Component evidence keeps observed history and accessible source-value tables, marks the observed cutoff, and adds model evidence using the actual assessment detail endpoint. Missing explanation metadata does not hide an otherwise valid estimate. The assessment's interval level, sensitivity reference and limitations come from recorded evidence.

Planning keeps its 2D resource timeline, assignment table, diagnostics and solver status. Exact-plan approval dialog precedes transactional rechecks; stock/version conflicts remain errors rather than implied success. Inventory retains actual free/physical/reserved quantities, versioned expected arrivals and reviewed receipt. Scenarios allow a new immutable revision with bay capacity and common synthetic part-availability hour, retain original outcomes, and compare two matching-demand/horizon runs on a shared percent axis. No replication interval is inferred from a deterministic run.

See [viewer](3d_viewer.md), [asset register](asset_register.md) and [verification](ui_verification.md) for rendering, licensing and measured limits.

The selected plan's Reservations & work history panel exposes retained part commitment rows and work outcomes/versions/consumption/timestamps. It does not derive reservations from assignments, and it refreshes only from server records after approval. No-row/proposed/error/mismatched identity states are explicit.

Scenarios uses a retained-revision selector and one active editor so accumulating saved alternatives does not push comparisons behind a growing grid. Saving a new revision selects its actual new identity; older revisions and outcomes remain accessible in selectors.

Customer trials (`/demo`) add four progressive decision stages: entered case and interactive aircraft, computed AI evidence, constrained schedule and matched supply projections, then explicit review/receipt/replanning/approval/work. Start now includes an aircraft poster and a prominent trial CTA; primary navigation is Start / Aircraft / Try demo / Planning. Supporting tools include the fleet register. Saved case inputs/results reopen by URL/library. Model evidence stays connected to entered cutoff and the recorded trial policy. See `docs/product/customer_trial.md` for behaviour and limitations.
