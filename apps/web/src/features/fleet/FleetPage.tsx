import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api, arrayOf, isFleetItem, type FleetItem } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { Icon } from "../../shared/ui/Icon";
import { PageHeader, RefreshButton } from "../../shared/ui/WorkspaceUI";
export function FleetPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "open" | "clear">("all");
  const query = useQuery({ queryKey: ["fleet"], queryFn: () => api<FleetItem[]>("/fleet", undefined, arrayOf(isFleetItem)) });
  const records = query.data;
  const visibleFleet = records?.filter((item) => `${item.tail_number} ${item.label}`.toLowerCase().includes(search.trim().toLowerCase()) && (filter === "all" || (filter === "open" ? item.open_tasks > 0 : item.open_tasks === 0)));
  return <section>
    <PageHeader eyebrow="FLEET OPERATIONS" title="Fleet overview" description="Choose an aircraft to review its component evidence. Open work means recorded maintenance tasks, not a safety rating." actions={<RefreshButton fetching={query.isFetching} onClick={() => void query.refetch()}/>}/>
    <article className="card fleet-register"><div className="card-heading"><div><h2>Aircraft register</h2><p>Open a component record to inspect its evidence and maintenance context.</p></div><span className="count-label">{records ? `${records.length} aircraft` : "Loading"}</span></div>
      <div className="table-toolbar"><div className="segmented-control" aria-label="Filter aircraft">{([['all','All aircraft'],['open','Open work'],['clear','No open work']] as const).map(([value,label]) => <button key={value} className={filter===value?"selected":""} aria-pressed={filter===value} onClick={() => setFilter(value)}>{label}</button>)}</div><div className="search-field"><Icon name="search" size={17}/><label className="sr-only" htmlFor="fleet-search">Search aircraft</label><input id="fleet-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search tail number or aircraft…"/>{search && <button className="icon-button" aria-label="Clear aircraft search" onClick={() => setSearch("")}><Icon name="close" size={15}/></button>}</div></div>
      <AsyncState loading={query.isLoading} error={query.error} empty={!visibleFleet?.length} emptyMessage={search || filter !== "all" ? "No aircraft match your filters" : "No aircraft records yet"} onRetry={() => void query.refetch()}>
        <div className="table-scroll"><table className="fleet-table"><thead><tr><th scope="col">Aircraft</th><th scope="col">Maintenance</th><th scope="col">Components</th><th scope="col">Open tasks</th><th scope="col">Source</th><th scope="col"><span className="sr-only">Actions</span></th></tr></thead><tbody>{visibleFleet?.map((item) => <tr key={item.id}><td><div className="asset-cell"><span className="asset-icon"><Icon name="aircraft" size={21}/></span><div>{item.component_ids.length ? <Link className="record-link" to={`/components/${encodeURIComponent(item.component_ids[0])}`}>{item.tail_number}</Link> : <strong>{item.tail_number}</strong>}<small>{item.label}</small></div></div></td><td><span className={`badge ${item.open_tasks ? "badge-warning" : "badge-normal"}`}><i/>{item.open_tasks ? "Open work" : "No open tasks"}</span></td><td>{item.components}</td><td><strong className={item.open_tasks ? "warning-text" : ""}>{item.open_tasks}</strong></td><td><span className="source-tag">{item.provenance}</span></td><td>{item.component_ids.length ? <Link className="row-action" to={`/components/${encodeURIComponent(item.component_ids[0])}`} aria-label={`View component for ${item.tail_number}`}>View record<Icon name="arrow" size={15}/></Link> : <span className="muted">No component</span>}</td></tr>)}</tbody></table></div><div className="table-footer"><span>Showing {visibleFleet?.length} of {records?.length} aircraft</span><span>Updated {query.dataUpdatedAt ? new Date(query.dataUpdatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}</span></div>
      </AsyncState>
    </article>
  </section>;
}
