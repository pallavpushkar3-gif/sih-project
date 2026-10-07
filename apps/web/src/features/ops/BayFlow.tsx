import { useMemo, useState, type CSSProperties } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Icon } from "../../shared/ui/Icon";
import { addDays, dayDiff } from "./AsOf";
import type { Schedule } from "./api";
import { longDate, shortDate } from "./format";

type Bar = { id: string; agency: string; lane: number | null; aircraft: string; label: string; kind: string; status: string; waiting_for: string | null; start: string; end: string; projected: boolean; component_id: string | null };
type Agency = { id: string; name: string; bays: number; lanes: number };
type Bay = { key: string; agency: string; lane: number; label: string; over: boolean; now: Bar | null; next: Bar | null; progress: number; x: number };

const W = 1200, TILE_W = 112, TILE_H = 80, GAP = 22, GROUP_GAP = 64;
const TILE_Y = 58, BUS_Y = 196, NODE_Y = 252, WAIT_Y = 372;
const COLS = 7, ROWS = 4;
const kindLabel: Record<string, string> = { predictive: "Planned replacement", unscheduled: "Unscheduled repair", scheduled: "Scheduled maintenance", inspection: "Inspection" };

/** Bays as panels, wired to the aircraft in them; queued aircraft hang off each agency's line.
 *  Everything is derived from the same schedule as the bay timeline below it. */
