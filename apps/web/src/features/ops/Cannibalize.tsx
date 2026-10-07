import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../../shared/ui/Icon";
import { useAsOf } from "./AsOf";
import { useCannibalizeStrategy, type CannibalizeStrategy } from "./api";
import { longDate, num } from "./format";
import { EmptyState, Modal, Query } from "./ui";

/** Planning: the supervisor asks for a part-swap plan between grounded aircraft. The plan is
 *  a read-only proposal; nothing is recorded until people act on it. */
export function CannibalizeButton() {
  const [open, setOpen] = useState(false);
  return <>
    <button type="button" className="o-cannibal-btn" onClick={() => setOpen(true)}>
      <Icon name="swap" size={22}/>
      <span><strong>GENERATE CANNIBALIZATION STRATEGY</strong><small>Swap parts between grounded aircraft to return the most jets for the least labour</small></span>
    </button>
    <Modal open={open} onOpenChange={setOpen} title="Cannibalization strategy" width={980}>
      {open && <StrategyBody/>}
    </Modal>
  </>;
}

function StrategyBody() {
  const strategy = useCannibalizeStrategy(true);
  return <Query query={strategy} rows={8}>{data => <Strategy data={data}/>}</Query>;
}

const actionLabel = { remove: "REMOVE", transfer: "TRANSFER", install: "INSTALL" } as const;

