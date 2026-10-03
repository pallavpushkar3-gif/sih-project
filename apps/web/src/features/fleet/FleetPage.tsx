import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import heroImage from "../../assets/maintenance-hangar.png";
import { api, arrayOf, isFleetItem, type FleetItem } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";

function AircraftSilhouette() {
  return (
    <svg className="aircraft-silhouette" viewBox="0 0 180 70" aria-hidden="true">
      <path d="M8 39h54l33-29h10L91 39h58l18-10h6l-9 17 9 17h-6l-18-10H91l14 17H95L62 53H8l-8-7Z" />
    </svg>
  );
}

export function FleetPage() {
  const query = useQuery({
    queryKey: ["fleet"],
    queryFn: () => api<FleetItem[]>("/fleet", undefined, arrayOf(isFleetItem)),
  });
  const openTasks = query.data?.reduce((total, item) => total + item.open_tasks, 0) ?? 0;
  return (
    <section>
      <article className="hero" style={{ "--hero-image": `url(${heroImage})` } as React.CSSProperties}>
        <div className="hero-content">
          <span className="hero-kicker">Maintenance command centre</span>
          <h1>Keep every aircraft<br />ready for its next mission.</h1>
          <p>Turn health evidence, maintenance demand, parts and capacity into one clear plan.</p>
          <div className="hero-actions">
            <Link className="button" to="/planning">Build maintenance plan</Link>
            <Link className="button ghost" to="/scenarios">Compare scenarios</Link>
          </div>
        </div>
        <div className="hero-status"><span className="live-dot" /> Live operational view</div>
      </article>

      <div className="section-heading">
        <div><span className="eyebrow">Today’s fleet</span><h2>What needs attention</h2></div>
        <p>Open work stays visible even when predictive evidence is unavailable.</p>
      </div>

      <div className="metric-grid">
        <article className="metric-card"><span>Aircraft monitored</span><strong>{query.data?.length ?? "—"}</strong><small>Current demonstration fleet</small></article>
        <article className="metric-card warning"><span>Mandatory tasks</span><strong>{openTasks}</strong><small>Require maintenance review</small></article>
        <article className="metric-card"><span>Parts on watch</span><strong>1</strong><small>Filter availability is constrained</small></article>
        <article className="metric-card neutral"><span>Prediction status</span><strong>Not active</strong><small>Model acceptance is pending</small></article>
      </div>

      <div className="section-heading compact">
        <div><span className="eyebrow">Aircraft</span><h2>Fleet status</h2></div>
      </div>
      <AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}>
        <div className="aircraft-grid">
          {query.data?.map((item, index) => (
            <Link className="aircraft-card" key={item.id} to={`/components/${item.component_ids[0]}`}>
              <div className="aircraft-card-top">
                <span className="aircraft-type">A{index === 0 ? "320" : "321"} · Engine health</span>
                <span className={`health-pill ${item.open_tasks ? "needs-review" : "ready"}`}>
                  {item.open_tasks ? "Review required" : "Ready"}
                </span>
              </div>
              <AircraftSilhouette />
              <div className="aircraft-identity"><strong>{item.tail_number}</strong><span>{item.label.replace("Synthetic demonstrator ", "")}</span></div>
              <div className="aircraft-stats">
                <div><span>Components</span><strong>{item.components}</strong></div>
                <div><span>Open work</span><strong>{item.open_tasks}</strong></div>
                <div><span>Data source</span><strong>Demo</strong></div>
              </div>
              <span className="card-link">Open aircraft record <b>→</b></span>
            </Link>
          ))}
        </div>
      </AsyncState>

      <div className="section-heading compact">
        <div><span className="eyebrow">A clear path to action</span><h2>From evidence to an approved plan</h2></div>
        <p>FlightDeck keeps technical evidence, human review and operational commitment separate and traceable.</p>
      </div>
      <div className="workflow-grid">
        <Link to="/alerts" className="workflow-step"><span>01</span><div><strong>Review attention items</strong><p>See why an aircraft needs review without inventing a prediction.</p></div><b>→</b></Link>
        <Link to="/planning" className="workflow-step"><span>02</span><div><strong>Build a feasible work plan</strong><p>Check deadlines, maintenance capacity and parts together.</p></div><b>→</b></Link>
        <Link to="/scenarios" className="workflow-step"><span>03</span><div><strong>Compare capacity choices</strong><p>Test operational assumptions before making a commitment.</p></div><b>→</b></Link>
      </div>
    </section>
  );
}
