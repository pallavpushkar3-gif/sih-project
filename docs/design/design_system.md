# Design system

The workspace uses generous neutral space and a compact 64px header with three primary destinations: Start, Fleet and Planning. The shared navigation dialog groups supporting tools separately. The default Start page has a concise offer and one main action; it imports no chart or 3D renderer. The product name remains Aircraft maintenance / PS 26249. Existing backend records drive component identity, quality, evidence, task constraints, proposals, stock and outcomes.

## Semantic palette

| Token | Value | Purpose |
|---|---|---|
| bg-page / bg-surface / bg-stage | #F4F5F7 / #FFFFFF / #E9EDF1 | Workspace, panels, model studio |
| text-primary / text-secondary / text-muted | #18212B / #46515F / #596574 | Hierarchical readable text |
| border-subtle / border-control | #D8DEE6 / #7A8796 | Grouping and interactive boundaries |
| accent / accent-hover / accent-soft | #2457C5 / #1D46A0 / #EAF0FF | Actions and selection |
| success / success-soft | #176344 / #EAF5EE | Recorded successful status |
| warning / warning-soft | #8A4B0F / #FFF3DF | Attention with explicit reason |
| danger / danger-soft | #A52A32 / #FCECEE | Errors/conflicts |
| unknown / unknown-soft | #596574 / #EDF0F3 | Unavailable/not assessed |
| focus | #2457C5 | Visible keyboard focus |

`tokens.css` owns these values. Charts and the aircraft renderer read the CSS variables through `semanticColor`. Status carries readable text as well as visual marking; unknown is never green. Colours do not establish a physical fault cause or aircraft clearance.

Inter is served locally with its OFL notice. Body 15/24, navigation/buttons 14/20, metadata 13/20, main heading 28/36 semibold, aircraft identity 36/44, section 20/28, panel 16/24 and assessment 32/40. Quantities use tabular numerals. Controls target at least 44px. Desktop gutters 32px, gaps 24px, panel padding 16px, panel radius 16px and control radius 10px.

At desktop sizes the inspection model/evidence form a roughly 2:1 split with a minimum 340px evidence panel. Below 1200px they stack; below 768px gutters are 16px and the scene is 300px high. Supporting fleet selection and related decision links remain readable. Tables scroll inside their containers rather than widening the page. Dense quantitative evidence stays in 2D ECharts with tables/text alternatives. Reduced-motion preference disables nonessential transitions, and the camera is immediate in all modes.

The single estimate uses a dot and whisker plus numerical interval endpoints. Interval level is shown only when actual assessment calibration metadata supplies it. A historical cutoff marker separates observed sensor values from unobserved future histories; no density curve, future sensor reconstruction or failure probability is fabricated. Sensitivities retain the server's reference/method/version and noncausal limitations.

The customer trial uses one visible decision stage, a four-step accessible progress list, an aircraft/input split view and compact constraint/comparison results. Stage changes preserve the case URL; pending work shows actual durable job states. Card spacing, labelled manual cutoff input plus accessible range control, semantic token colours and mobile stacking apply. Start uses the local aircraft poster; 3D loads on Aircraft / Try demo. Technical hashes stay in expandable provenance; input origin, quality, units and assumption meaning stay visible.

## Current operations layout rhythm — 2026-10-09

The shared frosted navbar has identical geometry and destination order across operations, aircraft and research pages: 72px desktop / 62px mobile header, shared responsive gutters/radius, search/theme/alerts/account tools, seven primary destinations, Workflow and More. Research tools are retained under More and the same mobile destination list; the navbar no longer shrinks on aircraft routes or switches to lab-only links. Expanded dropdowns scroll within the viewport. Route-specific active state and server-backed badge counts remain dynamic. Login/session gates are outside the workspace navbar.

The operations theme uses a shared 20px page-section gap (16px below 760px), whether a route renders a fragment or an explicit screen wrapper. Page-level card/grid margins do not add a second gap. Desktop content gutters are 24px; mobile gutters are 16px. KPI grids fit available width, become one column below 480px and wrap explanatory text instead of truncating it. Heading subtitles and panel actions wrap on narrow screens. Charts contain their drawing surface during responsive resize; wide tables retain their own horizontal scroll area. Long maintenance action labels wrap without widening the page. Spares part identifiers are keyboard-operable inspection buttons. The shared frosted header and data/decision semantics are unchanged by these spacing fixes.

## Shared canvas and replay placement — 2026-10-10

The workspace canvas uses reference-inspired olive (#699B45) and lime (#C2D575) washes on the left, with fixed viewport geometry across operations, aircraft and research routes. The light/dark themes adjust opacity; existing fonts, content layouts and semantic status colours remain intact. Single-value native selects share a 16px chevron centered vertically, inset 12px from the right, and a 36px trailing text gutter. Native option selection and keyboard interaction remain available; forced-colour mode restores the native arrow.

The former context row below navigation is removed. Replay sits at the right of the heading on every operations page (2026-10-11), including the workflow and supporting pages. Aircraft detail and Welcome use a right-aligned row above their main presentation. There are no bottom docks. On mobile replay wraps within the heading area above the content, with date scrubbing, play/pause and return-to-live retained. Research routes retain their own scientific cutoff controls. Synthetic-environment and API-connection text appear in the shared footer; replay cutoff and read-only decision rules are unchanged.
