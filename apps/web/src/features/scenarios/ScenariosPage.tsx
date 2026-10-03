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
      <div className="page-title"><div><span className="eyebrow">Capacity decisions</span><h1>What changes fleet availability?</h1><p>Compare the same maintenance demand under different hangar capacity. Results are projections, not operational readiness measures.</p></div><span className="projection-label">Simulated projections</span></div>
      {run.error && <div className="state error">{run.error.message}</div>}
      <div className="grid">
        <AsyncState loading={scenarios.isLoading} error={scenarios.error}>
          {scenarios.data?.map((scenario) => (
            <article className="card span-6" key={scenario.id}>
              <div className="scenario-visual"><span>✈</span><strong>{scenario.assumptions.maintenance_capacity === 1 ? "Current capacity" : "Additional bay"}</strong></div>
              <span className="eyebrow">Scenario {scenario.version}</span><h3>{scenario.name.replace("Synthetic ", "")}</h3>
              <p className="muted">Test how maintenance capacity affects waiting time and aircraft availability.</p>
              <div className="scenario-facts"><div><span>Aircraft</span><strong>{String(scenario.assumptions.aircraft_count)}</strong></div><div><span>Maintenance bays</span><strong>{String(scenario.assumptions.maintenance_capacity)}</strong></div><div><span>Horizon</span><strong>{String(scenario.assumptions.horizon_hours)} hr</strong></div></div>
              <button onClick={() => run.mutate(scenario.id)} disabled={run.isPending}>
                Queue deterministic reference
              </button>
            </article>
          ))}
        </AsyncState>
        <JobProgress kind="simulation" />
        <article className="card span-12">
          <div className="card-heading"><div><span className="eyebrow">Decision support</span><h3>Recorded comparisons</h3></div><span className="soft-label">Synthetic projection</span></div>
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
                    <td>{result.scenario_id === "scenario-baseline" ? "Current capacity" : "Additional bay"}</td>
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
