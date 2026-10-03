import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, arrayOf, isJob, isPlan, type Job, type Plan } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { JobProgress } from "../jobs/JobProgress";

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

  return (
    <section>
      <div className="actions">
        <div>
          <h2>Maintenance planning</h2>
          <p className="muted">Constraint-checked proposals do not reserve stock until approval.</p>
        </div>
        <button onClick={() => propose.mutate()} disabled={propose.isPending}>
          Queue proposal calculation
        </button>
      </div>
      {(propose.error || approve.error) && (
        <div className="state error">{(propose.error || approve.error)?.message}</div>
      )}
      <div className="grid">
        <JobProgress kind="planning" />
        <AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}>
          {query.data?.map((plan) => (
            <article className="card span-12" key={plan.id}>
              <div className="actions">
                <h3>{plan.id}</h3>
                <StatusBadge status={plan.status} />
                <StatusBadge status={plan.solver_status} />
              </div>
              <p className="muted">Input snapshot {plan.input_version}</p>
              <table>
                <thead>
                  <tr><th>Task</th><th>Start slot</th><th>End slot</th></tr>
                </thead>
                <tbody>
                  {plan.assignments.map((assignment) => (
                    <tr key={assignment.task_id}>
                      <td>{assignment.task_id}</td>
                      <td>{assignment.start}</td>
                      <td>{assignment.end}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {plan.status === "proposed" && (
                <button onClick={() => approve.mutate(plan.id)} disabled={approve.isPending}>
                  Approve with current-state check
                </button>
              )}
              {plan.diagnostics.map((diagnostic) => <p key={diagnostic}>{diagnostic}</p>)}
            </article>
          ))}
        </AsyncState>
      </div>
    </section>
  );
}
