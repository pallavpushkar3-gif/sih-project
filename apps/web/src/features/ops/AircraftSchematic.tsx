import type { HealthState, TwinSystem } from "./api";
import { stateLabel } from "./format";

/** Generic twin-engine transport, top-view wireframe. No real aircraft geometry is implied.
 *  Each system has one or more nodes; degraded or critical systems pulse to draw the eye. */
const nodes: Record<string, { label: string; points: [number, number][]; tag: [number, number] }> = {
  AVN: { label: "AVN", points: [[400, 70]], tag: [420, 66] },
  ELEC: { label: "ELEC", points: [[400, 150]], tag: [420, 146] },
  LG: { label: "LG", points: [[400, 120], [345, 262], [455, 262]], tag: [475, 262] },
  PROP: { label: "PROP", points: [[234, 226], [566, 226]], tag: [590, 222] },
  FUEL: { label: "FUEL", points: [[230, 262], [570, 262]], tag: [590, 276] },
  HYD: { label: "HYD", points: [[400, 305]], tag: [420, 301] },
  ECS: { label: "ECS", points: [[400, 375]], tag: [420, 371] },
};
const tone = (state: HealthState) => state === "healthy" ? "ok" : state === "watch" || state === "degraded" ? "warn" : state === "under_maintenance" ? "maint" : "crit";

export function AircraftSchematic({ systems, selected, onSelect, tail }: { systems: TwinSystem[]; selected: string | null; onSelect: (code: string) => void; tail: string }) {
  const byCode = Object.fromEntries(systems.map(system => [system.code, system]));
  return <svg className="o-wire" viewBox="0 0 800 520" role="group" aria-label={`Wireframe of ${tail} with system health nodes`}>
    <g className="o-wire-frame">
      <path d="M400 24 C426 36 440 76 442 128 L444 420 C444 452 426 482 400 496 C374 482 356 452 356 420 L358 128 C360 76 374 36 400 24 Z"/>
      <path d="M360 205 L66 287 L66 309 L362 274"/><path d="M440 205 L734 287 L734 309 L438 274"/>
      <path d="M394 408 L276 452 L276 468 L394 448"/><path d="M406 408 L524 452 L524 468 L406 448"/>
      <rect x="214" y="186" width="40" height="82" rx="10"/><rect x="546" y="186" width="40" height="82" rx="10"/>
      <path d="M400 432 L400 500" strokeDasharray="4 4"/>
      <path d="M372 112 L428 112" className="o-wire-thin"/><path d="M365 168 L435 168" className="o-wire-thin"/>
    </g>
    {Object.entries(nodes).map(([code, node]) => {
      const system = byCode[code];
      const state: HealthState = system?.state ?? "healthy";
      const t = tone(state);
      const active = selected === code;
      return <g key={code} className={`o-node n-${t}${active ? " active" : ""}`} tabIndex={0} role="button" aria-pressed={active}
        aria-label={`${system?.name ?? code}: ${stateLabel[state]}, health index ${system?.health_index.toFixed(0) ?? "—"}`}
        onClick={() => onSelect(code)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelect(code); } }}>
        {node.points.map(([x, y], index) => <g key={index} transform={`translate(${x} ${y})`}>
          {t !== "ok" && <circle r="13" className="o-node-pulse"/>}
          <circle r={t === "ok" ? 5 : 7} className="o-node-dot"/>
        </g>)}
        <text x={node.tag[0]} y={node.tag[1] + 4} className="o-node-tag">{node.label} {system ? system.health_index.toFixed(0) : "—"}</text>
      </g>;
    })}
  </svg>;
}
