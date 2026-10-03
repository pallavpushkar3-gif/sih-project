import { NavLink, Outlet } from "react-router-dom";

const links = [
  ["/fleet", "Fleet", "Aircraft overview", "aircraft"],
  ["/alerts", "Alerts", "Review evidence", "attention"],
  ["/planning", "Planning", "Schedule work", "schedule"],
  ["/inventory", "Inventory", "Parts and logistics", "parts"],
  ["/scenarios", "Scenarios", "Compare outcomes", "compare"],
] as const;

function NavIcon({ name }: { name: string }) {
  const paths: Record<string, React.ReactNode> = {
    aircraft: <path d="M3 13h7l4 7h2l-2-7h5.5a2.5 2.5 0 0 0 0-5H14l2-6h-2l-4 6H3l2 2.5Z" />,
    attention: <><path d="M12 3 2.7 19h18.6L12 3Z" /><path d="M12 9v4m0 3h.01" /></>,
    schedule: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4m10-4v4M3 10h18m-14 4h4m3 0h3m-10 3h3" /></>,
    parts: <><path d="m12 2 9 5-9 5-9-5 9-5Z" /><path d="m3 12 9 5 9-5M3 17l9 5 9-5" /></>,
    compare: <><path d="M4 19V9m6 10V5m6 14v-7m4 7H2" /></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>;
}

export function ApplicationLayout() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><span>F</span></span>
          <div><strong>FlightDeck</strong><small>Fleet maintenance</small></div>
        </div>
        <div className="nav-label">Workspace</div>
        <nav aria-label="Primary">
          {links.map(([to, label, description, icon]) => (
            <NavLink key={to} to={to}><NavIcon name={icon} /><span><b>{label}</b><small>{description}</small></span></NavLink>
          ))}
        </nav>
        <div className="sidebar-card">
          <span className="live-dot" />
          <div><strong>Local demonstrator</strong><span>All services connected</span></div>
        </div>
        <div className="scope-note">
          <strong>Evidence boundary</strong>
          <span>Synthetic fleet and logistics. Simulation results are projections.</span>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <div className="breadcrumbs"><strong>PS 26249</strong><i>/</i><span>Fleet maintenance</span><em>DEMO</em></div>
          <div className="topbar-actions">
            <span className="status-pill"><span className="live-dot" /> Systems online</span>
            <span className="avatar">DP</span>
          </div>
        </header>
        <div className="page"><Outlet /></div>
      </main>
    </div>
  );
}
