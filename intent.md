# Project Intent

**Project:** Aircraft Predictive Maintenance & Fleet Availability
**Problem statement:** PS 26249
**Document status:** Initial product intent; implementation and validation pending

## Purpose

Build a maintenance decision workspace that helps aircraft maintenance teams connect component-health evidence with executable maintenance plans and understand the projected effect on fleet availability.

The product should help a planner answer:

> What needs attention, how reliable is that assessment, what work can we perform with the resources available, and how does the proposed plan affect aircraft downtime?

Our goal is to support informed maintenance decisions through one traceable workflow, from incoming data to a reviewed plan. Predictions, recommendations and simulated outcomes must retain their evidence and limitations.

## Problem We Are Addressing

Aircraft availability depends on more than detecting deterioration. Maintenance teams must bring together health-monitoring data, technical histories, required work, spare parts, technicians and workshop capacity.

When these records are fragmented, a health concern can be identified without a practical way to act on it. A proposed task may be blocked by a missing part, unavailable crew or an occupied bay. Changing forecasts can also cause repeated replanning. An apparently precise prediction can conceal incomplete data or substantial uncertainty.

We intend to connect these information and decision gaps. The product should expose what is known, what remains uncertain, what prevents action and which maintenance options are feasible under the stated constraints.

## Primary Users

| User | Decision the product should support |
|---|---|
| Maintenance planner | Decide which tasks to propose, when to perform them and which resources they require. |
| Maintenance engineer or technical reviewer | Inspect sensor evidence, prediction reliability and the basis for a recommendation. |
| Parts or logistics coordinator | Identify shortages, understand lead-time effects and manage reservations for approved work. |
| Fleet maintenance supervisor | Review projected downtime, compare alternatives and approve plans within their authority. |

These are intended responsibilities, not a finalized permission model. Detailed roles and allowed actions belong in the engineering specifications.

## Product Promise

For a supported component with sufficient data, the product should make its health assessment understandable, connect that assessment to maintenance and logistics constraints, and help a human select an executable plan.

When evidence is insufficient, the product should make that limitation visible. A user must be able to distinguish measured records, model estimates, configured rules and simulation assumptions.

## Intended Experience

1. Open the fleet view and identify components or maintenance tasks requiring review.
2. Inspect a component's history, estimated remaining life, uncertainty and supporting sensor evidence.
3. Review the alert history and understand why attention is being requested.
4. Request a maintenance plan that accounts for mandatory deadlines, parts, crew and workshop resources.
5. Inspect bottlenecks and consider compatible work that could share a grounding.
6. Compare projected downtime under alternative plans or logistical assumptions.
7. Review and approve a plan; record the decision and its supporting evidence.
8. Record subsequent work and outcomes so the team can assess prediction and planning quality.

This is intended behaviour. Features become completed capabilities only after implementation and validation.

## Outcomes We Want

- **Connected information:** users can follow the relationship between a component, its observations, health assessments, maintenance tasks and required parts.
- **Understandable uncertainty:** users see the reliability and limitations of estimates before acting on them.
- **Useful alerts:** attention is directed to meaningful deterioration without unnecessary recommendation changes after minor fluctuations.
- **Executable plans:** proposed schedules respect explicit resource limits and mandatory maintenance requirements.
- **Visible bottlenecks:** users understand why work cannot proceed and which assumptions or resources would change the options.
- **Assessable consequences:** users can compare projected downtime and resource effects across alternatives.
- **Accountable decisions:** approved work retains a record of who decided, what evidence was available and which assumptions were used.

We will evaluate these outcomes through prediction tests, scheduling checks, workflow verification and reproducible simulation comparisons. Numerical targets and acceptance criteria belong in the evaluation and product specifications.

## Product Principles

### Evidence accompanies recommendations

Important outputs should identify their input records, model or policy version, and relevant assumptions. Model explanations describe influences on a prediction; they must not be presented as confirmed mechanical fault causes.

### Uncertainty is part of the decision

Life estimates should communicate uncertainty and data quality. A displayed range must have an evaluated meaning rather than an arbitrary confidence label.

### Constraints remain authoritative

Predictions inform maintenance proposals. They do not override mandatory maintenance requirements, resource limits or the need to recheck availability before committing a plan.

### Humans retain approval authority

The product assists technical review and planning. Approval and subsequent execution are explicit human workflow steps, separate from model predictions and simulated projections.

### Research claims remain testable

Use published methods as evidence and starting points. Compare implementations with suitable baselines, preserve unsuccessful results, and distinguish reproduced findings from unverified claims. Choose models and policies based on evaluation rather than architectural novelty.

### The workflow should remain coherent

Every principal feature should contribute to understanding component condition, selecting feasible work or assessing maintenance consequences. Interface detail should help users make those decisions.

## Initial Demonstration Boundary

The initial demonstration will use supported engine degradation data to evaluate component-level life prediction. Where public simulated engine histories are used, their simulated origin must be visible.

Fleet mappings, parts, technician capacity, maintenance duration and maintenance-effect assumptions may be synthetic demonstration inputs. Availability comparisons produced from those inputs are simulated projections, not measured operational improvements.

This demonstration does not establish whole-aircraft diagnostic coverage, actual military fleet readiness, airworthiness clearance or certified maintenance guidance. Expansion requires appropriate data, subsystem evidence and validation. Detailed inclusions, exclusions and extension gates belong in `scope.md`.

## Intended Contribution

Our contribution is an integrated and evaluated decision workflow connecting component prediction, uncertainty, maintenance constraints, parts and fleet downtime simulation.

Individual methods may already exist in research. We should demonstrate what our implementation adds through transparent comparisons and useful interaction, without claiming that integration alone proves superiority or guarantees a competition result.

## Relationship to Other Documents

- `scope.md` defines included capabilities, exclusions and release boundaries.
- `design.md` defines system architecture and module responsibilities.
- `rule.md` defines shared engineering conventions and invariants.
- `docs/product/feature_specifications.md` defines detailed behaviour.
- `docs/product/acceptance_criteria.md` defines completion evidence.
- `docs/research/` records sources, reproduction work, data protocols and evaluation methods.

This document is the canonical statement of product purpose. Revise it deliberately if the users, problem or intended outcomes change.

## Implemented decision journey — 2026-10-05

The local journey now includes immutable imports, quality withholding, registered RUL and uncertainty, demo-v2 review episodes, qualified crew/bay scheduling, exact-plan scenario replay, atomic approval/stock/resource bookings and auditable work. A separate engine-disjoint retraining benchmark is delivered without promotion or operational qualification. See `docs/team/release_acceptance.md` for executed evidence and unresolved gates. The mission remains decision support; customer acceptance is separate.
