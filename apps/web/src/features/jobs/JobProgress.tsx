import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api, arrayOf, isJob, type Job } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

const activeStates = new Set(["queued", "running", "cancellation_requested"]);

const jobLabels = {
  planning: {
    title: "Maintenance plan",
    description: "Checks deadlines, qualified capacity and available parts.",
    success: "Plan ready for review",
  },
  simulation: {
    title: "Availability comparison",
    description: "Runs the selected capacity assumptions with a fixed reference seed.",
    success: "Projection saved",
  },
};

export function JobProgress({ kind }: { kind: "planning" | "simulation" }) {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api<Job[]>("/jobs", undefined, arrayOf(isJob)),
    refetchInterval: 2_000,
  });
  const cancel = useMutation({
    mutationFn: (id: string) =>
      api<Job>(`/jobs/${id}/cancellation`, { method: "POST" }, isJob),
    onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const jobs = query.data?.filter((job) => job.kind === kind).slice(0, 5) ?? [];
  const completedResults = jobs
    .filter((job) => job.state === "succeeded")
    .map((job) => JSON.stringify(job.result))
    .join("|");
  const copy = jobLabels[kind];

  useEffect(() => {
    if (!completedResults) return;
    void client.invalidateQueries({
      queryKey: [kind === "planning" ? "plans" : "scenario-runs"],
    });
  }, [client, completedResults, kind]);

  return (
    <article className="card span-12" aria-live="polite">
      <div className="card-heading">
        <div><span className="eyebrow">Background processing</span><h3>Calculation activity</h3></div>
        <span className="soft-label">Updates automatically</span>
      </div>
      <AsyncState loading={query.isLoading} error={query.error} empty={!jobs.length}>
        <table className="activity-table">
          <thead>
            <tr>
              <th>Calculation</th>
              <th>Status</th>
              <th>Outcome</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id} data-job-id={job.id}>
                <td><strong>{copy.title}</strong><small className="table-subtitle">{copy.description}</small></td>
                <td>
                  <StatusBadge status={job.state} />
                </td>
                <td>{job.state === "succeeded" ? copy.success : "Waiting for result"}</td>
                <td>
                  {activeStates.has(job.state) ? (
                    <button
                      className="secondary"
                      onClick={() => cancel.mutate(job.id)}
                      disabled={cancel.isPending}
                    >
                      Request cancellation
                    </button>
                  ) : (
                    <details className="inline-details"><summary>Details</summary><span>Attempt {job.attempt} · {job.id}</span></details>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </AsyncState>
      {cancel.error && <div className="state error">{cancel.error.message}</div>}
    </article>
  );
}
