import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import aircraftImage from "../../assets/fleet-aircraft-game.png";
import { api, arrayOf, isFleetItem, type FleetItem } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";

function AircraftSilhouette({ index = 0 }: { index?: number }) {
  return (
    <svg className={`aircraft-silhouette variant-${index}`} viewBox="0 0 180 70" aria-hidden="true">
      <path d="M8 39h54l33-29h10L91 39h58l18-10h6l-9 17 9 17h-6l-18-10H91l14 17H95L62 53H8l-8-7Z" />
    </svg>
  );
}

export function FleetPage() {
  const [search, setSearch] = useState("");
  const query = useQuery({
    queryKey: ["fleet"],
    queryFn: () => api<FleetItem[]>("/fleet", undefined, arrayOf(isFleetItem)),
  });
  const openTasks = query.data?.reduce((total, item) => total + item.open_tasks, 0) ?? 0;
  const aircraftCount = query.data?.length ?? 0;
  const selectedAircraft = query.data?.[0];
  const selectedComponent = selectedAircraft?.component_ids[0] ?? "cmp-eng-01";
  const visibleFleet = query.data?.filter((item) => `${item.tail_number} ${item.label}`.toLowerCase().includes(search.toLowerCase()));
  return (
    <section>
      <article className="command-hero">
        <div className="showroom-head"><div><span>Aircraft</span><h1>Airbus A320</h1><p>{selectedAircraft?.tail_number ?? "Loading aircraft"} · Demonstration aircraft</p></div><div className="view-tabs"><button className="selected">Overview</button><Link to={`/components/${selectedComponent}`}>Engine</Link><Link to="/planning">Maintenance</Link></div></div>
        <div className="aircraft-stage">
          <img src={aircraftImage} alt="Commercial aircraft in the FlightDeck operations view" />
          <Link to={`/components/${selectedComponent}`} className="system-hotspot engine-hotspot"><i /><span>Engine</span></Link>
          <span className="aircraft-shadow" />
        </div>
        <aside className="aircraft-panel">
          <div className="panel-heading"><div><span>Selected aircraft</span><strong>{selectedAircraft?.tail_number ?? "—"}</strong></div><span className="health-pill needs-review">Review required</span></div>
          <div className="panel-section"><span>Maintenance status</span><strong>{selectedAircraft ? `${selectedAircraft.open_tasks} mandatory task${selectedAircraft.open_tasks === 1 ? "" : "s"} open` : "Loading"}</strong><small>Engine inspection remains active</small></div>
          <div className="panel-section"><span>Prediction support</span><strong>Unavailable</strong><small>No approved model artifact; no estimate is substituted</small></div>
          <div className="panel-stats"><div><span>Components</span><b>{selectedAircraft?.components ?? "—"}</b></div><div><span>Open work</span><b>{selectedAircraft?.open_tasks ?? "—"}</b></div><div><span>Source</span><b>Demo</b></div></div>
          <Link className="button" to={`/components/${selectedComponent}`}>Open aircraft record <b>→</b></Link>
        </aside>
        <div className="showroom-summary"><span><b>{aircraftCount || "—"}</b> aircraft monitored</span><span><b>{openTasks}</b> mandatory tasks</span><span><b>Check</b> parts status</span><span><b>Unavailable</b> prediction support</span></div>
      </article>

      <div className="section-heading compact">
        <div><span className="eyebrow">Fleet</span><h2>Choose an aircraft</h2></div>
        <div className="fleet-tools"><label htmlFor="fleet-search">Search aircraft</label><input id="fleet-search" value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="Tail number or label" /></div>
      </div>
      <AsyncState loading={query.isLoading} error={query.error} empty={!visibleFleet?.length} emptyMessage={search ? "No aircraft match this search." : undefined}>
        <div className="aircraft-grid">
          {visibleFleet?.map((item, index) => (
            <Link className="aircraft-card" key={item.id} to={`/components/${item.component_ids[0]}`}>
              <div className="aircraft-card-top">
                <span className="aircraft-type">A{index === 0 ? "320" : "321"} · Engine health</span>
                <span className={`health-pill ${item.open_tasks ? "needs-review" : "ready"}`}>
                  {item.open_tasks ? "Review required" : "Ready"}
                </span>
              </div>
              <div className="aircraft-card-scene"><span className="runway-line" /><AircraftSilhouette index={index} /></div>
              <div className="aircraft-identity"><strong>{item.tail_number}</strong><span>{item.label.replace("Synthetic demonstrator ", "")}</span></div>
              <div className="aircraft-stats">
                <div><span>Components</span><strong>{item.components}</strong></div>
                <div><span>Open work</span><strong>{item.open_tasks}</strong></div>
                <div><span>Data source</span><strong>Demo</strong></div>
              </div>
              <span className="card-link">View aircraft <b>→</b></span>
            </Link>
          ))}
        </div>
      </AsyncState>

      <div className="section-heading compact">
        <div><span className="eyebrow">Decision workflow</span><h2>From evidence to an approved plan</h2></div>
        <p>Three clear decisions connect technical evidence to an operationally feasible plan.</p>
      </div>
      <div className="workflow-grid">
        <Link to="/alerts" className="workflow-step"><span>1</span><div><strong>Review the evidence</strong><p>Understand why attention is required and what is unavailable.</p></div><b>→</b></Link>
        <Link to="/planning" className="workflow-step"><span>2</span><div><strong>Build a feasible plan</strong><p>Check deadline, bay, crew and parts constraints together.</p></div><b>→</b></Link>
        <Link to="/scenarios" className="workflow-step"><span>3</span><div><strong>Compare consequences</strong><p>Test capacity assumptions before committing the plan.</p></div><b>→</b></Link>
      </div>
    </section>
  );
}