export function BayFlow({ data }: { data: Schedule }) {
  const navigate = useNavigate();
  const t0 = data.today;
  const bars = data.bars as Bar[];
  const agencies = data.agencies as Agency[];
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "busy" | "free">("all");

  const { bays, groups, waiting, occupancy } = useMemo(() => {
    const active = (bar: Bar) => dayDiff(bar.start, t0) >= 0 && dayDiff(t0, bar.end) >= 0;
    const lanes = agencies.reduce((sum, a) => sum + a.lanes, 0);
    const width = lanes * TILE_W + (lanes - agencies.length) * GAP + (agencies.length - 1) * GROUP_GAP;
    let x = (W - width) / 2;
    const bays: Bay[] = [];
    const groups: { agency: Agency; x0: number; x1: number }[] = [];
    for (const agency of agencies) {
      const x0 = x;
      for (let lane = 0; lane < agency.lanes; lane++) {
        const mine = bars.filter(bar => bar.agency === agency.id && bar.lane === lane);
        const now = mine.find(active) ?? null;
        const next = mine.filter(bar => dayDiff(t0, bar.start) > 0).sort((a, b) => a.start.localeCompare(b.start))[0] ?? null;
        const span = now ? Math.max(1, dayDiff(now.start, now.end) + 1) : 1;
        const progress = now ? Math.min(1, Math.max(0, (dayDiff(now.start, t0) + 0.5) / span)) : 0;
        bays.push({ key: `${agency.id}-${lane}`, agency: agency.id, lane, label: `${agency.id.replace("AG-", "")} ${lane + 1}`, over: lane >= agency.bays, now, next, progress, x });
        x += TILE_W + GAP;
      }
      x += GROUP_GAP - GAP;
      groups.push({ agency, x0, x1: x - GROUP_GAP });
    }
    const waiting = bars.filter(bar => bar.lane === null && dayDiff(t0, bar.end) >= 0);
    const occupancy = Array.from({ length: 14 }, (_, i) => {
      const day = addDays(t0, i);
      return bars.filter(bar => bar.lane !== null && dayDiff(bar.start, day) >= 0 && dayDiff(day, bar.end) >= 0).length;
    });
    return { bays, groups, waiting, occupancy };
  }, [agencies, bars, t0]);

  const busy = bays.filter(bay => bay.now);
  const capacity = agencies.reduce((sum, a) => sum + a.bays, 0);
  const pick = bays.find(bay => bay.key === selected) ?? null;
  const shown = bays.filter(bay => filter === "all" || (filter === "busy" ? bay.now : !bay.now));
  const tone = (bar: Bar | null) => !bar ? "free" : bar.kind === "unscheduled" ? "crit" : bar.kind === "predictive" ? "plan" : "sched";

  return <div className="o-bayflow">
    <div className="o-bayflow-stats">
      <Stat label="Bays in work" value={busy.length} trend={occupancy} tone="plan" detail={`of ${capacity} staffed`}/>
      <Stat label="Waiting for bay or part" value={waiting.length} tone={waiting.length ? "warn" : "ok"} detail={waiting.length ? "queued aircraft" : "no queue"}/>
      <Stat label="Free bays now" value={Math.max(0, capacity - busy.filter(b => !b.over).length)} tone="ok" detail="ready to take work"/>
      <Stat label="Unscheduled in bays" value={busy.filter(b => b.now?.kind === "unscheduled").length} tone="crit" detail="failure repairs"/>
    </div>
    <div className="o-bayflow-body">
      <aside className="o-bayflow-list" aria-label="Bay operations">
        <header><strong>Bay operations</strong><div className="o-bayflow-filter">{([["all", "All"], ["busy", "In work"], ["free", "Free"]] as const).map(([value, text]) => <button type="button" key={value} className={filter === value ? "on" : ""} onClick={() => setFilter(value)}>{value !== "all" && <i className={value === "busy" ? "t-busy" : "t-free"}/>}{text}</button>)}</div></header>
        <ul>{shown.map(bay => <li key={bay.key}>
          <button type="button" className={`o-bay-row${selected === bay.key ? " on" : ""}`} onClick={() => setSelected(selected === bay.key ? null : bay.key)}>
            <span className={`o-bay-chip t-${tone(bay.now)}`}><Icon name="wrench" size={13}/></span>
            <span className="o-bay-name"><b>{bay.label}</b><small><i className={bay.now ? "t-busy" : "t-free"}/>{bay.now ? `${bay.now.aircraft} · ${bay.now.kind === "predictive" ? "planned" : bay.now.kind}` : bay.over ? "Overflow lane" : "Free"}</small></span>
            {bay.now && <span className="o-bay-progress"><small>Repair progress <b>{Math.round(bay.progress * 100)}%</b></small><span><i className={`t-${tone(bay.now)}`} style={{ width: `${bay.progress * 100}%` }}/></span></span>}
          </button>
        </li>)}</ul>
      </aside>
      <div className="o-bayflow-canvas">
        <svg viewBox={`0 0 ${W} 440`} role="group" aria-label="Maintenance bays wired to the aircraft they hold">
          <defs>
            <linearGradient id="bf-plan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--o-accent-2)" stopOpacity=".95"/><stop offset="1" stopColor="var(--o-accent-2)" stopOpacity=".75"/></linearGradient>
            <linearGradient id="bf-ok" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--o-accent)" stopOpacity=".9"/><stop offset="1" stopColor="var(--o-accent)" stopOpacity=".7"/></linearGradient>
            <filter id="bf-shadow" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="6" stdDeviation="6" floodColor="#12201a" floodOpacity=".14"/></filter>
          </defs>
          {groups.map(({ agency, x0, x1 }) => <g key={agency.id}>
            <text x={x0} y={30} className="o-bf-agency">{agency.name}</text>
            <text x={x1} y={30} textAnchor="end" className="o-bf-meta">{agency.bays} bays</text>
            <path d={`M${x0 - 14} ${BUS_Y} H${x1 + 14}`} className="o-bf-bus"/>
            <rect x={x0 - 20} y={BUS_Y - 6} width={12} height={12} rx={3} className="o-bf-hub"/>
            {waiting.filter(bar => bar.agency === agency.id).map((bar, index, list) => {
              const nx = x0 + ((x1 - x0) / Math.max(list.length, 1)) * (index + 0.5);
              const jx = Math.min(x1 + 10, Math.max(x0 - 10, nx));
              return <g key={bar.id} className="o-bf-wait">
                <path d={`M${jx} ${BUS_Y} V${WAIT_Y - 40} Q${jx} ${WAIT_Y - 26} ${nx} ${WAIT_Y - 22} V${WAIT_Y - 18}`} className="o-bf-line t-warn"/>
                <rect x={jx - 5} y={BUS_Y + 30} width={10} height={10} rx={2} className="o-bf-junction t-warn"/>
                <Node x={nx} y={WAIT_Y} tail={bar.aircraft} sub={`waiting · ${bar.waiting_for ?? "bay"}`} tone="warn" onClick={() => bar.component_id ? navigate(`/health/${bar.component_id}`) : navigate(`/aircraft/${bar.aircraft}`)}/>
              </g>;
            })}
          </g>)}
          {groups.slice(1).map((g, i) => <path key={g.agency.id} d={`M${groups[i].x1 + 14} ${BUS_Y} H${g.x0 - 20}`} className="o-bf-bus dim"/>)}
          {bays.map(bay => {
            const cx = bay.x + TILE_W / 2;
            const t = tone(bay.now);
            const filled = Math.round(bay.progress * COLS * ROWS);
            return <g key={bay.key} className={`o-bf-bay t-${t}${selected === bay.key ? " on" : ""}`} tabIndex={0} role="button" aria-pressed={selected === bay.key}
              aria-label={`${bay.label}: ${bay.now ? `${bay.now.aircraft}, ${kindLabel[bay.now.kind] ?? bay.now.kind}, ${Math.round(bay.progress * 100)}% through` : "free"}`}
              onClick={() => setSelected(selected === bay.key ? null : bay.key)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); setSelected(selected === bay.key ? null : bay.key); } }}>
              {bay.now && <>
                <path d={`M${cx} ${TILE_Y + TILE_H + 10} V${NODE_Y - 18}`} className={`o-bf-line t-${t}`}/>
                <rect x={cx - 5} y={BUS_Y - 5} width={10} height={10} rx={2} className={`o-bf-junction t-${t}`}/>
              </>}
              {!bay.now && <path d={`M${cx} ${TILE_Y + TILE_H + 10} V${BUS_Y}`} className="o-bf-line t-free"/>}
              {/* Panel: a slab with a cell grid; filled cells show how far the job has run. */}
              <rect x={bay.x + 4} y={TILE_Y + 10} width={TILE_W} height={TILE_H} rx={8} className="o-bf-slab-side"/>
              <rect x={bay.x} y={TILE_Y} width={TILE_W} height={TILE_H} rx={8} className="o-bf-slab" filter="url(#bf-shadow)"/>
              {Array.from({ length: COLS * ROWS }, (_, i) => {
                const col = i % COLS, row = Math.floor(i / COLS);
                const cw = (TILE_W - 16 - (COLS - 1) * 3) / COLS, ch = (TILE_H - 16 - (ROWS - 1) * 3) / ROWS;
                return <rect key={i} x={bay.x + 8 + col * (cw + 3)} y={TILE_Y + 8 + row * (ch + 3)} width={cw} height={ch} rx={2.5}
                  className={`o-bf-cell${bay.now && i < filled ? " lit" : ""}`}/>;
              })}
              <text x={bay.x} y={TILE_Y + TILE_H + 26} className="o-bf-bay-label">{bay.label}</text>
              {bay.now && <text x={bay.x + TILE_W} y={TILE_Y + TILE_H + 26} textAnchor="end" className="o-bf-pct">{Math.round(bay.progress * 100)}%</text>}
              {(bay.over || bay.now?.kind === "unscheduled") && <g transform={`translate(${bay.x + TILE_W - 6} ${TILE_Y - 6})`} className="o-bf-alert">
                <circle r={11}/><path d="M0 -5 L5 4 H-5 Z"/>
              </g>}
              {bay.now && <Node x={cx} y={NODE_Y} tail={bay.now.aircraft} sub={shortLabel(bay.now)} tone={t} onClick={() => navigate(`/aircraft/${bay.now!.aircraft}`)}/>}
              {!bay.now && bay.next && <text x={cx} y={BUS_Y + 22} textAnchor="middle" className="o-bf-meta">next {bay.next.aircraft} · {shortDate(bay.next.start)}</text>}
            </g>;
          })}
          <text x={W - 10} y={430} textAnchor="end" className="o-bf-meta">T0 {longDate(t0)} · progress = elapsed share of the planned bay time</text>
        </svg>
        {pick && <div className="o-bayflow-card o-glass-pop" role="dialog" aria-label={`${pick.label} details`} style={{ "--x": `${((pick.x + TILE_W / 2) / W) * 100}%` } as CSSProperties}>
          <header><span className={`o-bay-chip t-${tone(pick.now)}`}><Icon name="wrench" size={13}/></span><div><strong>{pick.label}</strong><small>{agencies.find(a => a.id === pick.agency)?.name}{pick.over ? " · overflow lane" : ""}</small></div>
            <button type="button" className="o-icon-btn" aria-label="Close" onClick={() => setSelected(null)}><Icon name="close" size={14}/></button></header>
          {pick.now ? <>
            <p className="o-bf-card-job"><b>{pick.now.aircraft}</b> · {pick.now.label}</p>
            <small className="o-muted">{kindLabel[pick.now.kind] ?? pick.now.kind} · {shortDate(pick.now.start)} → {shortDate(pick.now.end)}{pick.now.projected ? " (projected)" : ""}</small>
            <div className="o-bay-progress wide"><small>Repair progress <b>{Math.round(pick.progress * 100)}%</b></small><span><i className={`t-${tone(pick.now)}`} style={{ width: `${pick.progress * 100}%` }}/></span></div>
            <div className="o-bf-card-actions"><Link className="o-btn sm ghost" to={`/aircraft/${pick.now.aircraft}`}>Open aircraft</Link>{pick.now.component_id && <Link className="o-btn sm ghost" to={`/health/${pick.now.component_id}`}>Component</Link>}</div>
          </> : <p className="o-muted o-small">Free now.{pick.next ? ` Next: ${pick.next.aircraft} from ${longDate(pick.next.start)}.` : " Nothing booked in the next 14 days."}</p>}
        </div>}
        <div className="o-legend o-bayflow-legend"><span><i style={{ background: "var(--o-accent-2)" }}/>Planned from advisory</span><span><i style={{ background: "var(--o-critical)" }}/>Unscheduled repair</span><span><i style={{ background: "var(--o-text-3)" }}/>Scheduled / inspection</span><span><i style={{ background: "var(--o-watch)" }}/>Waiting</span><span><i style={{ background: "var(--o-accent)" }}/>Free bay</span></div>
      </div>
    </div>
  </div>;
}

