import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { api, arrayOf, isJob, type Job } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

const activeStates = new Set(["queued", "running", "cancellation_requested"]);

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

  useEffect(() => {
    if (!completedResults) return;
    void client.invalidateQueries({
      queryKey: [kind === "planning" ? "plans" : "scenario-runs"],
    });
  }, [client, completedResults, kind]);

  return (
    <article className="card span-12" aria-live="polite">
      <h3>Calculation jobs</h3>
      <AsyncState loading={query.isLoading} error={query.error} empty={!jobs.length}>
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>State</th>
              <th>Attempt</th>
              <th>Result</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.id}</td>
                <td>
                  <StatusBadge status={job.state} />
                </td>
                <td>{job.attempt}</td>
                <td>{job.result ? Object.values(job.result).join(", ") : "—"}</td>
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
                    "—"
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
