import { Component, Suspense, lazy, useRef, useState, type ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Link } from "react-router-dom";
import type { AircraftDetail } from "./api";
import { architectureColor, architectureComponents, structureLabels } from "./componentArchitecture";
import { num, pct, rulText, shortDate, stateLabel } from "./format";
import { Icon } from "../../shared/ui/Icon";
import "./aircraft-blueprint.css";

const Studio = lazy(() => import("./BlueprintStudio").then(module => ({ default: module.BlueprintStudio })));
class BlueprintBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() { return this.state.failed ? <p className="bp-renderer-fallback" role="status">3D view unavailable. Use the drawing and component records to continue.</p> : this.props.children; }
}
function Drawing() {
  return <g className="bp-airframe" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round">
    {/* Authored orthographic silhouette of the existing visual fighter, not a scan of the reference. */}
    <path d="M94 275 L132 272 C180 258 230 254 270 252 L360 239 C428 237 535 243 633 250 L670 253 L670 297 L633 300 C535 307 428 313 360 311 L270 298 C230 296 180 292 132 278 Z"/>
    <path d="M341 239 L467 203 L565 89 L582 91 L603 246 M341 311 L467 347 L565 461 L582 459 L603 304"/>
    <path d="M373 241 L455 227 L554 118 M373 309 L455 323 L554 432"/>
    <path d="M458 247 L574 221 L583 207 L592 246 M458 303 L574 329 L583 343 L592 304"/>
    <path d="M283 251 C307 248 341 246 356 246 L357 258 L292 262 M283 299 C307 302 341 304 356 304 L357 292 L292 288"/>
    <path d="M234 269 C222 256 266 251 292 254 C320 256 322 266 315 271 C282 280 250 280 234 269 Z"/>
    <path d="M254 255 L254 275 M288 254 L288 275 M142 274 L685 274" strokeDasharray="5 5" opacity=".5"/>
    <path d="M502 267 L588 270 L621 274 L588 278 L502 282 Z M633 250 L633 300 M645 251 L645 299 M655 252 L655 298 M660 253 L660 297"/>
    <path d="M515 160 L557 202 L548 217 L493 192 Z M515 390 L557 348 L548 333 L493 358 Z"/>
    <path d="M402 240 L402 310 M448 241 L448 309 M475 244 L475 306 M313 253 L313 298" opacity=".7"/>
    <g transform="translate(778 122)"><path d="M0 -67 L8 -22 C31 -13 32 10 0 15 C-32 10 -31 -13 -8 -22 Z M-90 2 L-16 -2 M16 -2 L90 2 M-23 14 L-23 40 L-16 40 L-16 15 M23 14 L23 40 L16 40 L16 15 M0 14 L0 39"/><ellipse cy="-7" rx="13" ry="14"/><path d="M-35 3 L-29 12 L-21 4 M35 3 L29 12 L21 4"/></g>
    <g transform="translate(112 524) scale(.87)"><path d="M0 0 L52 -8 L155 -18 L288 -22 L427 -15 L574 -13 L604 -9 L604 18 L512 22 L302 14 L151 11 L48 5 Z M132 -17 C143 -52 207 -49 239 -22 M152 -20 C162 -41 207 -40 218 -22 M418 -15 L492 -99 L521 -90 L538 -14 M492 -99 L499 -16 M158 11 L169 54 M412 18 L424 54"/><circle cx="170" cy="58" r="11"/><circle cx="425" cy="58" r="15"/><path d="M245 12 L397 10 L439 0 M574 -13 L574 20 M586 -12 L586 20"/></g>
    <g className="bp-dimension" strokeWidth=".7" opacity=".4"><path d="M94 470 L670 470 M94 463 L94 477 M670 463 L670 477 M58 89 L58 461 M51 89 L65 89 M51 461 L65 461" strokeDasharray="3 3"/></g>
  </g>;
}
export function AircraftBlueprint({ data }: { data: AircraftDetail }) {
  const components = architectureComponents(data);
  const [view, setView] = useState<"drawing" | "spatial">("drawing");
  const [findingsOnly, setFindingsOnly] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [mode, setMode] = useState<"assembled" | "exploded" | "wireframe">("assembled");
  const [reset, setReset] = useState(0);
  const lastSelection = useRef<string | null>(null);
  const selected = components.find(item => item.id === selectedId);
  const findings = components.filter(item => item.attention).length;
  const visible = components.filter(item => !findingsOnly || item.attention);
  const select = (id: string) => { lastSelection.current = id; setSelectedId(id); setMode("assembled"); setReset(0); };
  return <section className="aircraft-blueprint" aria-label="Aircraft component blueprint" id="aircraft-blueprint">
    <header className="bp-header"><div><span className="bp-eyebrow">AIRFRAME / COMPONENT INSPECTION</span><h2>Aircraft blueprint</h2><p>{String(data.aircraft.id)} · {shortDate(data.as_of)} · Select a component to inspect its structure and condition.</p></div><span className={`bp-finding-count${!components.length ? " is-unavailable" : findings ? " has-findings" : ""}`}><Icon name={findings ? "warning" : "aircraft"} size={16}/>{!components.length ? "Component records unavailable" : findings ? `${findings} condition ${findings === 1 ? "finding" : "findings"}` : "No condition findings"}</span></header>
    <div className="bp-workspace">
      <div className="bp-drawing-panel">
        <div className="bp-toolbar"><div role="group" aria-label="Blueprint view">{(["drawing", "spatial"] as const).map(item => <button key={item} type="button" aria-pressed={view === item} onClick={() => setView(item)}>{item === "drawing" ? "Blueprint" : "3D architecture"}</button>)}</div><button type="button" className="bp-filter" aria-pressed={findingsOnly} onClick={() => setFindingsOnly(value => !value)}>Findings only</button></div>
        <div className="bp-drawing-surface">
          {view === "drawing" ? <svg viewBox="0 0 900 600" role="group" aria-label={`Illustrative fighter blueprint for ${String(data.aircraft.id)}`}>
            <Drawing/><g className="bp-view-labels" fill="currentColor"><text x="85" y="54">01 / PLAN VIEW</text><text x="718" y="54">02 / FRONT</text><text x="85" y="498">03 / SIDE</text><text x="718" y="575">NOT TO SCALE</text></g>
            {visible.filter(item => item.layout).map(item => {
              const index = components.indexOf(item), [x, , z] = item.layout!.position;
              return <g key={item.id} transform={`translate(${400 - z * 56} ${275 + x * 59})`} className={`bp-hotspot${item.attention ? " is-alert" : ""}`} data-component-id={item.id} data-attention={item.attention} style={{ color: architectureColor(item) }} role="button" tabIndex={0} aria-label={`Inspect ${item.name}: ${stateLabel[item.state]}`} onClick={() => select(item.id)} onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); select(item.id); } }}>
                <title>{item.name} · {stateLabel[item.state]} · HI {num(item.hi)}</title><circle className="bp-hotspot-halo" r="19"/><circle className="bp-hotspot-core" r="11"/><text textAnchor="middle" dominantBaseline="central">{index + 1}</text>
              </g>;
            })}
          </svg> : <div className="bp-spatial-scene" aria-label="Rotatable 3D aircraft architecture"><BlueprintBoundary><Suspense fallback={<p className="bp-renderer-fallback" role="status">Preparing architecture…</p>}><Studio components={visible} onSelect={select} reset={String(reset)}/></Suspense></BlueprintBoundary></div>}
        </div>
        <footer className="bp-drawing-footer"><div><span><i className="bp-red"/>Condition finding</span><span><i className="bp-blue"/>Maintenance</span><span><i className="bp-green"/>Healthy</span></div><span>{view === "drawing" ? "Click a numbered part" : "Drag to orbit · Click a marker"}</span></footer>
      </div>
      <aside className="bp-component-register" aria-label="Blueprint component register"><header><h3>Component register</h3><span>{visible.length} / {components.length}</span></header><div className="bp-register-list">
        {visible.map(item => <button type="button" key={item.id} onClick={() => select(item.id)} className={`bp-register-item${item.attention ? " has-finding" : ""}`} data-component-id={item.id} data-attention={item.attention}>
          <span className="bp-number" style={{ color: architectureColor(item) }}>{String(components.indexOf(item) + 1).padStart(2, "0")}</span><span><strong>{item.name}</strong><small>{item.system} · {stateLabel[item.state]}</small></span><Icon name="chevron" size={14}/>
        </button>)}
        {!visible.length && <p className="bp-empty">{components.length && findingsOnly ? "No condition findings in this snapshot. Turn off Findings only to inspect all components." : "No component records available for this aircraft."}</p>}
      </div></aside>
    </div>
    <p className="bp-provenance">Illustrative architecture · Synthetic component records. Locations and internal structures are conceptual, not verified installation or fault-location data.</p>
    <Dialog.Root open={Boolean(selected)} onOpenChange={open => { if (!open) setSelectedId(null); }}><Dialog.Portal><Dialog.Overlay className="o-overlay bp-inspection-overlay"/><Dialog.Content className="bp-inspection-dialog" aria-describedby="bp-inspection-context" onCloseAutoFocus={event => { event.preventDefault(); if (lastSelection.current) document.querySelector<HTMLButtonElement>(`.bp-register-item[data-component-id="${CSS.escape(lastSelection.current)}"]`)?.focus(); }}>
      {selected && <><header className="bp-inspection-header"><div><span className="bp-eyebrow">COMPONENT / 3D INSPECTION</span><Dialog.Title>{selected.name}</Dialog.Title><Dialog.Description id="bp-inspection-context">{String(data.aircraft.id)} · {selected.system} · {shortDate(data.as_of)}</Dialog.Description></div><Dialog.Close asChild><button type="button" aria-label="Close component inspection"><Icon name="close" size={20}/></button></Dialog.Close></header>
        <div className="bp-inspection-body"><div className="bp-part-stage"><div className="bp-part-toolbar" role="group" aria-label="Component structure view">{(["assembled", "exploded", "wireframe"] as const).map(item => <button type="button" key={item} aria-pressed={mode === item} onClick={() => setMode(item)}>{item[0].toUpperCase() + item.slice(1)}</button>)}<button type="button" aria-label="Reset component camera" onClick={() => setReset(value => value + 1)}><Icon name="history" size={15}/></button></div>
          <div className="bp-part-canvas" aria-label={`3D structure of ${selected.name}`}>{selected.layout ? <BlueprintBoundary key={selected.id}><Suspense fallback={<p role="status">Preparing component structure…</p>}><Studio components={components} selected={selected} mode={mode} reset={String(reset)}/></Suspense></BlueprintBoundary> : <p className="bp-renderer-fallback">A structure model is not available for this component type. Its condition records remain available.</p>}</div>
          <div className="bp-part-legend">{selected.layout && structureLabels[selected.layout.kind].map(label => <span key={label}>{label}</span>)}</div><p className="bp-part-note">Illustrative section model · Drag to rotate. Red marks the component’s recorded condition, not a diagnosed internal defect.</p>
        </div><aside className="bp-part-evidence"><span className={`bp-condition ${selected.attention ? "has-finding" : selected.state === "under_maintenance" ? "state-maintenance" : ""}`}>{stateLabel[selected.state]}</span><dl><div><dt>Health index</dt><dd>{num(selected.hi)}<small>/100</small></dd></div><div><dt>Remaining life</dt><dd>{rulText(selected.rul)}</dd></div><div><dt>14-day risk</dt><dd>{pct(selected.risk14)}</dd></div><div><dt>Serial</dt><dd className="bp-serial">{selected.serial || "Unavailable"}</dd></div></dl>
          <h3>Recorded findings</h3>{selected.openAdvisories.length ? selected.openAdvisories.map(advisory => <p key={advisory.id}>{advisory.id} · {advisory.status.replaceAll("_", " ")}</p>) : <p>No open advisory in this snapshot. The condition shown above is the component record, not a confirmed fault cause.</p>}
          <Link className="bp-evidence-action" to={`/health/${selected.id}`}>Open condition evidence <Icon name="arrow" size={16}/></Link>
        </aside></div></>}
    </Dialog.Content></Dialog.Portal></Dialog.Root>
  </section>;
}