function shortLabel(bar: Bar) {
  const text = bar.kind === "predictive" ? bar.label.replace("Planned replacement: ", "") : bar.label;
  return text.length > 18 ? `${text.slice(0, 17)}…` : text;
}

function Node({ x, y, tail, sub, tone, onClick }: { x: number; y: number; tail: string; sub: string; tone: string; onClick: () => void }) {
  return <g className={`o-bf-node t-${tone}`} transform={`translate(${x - 62} ${y - 18})`} onClick={event => { event.stopPropagation(); onClick(); }} role="link" tabIndex={0} aria-label={`${tail}: ${sub}`}
    onKeyDown={event => { if (event.key === "Enter") { event.stopPropagation(); onClick(); } }}>
    <rect width={124} height={44} rx={12} filter="url(#bf-shadow)"/>
    <circle cx={18} cy={22} r={10} className="o-bf-node-icon"/>
    <path d="M14 22 h8 M18 18 l4 4 -4 4" className="o-bf-node-glyph"/>
    <text x={34} y={19} className="o-bf-node-tail">{tail}</text>
    <text x={34} y={33} className="o-bf-node-sub">{sub}</text>
  </g>;
}

function Stat({ label, value, detail, tone, trend }: { label: string; value: number; detail: string; tone: string; trend?: number[] }) {
  const max = Math.max(1, ...(trend ?? [1]));
  return <div className="o-bf-stat">
    <div><strong>{value}</strong><span className={`o-bf-dot t-${tone}`}/></div>
    <small>{label}<em>{detail}</em></small>
    {trend && <svg className="o-bf-spark" viewBox={`0 0 ${trend.length * 6} 30`} aria-label={`Bays in use over the next ${trend.length} days`} role="img">
      {trend.map((v, i) => <rect key={i} x={i * 6} y={30 - (v / max) * 28} width={3} height={(v / max) * 28 || 1} rx={1} className={i === 0 ? "now" : ""}/>)}
    </svg>}
  </div>;
}
