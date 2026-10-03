import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

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
    textStyle: { color: "#b9c7d4" },
    xAxis: { type: "category" as const, data: data?.observations.map((item) => item.cycle), name: "cycle" },
    yAxis: { type: "value" as const, name: data?.observations[0]?.unit },
    series: [{ type: "line" as const, data: data?.observations.map((item) => item.value), smooth: true, lineStyle: { color: "#59d6c4" } }],
  };
  return (
    <section>
      <AsyncState loading={query.isLoading} error={query.error}>
        {data && <>
          <div className="actions"><h2>{data.serial_number}</h2><StatusBadge status={data.status} /></div>
          {data.assessment?.state !== "eligible" && <div className="banner"><strong>Assessment unavailable</strong><div>No evaluated model artifact is installed. Mandatory maintenance remains visible; no numerical estimate is substituted.</div></div>}
          <div className="grid">
            <article className="card span-8"><h3>Observed sensor trend</h3><Chart option={option} label="Sensor 2 values by operating cycle" /></article>
            <article className="card span-4"><h3>Evidence & provenance</h3><p>Input: {data.assessment?.input_version}</p><p>Model: {data.assessment?.model_version ?? "Not installed"}</p><p>Cutoff: cycle {data.current_cycle}</p><p className="muted">Sensor physical meaning is not asserted by the synthetic fixture.</p></article>
          </div>
        </>}
      </AsyncState>
    </section>
  );
}
