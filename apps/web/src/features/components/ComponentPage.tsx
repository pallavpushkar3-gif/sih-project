import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import aircraftImage from "../../assets/fleet-aircraft-game.png";
import { api, isComponentDetail, type ComponentDetail } from "../../shared/api/client";
import { Chart } from "../../shared/charts/Chart";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";
import { HealthAssessment } from "../health/HealthAssessment";
import { PredictionEvidenceCard } from "../health/PredictionEvidenceCard";
import { ComponentHistory } from "./ComponentHistory";

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
    textStyle: { color: "#8295ab", fontFamily: "Inter" },
    xAxis: { type: "category" as const, data: data?.observations.map((item) => item.cycle), name: "Operating cycle", axisLine: { lineStyle: { color: "#31445c" } }, axisLabel: { color: "#8295ab" } },
    yAxis: { type: "value" as const, name: data?.observations[0]?.unit, splitLine: { lineStyle: { color: "#1b2a3d" } }, axisLabel: { color: "#8295ab" } },
    series: [{ type: "line" as const, data: data?.observations.map((item) => item.value), smooth: true, symbolSize: 7, areaStyle: { color: "rgba(82,217,255,.09)" }, lineStyle: { color: "#59c9dc", width: 3 }, itemStyle: { color: "#59c9dc" } }],
  };
  return (
    <section>
      <AsyncState loading={query.isLoading} error={query.error}>
        {data && <>
          <Link className="back-link" to="/fleet">← Back to fleet</Link>
          <div className="record-heading">
            <div><span className="eyebrow">Aircraft component</span><h1>{data.serial_number}</h1><p>{data.kind} · Aircraft {data.aircraft_id.replace("ac-syn-", "SYN-")}</p></div>
            <StatusBadge status={data.status} />
          </div>
          {data.assessment?.state !== "eligible" && <div className="decision-banner"><span>!</span><div><strong>Prediction is intentionally unavailable</strong><p>The validated model has not been approved for live use. The mandatory inspection remains active, so the safe next action is technical review—not a guessed life estimate.</p></div><Link className="button" to="/planning">Review work plan</Link></div>}
          <article className="diagnostic-stage">
            <div className="diagnostic-copy"><span className="eyebrow">Aircraft systems</span><h2>Engine health evidence</h2><p>The selected engine has an active inspection task. No unsupported estimate is allowed to enter planning.</p><div className="diagnostic-steps"><span className="done"><b>1</b> Input checked</span><span className="current"><b>2</b> Engineer review</span><span><b>3</b> Plan work</span></div></div>
            <div className="diagnostic-aircraft"><img src={aircraftImage} alt="Aircraft with selected engine diagnostic context" /><i className="engine-target" /><span>Engine selected</span></div>
          </article>
          <div className="metric-grid record-metrics">
            <article className="metric-card"><span>Current usage</span><strong>{data.current_cycle} cycles</strong><small>Latest observed cycle</small></article>
            <HealthAssessment assessment={data.assessment} />
            <article className="metric-card"><span>Open action</span><strong>Inspection</strong><small>Mandatory work stays active</small></article>
            <article className="metric-card neutral"><span>Data quality</span><strong>Review</strong><small>Generic sensor mapping</small></article>
          </div>
          <div className="grid detail-grid">
            <article className="card span-8"><div className="card-heading"><div><span className="eyebrow">Recorded evidence</span><h3>Sensor trend</h3></div><span className="soft-label">Last {data.observations.length} observations</span></div><Chart option={option} label="Sensor 2 values by operating cycle" /><ComponentHistory observations={data.observations} /></article>
            <PredictionEvidenceCard assessment={data.assessment} cycle={data.current_cycle} />
          </div>
        </>}
      </AsyncState>
    </section>
  );
}
