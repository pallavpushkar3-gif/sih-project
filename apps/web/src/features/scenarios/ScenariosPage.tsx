import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  api,
  arrayOf,
  isJob,
  isScenario,
  isSimulationRun,
  type Job,
  type Scenario,
  type SimulationRun,
} from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { JobProgress } from "../jobs/JobProgress";

export function ScenariosPage() {
  const client = useQueryClient();
  const scenarios = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => api<Scenario[]>("/scenarios", undefined, arrayOf(isScenario)),
  });
  const runs = useQuery({
    queryKey: ["scenario-runs"],
    queryFn: () =>
      api<SimulationRun[]>("/scenarios/runs/all", undefined, arrayOf(isSimulationRun)),
  });
  const run = useMutation({
    mutationFn: (id: string) =>
      api<Job>(`/jobs/simulation/${id}`, { method: "POST" }, isJob),
    onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] }),
  });

  return (
    <section>
      <h2>Availability scenarios</h2>
      <div className="banner">
        <strong>Simulated projections</strong>
        <div>
          Results use synthetic logistics and explicit maintenance-effect assumptions; they are not
          operational readiness measures.
        </div>
      </div>
      {run.error && <div className="state error">{run.error.message}</div>}
      <div className="grid">
        <AsyncState loading={scenarios.isLoading} error={scenarios.error}>
          {scenarios.data?.map((scenario) => (
            <article className="card span-6" key={scenario.id}>
              <h3>{scenario.name}</h3>
              <p className="muted">Version {scenario.version} · {scenario.provenance}</p>
              <pre>{JSON.stringify(scenario.assumptions, null, 2)}</pre>
              <button onClick={() => run.mutate(scenario.id)} disabled={run.isPending}>
                Queue deterministic reference
              </button>
            </article>
          ))}
        </AsyncState>
        <JobProgress kind="simulation" />
        <article className="card span-12">
          <h3>Recorded results</h3>
          <AsyncState loading={runs.isLoading} error={runs.error} empty={!runs.data?.length}>
            <table>
              <thead>
                <tr>
                  <th>Scenario</th><th>Availability</th><th>Queue wait</th><th>Seed</th><th>Label</th>
                </tr>
              </thead>
              <tbody>
                {runs.data?.map((result) => (
                  <tr key={result.id}>
                    <td>{result.scenario_id}</td>
                    <td>{(result.availability * 100).toFixed(1)}%</td>
                    <td>{String(result.metrics.queue_wait_hours ?? "—")}</td>
                    <td>{result.seed}</td>
                    <td>{String(result.metrics.label)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </AsyncState>
        </article>
      </div>
    </section>
  );
}
