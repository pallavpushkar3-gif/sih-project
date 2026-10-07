/** Fleet-level charts shared by the fleet manager's status page. */
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useHeatGrid, useTrend, type HeatGrid } from "./api";
import { availabilityLabel, pct, shortDate, stateLabel } from "./format";
import { OpsChart, baseAxes, tooltip } from "./OpsChart";
import { Card, Query, Segmented } from "./ui";

export function AvailabilityCard() {
  const trend = useTrend();
  const [range, setRange] = useState<"90" | "180">("90");
  return <Card title="Fleet availability" subtitle="Daily share of aircraft available, with the Monte Carlo forecast band (P10–P90) for the next 30 days"
    actions={<Segmented label="History range" value={range} onChange={setRange} options={[["90", "90 d"], ["180", "180 d"]] as const}/>}>
    <Query query={trend} rows={6}>{data => {
      const history = data.history.slice(-Number(range));
      const dates = [...history.map(p => p.date), ...data.forecast.map(p => p.date)];
      const pad = (values: (number | null)[], before: number, after: number) => [...Array(before).fill(null), ...values, ...Array(after).fill(null)];
      const last = history.at(-1);
      return <>
        <OpsChart label="Fleet availability history and 30-day forecast" height={290} deps={[data, range]} build={p => ({
          grid: { left: 44, right: 16, top: 16, bottom: 28 },
          tooltip: { ...tooltip(p), valueFormatter: (value: unknown) => typeof value === "number" ? pct(value, 1) : "—" },
          xAxis: { type: "category", data: dates, boundaryGap: false, ...baseAxes(p), axisLabel: { color: p.muted, fontSize: 11, formatter: (value: string) => shortDate(value) } },
          yAxis: { type: "value", min: (value: { min: number }) => Math.max(0, Math.floor(value.min * 10) / 10 - 0.05), max: 1, ...baseAxes(p), axisLabel: { color: p.muted, fontSize: 11, formatter: (value: number) => pct(value) } },
          series: [
            { name: "Band floor", type: "line", data: pad(data.forecast.map(f => f.p10), history.length, 0), stack: "band", lineStyle: { opacity: 0 }, symbol: "none", tooltip: { show: false } },
            { name: "P10–P90", type: "line", data: pad(data.forecast.map(f => f.p90 - f.p10), history.length, 0), stack: "band", lineStyle: { opacity: 0 }, symbol: "none", areaStyle: { color: p.accent2, opacity: 0.16 }, tooltip: { show: false } },
            { name: "Recorded", type: "line", data: pad(history.map(h => h.availability), 0, data.forecast.length), symbol: "none", smooth: 0.25, lineStyle: { width: 2.2, color: p.accent }, areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: `${p.accent}33` }, { offset: 1, color: `${p.accent}00` }] } },
              markLine: { symbol: "none", silent: true, label: { formatter: "Today", color: p.muted, fontSize: 10 }, lineStyle: { color: p.muted, type: "dashed" }, data: [{ xAxis: last?.date ?? "" }] } },
            { name: "Forecast P50", type: "line", data: pad([last?.availability ?? null, ...data.forecast.map(f => f.p50)], history.length - 1, 0), symbol: "none", smooth: 0.3, lineStyle: { width: 2.2, type: "dashed", color: p.accent2 } },
          ],
        })}/>
        <div className="o-legend"><span><i style={{ background: "var(--o-accent)" }}/>Recorded availability</span><span><i style={{ background: "var(--o-accent-2)" }}/>Forecast median</span><span><i style={{ background: "color-mix(in srgb, var(--o-accent-2) 25%, transparent)" }}/>P10–P90 across simulation runs</span></div>
      </>;
    }}</Query>
  </Card>;
}

export function HeatGridCard() {
  const grid = useHeatGrid();
  const navigate = useNavigate();
  const [sort, setSort] = useState<"risk" | "id">("risk");
  return <Card title="Fleet × system health" subtitle="Each cell is the worst component state in that system. Click a cell to open the aircraft’s digital twin."
    actions={<><div className="o-legend">{(["healthy", "watch", "degraded", "critical", "failed"] as const).map(state => <span key={state}><i className={`o-seg-${state}`}/>{stateLabel[state]}</span>)}</div><Segmented label="Sort aircraft" value={sort} onChange={setSort} options={[["risk", "By risk"], ["id", "By tail"]] as const}/></>}>
    <Query query={grid} rows={6}>{data => <HeatGridView data={data} sort={sort} onOpen={(aircraft, system) => navigate(`/aircraft/${aircraft}${system ? `?system=${system}` : ""}`)}/>}</Query>
  </Card>;
}

const rank = { healthy: 0, watch: 1, degraded: 2, critical: 3, failed: 4, under_maintenance: 3 } as const;
function HeatGridView({ data, sort, onOpen }: { data: HeatGrid; sort: "risk" | "id"; onOpen: (aircraft: string, system?: string) => void }) {
  const rows = useMemo(() => sort === "id" ? data.rows : [...data.rows].sort((a, b) => rank[b.state] - rank[a.state] || a.health_index - b.health_index), [data, sort]);
  return <div className="o-heat" style={{ gridTemplateColumns: `150px repeat(${rows.length}, minmax(16px, 1fr))` }}>
    <span className="o-heat-corner">Availability</span>
    {rows.map(row => <button type="button" key={`a-${row.aircraft}`} className={`o-heat-avail ${row.availability_state}`} title={`${row.aircraft}: ${availabilityLabel[row.availability_state]}`} onClick={() => onOpen(row.aircraft)} aria-label={`${row.aircraft} ${availabilityLabel[row.availability_state]}`}/>)}
    {data.systems.map((system, index) => <div className="o-heat-row" key={system.code} style={{ display: "contents" }}>
      <span className="o-heat-label">{system.name}</span>
      {rows.map(row => {
        const cell = row.cells[index];
        return <button type="button" key={`${row.aircraft}-${system.code}`} className={`o-heat-cell o-seg-${cell.state}`} onClick={() => onOpen(row.aircraft, system.code)}
          title={`${row.aircraft} · ${system.name}: ${stateLabel[cell.state]} · HI ${cell.health_index.toFixed(0)}${cell.driver ? ` · driver ${cell.driver}` : ""}`} aria-label={`${row.aircraft} ${system.name} ${stateLabel[cell.state]}`}/>;
      })}
    </div>)}
    <span/>
    {rows.map(row => <button type="button" key={`l-${row.aircraft}`} className="o-heat-tail" onClick={() => onOpen(row.aircraft)}>{row.aircraft.slice(3)}</button>)}
  </div>;
}
