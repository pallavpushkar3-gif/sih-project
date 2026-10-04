import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

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
  const [showAll, setShowAll] = useState(false);
  const query = useQuery({
    queryKey: ["jobs", kind],
    queryFn: () => api<Job[]>(`/jobs?kind=${kind}&limit=50`, undefined, arrayOf(isJob)),
    refetchInterval: (query) => query.state.data?.some((job) => activeStates.has(job.state)) ? 2_000 : 10_000,
  });
  const cancel = useMutation({
    mutationFn: (id: string) =>
      api<Job>(`/jobs/${id}/cancellation`, { method: "POST" }, isJob),
    onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }),
  });
  const allJobs = query.data?.filter((job) => job.kind === kind) ?? [];
  const jobs = showAll ? allJobs : allJobs.slice(0, 5);
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
    <article className="card span-12">
      <div className="card-heading">
        <div><h3>Background jobs</h3><p>Completed results are saved before they appear here.</p></div>
        <span className="soft-label">Updates automatically</span>
      </div>
      <AsyncState loading={query.isLoading} error={query.error} empty={!jobs.length} emptyMessage="No calculations recorded yet" onRetry={() => void query.refetch()}>
        <div className="table-scroll"><table className="activity-table">
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
                <td>{job.state === "succeeded" ? copy.success : job.state === "failed" ? `Calculation failed${typeof job.result?.error === "string" ? `: ${job.result.error.replaceAll("_", " ")}` : ""}` : job.state === "cancelled" ? "Cancelled; no accepted result" : job.state === "cancellation_requested" ? "Cancellation requested; awaiting confirmation" : "Waiting for result"}</td>
                <td>
                  {activeStates.has(job.state) ? (
                    <button
                      className="secondary"
                      onClick={() => cancel.mutate(job.id)}
                      disabled={cancel.isPending || job.state === "cancellation_requested"}
                    >
                      {job.state === "cancellation_requested" ? "Cancellation requested" : "Request cancellation"}
                    </button>
                  ) : (
                    <details className="inline-details"><summary>Details</summary><span>Attempt {job.attempt} · {job.id}</span></details>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table></div>
        {allJobs.length > 5 && <div className="table-footer"><span>{jobs.length} of {allJobs.length} jobs</span><button className="secondary" onClick={() => setShowAll(!showAll)}>{showAll ? "Show recent jobs" : "Show all jobs"}</button></div>}
      </AsyncState>
      {cancel.error && <div className="state error" role="alert">{cancel.error.message}</div>}
    </article>
  );
}
