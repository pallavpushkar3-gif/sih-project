import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, arrayOf, isJob, isPlan, type Job, type Plan } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { JobProgress } from "../jobs/JobProgress";
import { ConstraintDetails } from "./ConstraintDetails";
import { PlanApproval } from "./PlanApproval";
import { PlanTimeline } from "./PlanTimeline";

export function PlanningPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["plans"],
    queryFn: () => api<Plan[]>("/plans", undefined, arrayOf(isPlan)),
  });
  const propose = useMutation({
    mutationFn: () => api<Job>("/jobs/planning", { method: "POST" }, isJob),
    onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const approve = useMutation({
    mutationFn: (id: string) =>
      api<Plan>(`/plans/${id}/approve`, { method: "POST" }, isPlan),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["plans"] });
      void client.invalidateQueries({ queryKey: ["inventory"] });
    },
  });
  const recentPlans = query.data?.slice(0, 3);

  return (
    <section>
      <div className="page-title">
        <div><span className="eyebrow">Planning</span><h1>Maintenance planning</h1><p>Build a schedule that satisfies deadlines, qualified capacity, available parts, and existing commitments.</p></div>
        <button onClick={() => propose.mutate()} disabled={propose.isPending}>
          {propose.isPending ? "Starting calculation…" : "Queue proposal calculation"}
        </button>
      </div>
      {(propose.error || approve.error) && (
        <div className="state error">{(propose.error || approve.error)?.message}</div>
      )}
      <div className="planner-hud">
        <div className="planner-node complete"><b>1</b><span><strong>Evidence</strong><small>Unavailable estimate withheld</small></span><i>✓</i></div>
        <div className="planner-connector" />
        <Link to="/inventory" className="planner-node blocked"><b>2</b><span><strong>Parts</strong><small>Filter stock needs attention</small></span><i>!</i></Link>
        <div className="planner-connector" />
        <div className="planner-node"><b>3</b><span><strong>Schedule</strong><small>Run constraint solver</small></span><i>○</i></div>
        <div className="planner-connector" />
        <div className="planner-node"><b>4</b><span><strong>Approval</strong><small>Reserve only after review</small></span><i>○</i></div>
      </div>
      <div className="grid">
        <JobProgress kind="planning" />
        <AsyncState loading={query.isLoading} error={query.error} empty={!recentPlans?.length}>
          {recentPlans?.map((plan, index) => (
            <article className="card span-12 plan-card" key={plan.id}>
              <div className="plan-heading"><div><span className="eyebrow">{index === 0 ? "Latest proposal" : "Recent proposal"}</span><h3>Fleet maintenance proposal</h3><p>Generated from the current task, capacity and inventory snapshot.</p></div><div><StatusBadge status={plan.status} /> <StatusBadge status={plan.solver_status} /></div></div>
              <ConstraintDetails plan={plan} />
              <div className="plan-summary"><div><span>Tasks scheduled</span><strong>{plan.assignments.length}</strong></div><div><span>Plan duration</span><strong>{Math.max(...plan.assignments.map((item) => item.end), 0) * 8} hours</strong></div><div><span>Constraint result</span><strong>{plan.solver_status === "optimal" ? "All checks passed" : plan.solver_status}</strong></div></div>
              <PlanTimeline plan={plan} />
              <table>
                <thead>
                  <tr><th>Maintenance action</th><th>Starts</th><th>Completes</th></tr>
                </thead>
                <tbody>
                  {plan.assignments.map((assignment) => (
                    <tr key={assignment.task_id}>
                      <td><strong>{assignment.task_id.includes("inspect") ? "Engine inspection" : "Filter replacement"}</strong><small className="table-subtitle">{assignment.task_id.includes("inspect") ? "Aircraft SYN-001" : "Aircraft SYN-002"}</small></td>
                      <td>Hour {assignment.start * 8}</td>
                      <td>Hour {assignment.end * 8}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <PlanApproval plan={plan} pending={approve.isPending} onApprove={(id) => approve.mutate(id)} />
              <details className="technical-details"><summary>Technical checks and record identity</summary><p>Record {plan.id} · Input {plan.input_version}</p>{plan.diagnostics.map((diagnostic) => <p key={diagnostic}>{diagnostic}</p>)}</details>
            </article>
          ))}
        </AsyncState>
        {(query.data?.length ?? 0) > 3 && <p className="history-note span-12">Showing the three most recent proposals · {query.data!.length - 3} older records remain in the audit history.</p>}
      </div>
    </section>
  );
}