function Strategy({ data }: { data: CannibalizeStrategy }) {
  const { setAsOf } = useAsOf();
  const v = data.verification;
  const nothing = data.swaps.length === 0;
  return <div className="o-cannibal">
    <p className="o-note"><Icon name="info" size={16}/>Proposal only for {longDate(data.as_of)}{data.replay ? " (replay)" : ""}: nothing is recorded. Each removal needs engineering approval and an entry in both aircraft's records. Synthetic data.</p>
    <div className="o-cannibal-kpis">
      <div><span>Aircraft unblocked</span><b>{data.aircraft_unblocked.length}</b><small>{data.aircraft_unblocked.join(", ") || "none"}</small></div>
      <div><span>Available after repairs</span><b>{data.available_now} → {data.available_after_repairs}</b><small>of {data.fleet_size}; unblocked aircraft still need bay time</small></div>
      <div><span>Swap labour</span><b>{num(data.total_labor_hours, 1)} h</b><small>man-hours, removal + fitting</small></div>
      <div><span>Plan check</span><b className={v.greedy_is_optimal === false ? "t-warn" : "t-ok"}>{v.greedy_is_optimal == null ? "not checked" : v.greedy_is_optimal ? "optimal" : "exact plan used"}</b><small>{v.optimal_unblocked == null ? v.exact_method : `optimum ${v.optimal_unblocked} aircraft · ${num(v.optimal_labor_hours ?? 0, 1)} h`}</small></div>
    </div>

    {nothing && <EmptyState title={data.unmet.length ? "No swap can unblock an aircraft" : "No grounded aircraft is waiting for a part"} icon={data.unmet.length ? "warning" : "check"}>
      {data.unmet.length ? "The parts these aircraft wait for are not available as healthy units on other grounded aircraft." : "Grounded aircraft are waiting for a bay or are already in work, so robbing parts would not return any of them sooner."}
    </EmptyState>}
    {nothing && data.days_with_blocked_aircraft.length > 0 && <div className="o-cannibal-days">
      <span>Replay a day when aircraft were waiting for parts:</span>
      {data.days_with_blocked_aircraft.map(day => <button key={day} type="button" className="o-btn sm ghost" onClick={() => setAsOf(day)}>{longDate(day)}</button>)}
    </div>}

    {!nothing && <>
      <h4 className="o-sub">Robbery sequence</h4>
      <ol className="o-robbery">{data.sequence.map(step => <li key={step.step} className={`a-${step.action}`}>
        <span className="o-robbery-n">{String(step.step).padStart(2, "0")}</span>
        <span className="o-robbery-act">{actionLabel[step.action]}</span>
        <span className="o-robbery-what"><b>{step.component_name}</b> <code>{step.part_number}</code> {step.action === "remove" ? "from" : step.action === "install" ? "on" : "to base of"} <Link to={`/aircraft/${step.aircraft}`}>{step.aircraft}</Link>{step.component_id && step.action !== "transfer" && <small>{step.component_id}</small>}</span>
        <span className="o-robbery-h">{num(step.labor_hours, 1)} h</span>
      </li>)}</ol>

      <h4 className="o-sub">Swaps</h4>
      <div className="o-table-wrap"><table className="o-table">
        <thead><tr><th>#</th><th>Swap</th><th className="num">Donor HI</th><th className="num">Labour</th><th className="num">Supply wait avoided</th><th className="num">Donor then waits</th></tr></thead>
        <tbody>{data.swaps.map(s => <tr key={s.swap}>
          <td className="o-mono">{s.swap}</td>
          <td><span className="o-strong">{s.text}</span><small>{s.part_number} · {s.work_order}{s.cross_base ? " · cross-base move" : ""}</small></td>
          <td className="num">{num(s.donor_health_index, 0)}</td>
          <td className="num">{num(s.labor_hours, 1)} h</td>
          <td className="num">{num(s.supply_wait_avoided_days, 0)} d</td>
          <td className="num">{num(s.donor_new_wait_days, 0)} d</td>
        </tr>)}</tbody>
      </table></div>
    </>}

    <div className="o-cannibal-cols">
      {data.hangar_queens.length > 0 && <section><h4 className="o-sub">Donors (hangar queens)</h4><ul className="o-plain">{data.hangar_queens.map(q => <li key={q.aircraft}><Link to={`/aircraft/${q.aircraft}`}>{q.aircraft}</Link> gives {q.components_removed.length} part{q.components_removed.length === 1 ? "" : "s"}</li>)}</ul></section>}
      {data.forge.length > 0 && <section><h4 className="o-sub"><Icon name="printer" size={14}/> Printed instead (Project Forge)</h4><ul className="o-plain">{data.forge.map(f => <li key={f.work_order}>{f.aircraft}: {f.component_name} <code>{f.part_number}</code> printed in {f.print_days} day, no robbery needed</li>)}</ul></section>}
      {data.unmet.length > 0 && <section><h4 className="o-sub">Not swapped</h4><ul className="o-plain">{data.unmet.map(u => <li key={u.work_order}>{u.aircraft}: {u.component_name} <code>{u.part_number}</code>, supply in {num(u.supply_wait_days, 0)} d. <small>{u.reason}</small></li>)}</ul></section>}
      <section><h4 className="o-sub">Grounded aircraft</h4><div className="o-cannibal-chips">{data.grounded.map(g => <span key={g.aircraft} className={`o-tag r-${g.role}`} title={`${g.state.replaceAll("_", " ")}${g.waiting_for.length ? ` · waiting for ${g.waiting_for.join(", ")}` : ""}`}>{g.aircraft} · {g.role}</span>)}</div></section>
    </div>

    <h4 className="o-sub">Verification</h4>
    <ul className="o-checks">
      <Check ok={v.no_unit_used_twice}>No unit is moved twice</Check>
      <Check ok={v.types_match}>Every unit matches the component type it replaces</Check>
      <Check ok={v.donors_grounded}>Donors are already grounded; no mission-capable aircraft is robbed</Check>
      <Check ok={v.donors_not_unblocked}>No donor is counted as returned</Check>
      <Check ok={v.recipients_fully_covered}>Each unblocked aircraft gets every part it waits for</Check>
      <Check ok={v.greedy_is_optimal !== false}>Greedy: {v.greedy_unblocked} aircraft, {num(v.greedy_labor_hours, 1)} h. Exact optimum: {v.optimal_unblocked ?? "—"} aircraft, {v.optimal_labor_hours == null ? "—" : `${num(v.optimal_labor_hours, 1)} h`}. Plan returned: {v.plan_source}.</Check>
    </ul>
    <details className="o-cannibal-method"><summary>Method and assumptions</summary><p>{data.method} Exact check: {v.exact_method}.</p><ul>{data.assumptions.map(a => <li key={a}>{a}</li>)}</ul></details>
  </div>;
}

function Check({ ok, children }: { ok: boolean; children: ReactNode }) {
  return <li className={ok ? "ok" : "bad"}><Icon name={ok ? "check" : "warning"} size={14}/>{children}</li>;
}
