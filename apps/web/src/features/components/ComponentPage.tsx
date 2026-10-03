import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { api, isComponentDetail, type ComponentDetail } from "../../shared/api/client";
import { Chart } from "../../shared/charts/Chart";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

export function ComponentPage() {
  const { componentId = "" } = useParams();
  const query = useQuery({
    queryKey: ["component", componentId],
    queryFn: () => api<ComponentDetail>(`/components/${componentId}`, undefined, isComponentDetail),
    enabled: Boolean(componentId),
  });
  const data = query.data;
  const option = {
    backgroundColor: "transparent",
    grid: { left: 45, right: 18, top: 25, bottom: 40 },
    tooltip: { trigger: "axis" as const },
    textStyle: { color: "#697386", fontFamily: "Inter" },
    xAxis: { type: "category" as const, data: data?.observations.map((item) => item.cycle), name: "Operating cycle", axisLine: { lineStyle: { color: "#dfe5ee" } } },
    yAxis: { type: "value" as const, name: data?.observations[0]?.unit, splitLine: { lineStyle: { color: "#edf0f4" } } },
    series: [{ type: "line" as const, data: data?.observations.map((item) => item.value), smooth: true, symbolSize: 7, areaStyle: { color: "rgba(51,92,255,.08)" }, lineStyle: { color: "#335cff", width: 3 }, itemStyle: { color: "#335cff" } }],
  };
  return (
    <section>
      <AsyncState loading={query.isLoading} error={query.error}>
        {data && <>
          <Link className="back-link" to="/fleet">← Back to fleet</Link>
          <div className="record-heading">
            <div><span className="eyebrow">Aircraft component record</span><h1>{data.serial_number}</h1><p>{data.kind} · Aircraft {data.aircraft_id.replace("ac-syn-", "SYN-")}</p></div>
            <StatusBadge status={data.status} />
          </div>
          {data.assessment?.state !== "eligible" && <div className="decision-banner"><span>!</span><div><strong>Prediction is intentionally unavailable</strong><p>The validated model has not been approved for live use. The mandatory inspection remains active, so the safe next action is technical review—not a guessed life estimate.</p></div><Link className="button" to="/planning">Review work plan</Link></div>}
          <div className="metric-grid record-metrics">
            <article className="metric-card"><span>Current usage</span><strong>{data.current_cycle} cycles</strong><small>Latest observed cycle</small></article>
            <article className="metric-card warning"><span>Assessment</span><strong>Unavailable</strong><small>Evidence policy is protecting the decision</small></article>
            <article className="metric-card"><span>Open action</span><strong>Inspection</strong><small>Mandatory work stays active</small></article>
            <article className="metric-card neutral"><span>Data quality</span><strong>Review</strong><small>Generic sensor mapping</small></article>
          </div>
          <div className="grid detail-grid">
            <article className="card span-8"><div className="card-heading"><div><span className="eyebrow">Recorded evidence</span><h3>Sensor trend</h3></div><span className="soft-label">Last {data.observations.length} observations</span></div><Chart option={option} label="Sensor 2 values by operating cycle" /></article>
            <article className="card span-4"><span className="eyebrow">Decision context</span><h3>What this means</h3><div className="explanation-list"><div><span>Input record</span><strong>{data.assessment?.input_version}</strong></div><div><span>Model used</span><strong>{data.assessment?.model_version ?? "None"}</strong></div><div><span>Evaluation point</span><strong>Cycle {data.current_cycle}</strong></div></div><p className="footnote">The sensor name and unit remain generic because this fixture does not establish a physical mapping.</p></article>
          </div>
        </>}
      </AsyncState>
    </section>
  );
}
