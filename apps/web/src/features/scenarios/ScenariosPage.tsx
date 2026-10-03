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
import { ScenarioComparison } from "./ScenarioComparison";
import { ScenarioEditor } from "./ScenarioEditor";

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
  const baseline = runs.data?.find((result) => result.scenario_id === "scenario-baseline");
  const additional = runs.data?.find((result) => result.scenario_id !== "scenario-baseline");
  const delta = baseline && additional ? (additional.availability - baseline.availability) * 100 : null;

  return (
    <section>
      <div className="page-title"><div><span className="eyebrow">Scenarios</span><h1>What changes fleet availability?</h1><p>Compare the same aircraft, maintenance demand, and horizon while changing one capacity assumption.</p></div><span className="projection-label">Simulated projections</span></div>
      <div className="versus-board"><div><small>Current capacity</small><strong>{baseline ? `${(baseline.availability*100).toFixed(1)}%` : "Run"}</strong><span>Projected aircraft-time availability</span></div><b>vs</b><div><small>Additional maintenance bay</small><strong>{additional ? `${(additional.availability*100).toFixed(1)}%` : "Run"}</strong><span>{delta === null ? "Awaiting comparable run" : `${delta>=0?"+":""}${delta.toFixed(1)} points in this scenario`}</span></div></div>
      {run.error && <div className="state error">{run.error.message}</div>}
      <div className="grid">
        <AsyncState loading={scenarios.isLoading} error={scenarios.error}>
          {scenarios.data?.map((scenario) => <ScenarioEditor key={scenario.id} scenario={scenario} pending={run.isPending} onRun={(id)=>run.mutate(id)} />)}
        </AsyncState>
        <JobProgress kind="simulation" />
        <ScenarioComparison runs={runs.data} loading={runs.isLoading} error={runs.error} />
      </div>
    </section>
  );
}
