# AeroCare — evaluator guide

**Team Null Paradox · SIH26249 · Aircraft Predictive Maintenance & Fleet Availability**

[Live application](https://sih-34-56-39-7.sslip.io/) ·
[Video demonstration](https://www.youtube.com/watch?v=HlYxblGJHEs) ·
[Capability and verification index](capability_evidence.md)

## Problem and approach

The [official problem](problem_statement.md) identifies fragmented aircraft-health,
technical-record, spares and maintenance-agency information as a cause of reactive maintenance
and low availability. AeroCare connects evidence review, maintenance cases, supply dependencies
and work history across four coordinated workspaces. Its contribution is a traceable path from
evidence to human-approved action and recorded completion.

The fleet workspace uses synthetic aircraft and logistics. A separate engine-research workflow
uses NASA C-MAPSS histories for remaining-life estimates, checked scheduling and simulated
comparisons. Benchmark engine results do not validate every fleet-board prediction.

## Five capabilities to inspect

| Capability | Review evidence |
|---|---|
| **Coordinated workspaces** | Engineering, supervision, logistics and fleet management share linked records. [Capability map](capability_evidence.md). |
| **Approval integrity** | Current-input checks, stock/resource reservations, stale approvals and auditable work transitions. [Acceptance ledger](../team/release_acceptance.md). |
| **Complete guided trial** | Supported history → assessment → schedule → receipt/replan → approval → execution → verification. [Trial contract and retained checks](customer_trial.md). Requires enabled isolated trial mode and installed artifacts. |
| **Availability-oriented planning** | CP-SAT minimises represented aircraft grounding under hard constraints; saved-plan replay compares against FIFO. [Study design and reproduction](../research/availability_study.md). |
| **Context-aware copilot** | Permitted record/service tools, source links and answer checks support maintenance questions. [Copilot operation and scoped verification](../operations/ai_copilot.md). |

## Short demonstration route

1. **Enter a workspace:** select maintenance engineer, supervisor, logistics or fleet manager,
   then sign in or create a demonstration account using the installation's access policy.
2. **Inspect a finding:** open an aircraft/component, review supporting evidence and follow its
   maintenance case. Explain what is recorded, estimated and synthetic.
3. **Follow the handoff:** inspect proposed work, required parts, shortages and work history in
   the relevant workspaces. Only submit an action when demonstrating an authorized synthetic case.
4. **Ask about the selected record:** use a question such as “What maintenance is open for this
   aircraft?” Inspect the returned evidence links. Optional generative inference requires the
   configured model service.
5. **Show the full trial on a prepared installation:** assess supported history, inspect the
   constrained plan, compare supply assumptions, record receipt and replan, then approve,
   complete and verify work. Trial mode is installation-dependent; the
   [retained walkthrough](../design/maintenance_walkthrough.md) is historical local evidence,
   not proof that this route is enabled on the current public deployment.

## Measured results and simulated outcomes

- **Engine benchmark:** the retained FD001 selected-model evaluation reports RMSE **11.710
  cycles** at 100 official truncated test-engine endpoints, using a 125-cycle capped target.
  Nominal 90% intervals covered 98/100 engines with mean width **58.231 cycles**. These are
  historical inspected benchmark results, not whole-aircraft accuracy. See the
  [evaluation protocol, results and limitations](../research/release_evaluation.md).
- **Planning and supply:** the availability study uses matched synthetic tasks, resources and
  supply assumptions. The guided single-aircraft parts example isolates parts waiting and can
  tie FIFO under identical supply. These comparisons establish neither a universal scheduling
  advantage nor observed real-fleet savings.
- **Functional verification:** linked tests and dated records describe their actual revision,
  installation and scope. This guide introduces no new test run or deployment acceptance claim.

Local reproduction starts with the [setup guide](../operations/local_setup.md). Trained artifacts
and bulk data require separate preparation. All maintenance decisions remain human-approved;
the demonstration does not provide airworthiness or dispatch clearance.
