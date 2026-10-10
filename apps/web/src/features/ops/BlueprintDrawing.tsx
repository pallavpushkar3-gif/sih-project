import { Fragment } from "react";
import type { ArchitectureComponent, StructureKind } from "./componentArchitecture";
import { architectureColor } from "./componentArchitecture";
import { stateLabel } from "./format";

// Section drawings share the conceptual installation coordinates of the 3D cutaway.
// They describe assembly envelopes, not aircraft-specific dimensions or fault locations.
const sizes: Record<StructureKind, [number, number]> = {
  compressor: [92, 40], turbine: [78, 42], reservoir: [32, 20], valve: [28, 18],
  pump: [26, 24], actuator: [65, 13], filter: [30, 19], generator: [36, 22],
  electronics: [32, 23], battery: [32, 24], brake: [26, 20], strut: [45, 12],
  tyre: [26, 19], sensor: [27, 10], cooling: [34, 24],
};
function Assembly({ kind }: { kind: StructureKind }) {
  const [w, h] = sizes[kind];
  const rectangular = ["electronics", "battery", "cooling"].includes(kind);
  return <>
    <path className="bp-part-fill" d={rectangular
      ? `M${-w / 2} ${-h / 2}h${w}v${h}h${-w}Z`
      : `M${-w / 2} ${-h * .3} L${-w * .4} ${-h / 2}H${w * .4}L${w / 2} ${-h * .3}V${h * .3}L${w * .4} ${h / 2}H${-w * .4}L${-w / 2} ${h * .3}Z`}/>
    <g className="bp-part-detail" fill="none" strokeWidth=".8">
      <path d={`M${-w * .6} 0H${w * .6}`}/>
      {Array.from({ length: kind === "compressor" ? 7 : kind === "turbine" ? 5 : 3 }, (_, i) => {
        const x = -w * .3 + i * w * .6 / (kind === "compressor" ? 6 : kind === "turbine" ? 4 : 2);
        return <path key={i} d={`M${x} ${-h * .42}v${h * .84}m-2 ${-h * .65}h4m-4 ${h * .45}h4`}/>;
      })}
      {kind === "electronics" && <path d="M-10 -6H10V6H-10Zm3 3h14v6H-7Z"/>}
      {kind === "battery" && <path d="M-8 -8v16M0 -8v16M8 -8v16"/>}
      {(kind === "strut" || kind === "actuator") && <path d={`M0 -2h${w * .7}v4H0Z`}/>}
      {kind === "tyre" && <path d="M-9 -7H9V7H-9Z M-6 -7v14M6 -7v14"/>}
    </g>
  </>;
}
export function BlueprintDrawing({ components, onSelect }: { components: ArchitectureComponent[]; onSelect: (id: string) => void }) {
  const mapped = components.filter(item => item.layout);
  const coreFinding = mapped.some(item => ["ENG-CMP", "ENG-TRB"].includes(item.type) && item.attention);
  return <>
    <g className="bp-airframe" fill="none" stroke="currentColor" strokeWidth="1.25" strokeLinejoin="round">
      <path d="M94 275 L132 272 C180 258 230 254 270 252 L360 239 C428 237 535 243 633 250 L670 253 L670 297 L633 300 C535 307 428 313 360 311 L270 298 C230 296 180 292 132 278 Z"/>
      <path d="M341 239 L467 203 L565 89 L582 91 L603 246 M341 311 L467 347 L565 461 L582 459 L603 304"/>
      <path d="M373 241 L455 227 L554 118 M373 309 L455 323 L554 432 M458 247 L574 221 L583 207 L592 246 M458 303 L574 329 L583 343 L592 304"/>
      <path d="M283 251L356 246V258L292 262 M283 299L356 304V292L292 288 M142 275H688" strokeDasharray="4 4"/>
      {/* Wing ribs, spars, fuel cells and control surfaces remain visible through the cutaway. */}
      {Array.from({ length: 9 }, (_, i) => <path key={i} d={`M${408 + i * 20} ${233 - i * 14}L${435 + i * 18} 242 M${408 + i * 20} ${317 + i * 14}L${435 + i * 18} 308`} opacity=".6"/>)}
      <path d="M466 207L557 150L584 229L486 241Z M466 343L557 400L584 321L486 309Z M497 181L574 221 M497 369L574 329 M595 246L607 299"/>
      {/* Pilot cabin: canopy frames, instrument panel, seat and harness. */}
      <path d="M234 269C222 256 266 251 292 254C320 256 322 266 315 271C282 280 250 280 234 269Z M246 255V276 M293 255V275 M260 260h20v13h-20Z M262 262l16 9m0-9-16 9 M237 258v13m3-13v13"/>
      <path d="M633 250V300 M645 251V299 M655 252V298 M660 253V297 M643 254l15 41m-15-7 15-31"/>
      <path d="M400 244H616V306H400Z" className={coreFinding ? "bp-engine-envelope has-finding" : "bp-engine-envelope"}/>
      <g transform="translate(778 140)"><path d="M0 -67L8 -22C31 -13 32 10 0 15C-32 10-31-13-8-22Z M-90 2L-16-2M16-2L90 2 M-23 14V40H-16V15 M23 14V40H16V15 M0 14V39 M-35 3L-29 12L-21 4M35 3L29 12L21 4"/><ellipse cy="-7" rx="13" ry="14"/><path d="M-7-12H7V5H-7Z M-90 2L-46 12L-14 8M90 2L46 12L14 8"/></g>
      <path d="M94 524L142 516L249 504L382 502L521 509L670 511V538L584 542L395 534L245 535L142 529Z M231 506C242 468 307 470 331 504 M247 505C258 481 294 482 311 504 M535 510L592 423L621 432L632 511 M592 423L604 510 M255 535L265 570 M531 539L544 569"/>
      <path d="M260 496h26v14h-26Z M260 498l24 10 M309 495v15 M402 504v31M448 505v31M475 506v31 M633 512v27M645 512v27"/>
      <ellipse cx="266" cy="579" rx="11" ry="12"/><ellipse cx="546" cy="582" rx="15" ry="14"/>
      <path d="M94 470H670M94 463V477M670 463V477M58 89V461M51 89H65M51 461H65" strokeDasharray="3 3" opacity=".45"/>
    </g>
    <g className="bp-view-labels" fill="currentColor"><text x="85" y="54">01 / TOP-DOWN CUTAWAY</text><text x="703" y="54">02 / FRONT</text><text x="85" y="496">03 / SIDE CUTAWAY</text><text x="702" y="575">ILLUSTRATIVE</text><text x="252" y="238">PILOT CABIN</text></g>
    {mapped.map(item => {
      const [x, y, z] = item.layout!.position;
      return <Fragment key={item.id}><g className={`bp-assembly${item.attention ? " is-alert" : ""}`} data-component-id={item.id} data-attention={item.attention} data-projection="plan" style={{ color: architectureColor(item) }} transform={`translate(${400 - z * 56} ${275 + x * 59})`} role="button" tabIndex={0} aria-label={`Inspect ${item.name}: ${stateLabel[item.state]}`} onClick={() => onSelect(item.id)} onKeyDown={event => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); onSelect(item.id); } }}>
        <title>{item.number}. {item.name} · {stateLabel[item.state]}</title><Assembly kind={item.layout!.kind}/>
        <text className="bp-part-number" x={-sizes[item.layout!.kind][0] / 2} y={-sizes[item.layout!.kind][1] / 2 - 4}>{String(item.number).padStart(2, "0")}</text>
      </g>
      {/* Separate projection avoids a large empty hit area between the two drawings. */}
      {["ENG-CMP", "ENG-TRB", "LG-STR", "LG-TYR", "AVN-FCC", "AVN-DSP", "AVN-SNS"].includes(item.type) && <g className={`bp-side-assembly${item.attention ? " is-alert" : ""}`} style={{ color: architectureColor(item) }} transform={`translate(${400 - z * 56} ${524 - y * 46})`} aria-hidden="true" onClick={() => onSelect(item.id)}>
        <Assembly kind={item.layout!.kind}/>
      </g>}
      </Fragment>;
    })}
  </>;
}
