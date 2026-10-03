import { useQuery } from "@tanstack/react-query";

import { api, arrayOf, isInventoryPart, type InventoryPart } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";

export function InventoryPage() {
  const query = useQuery({ queryKey: ["inventory"], queryFn: () => api<InventoryPart[]>("/inventory", undefined, arrayOf(isInventoryPart)) });
  return <section><div className="page-title"><div><span className="eyebrow">Material readiness</span><h1>Parts for upcoming work</h1><p>See what is available, what is already committed, and which lead times could delay the maintenance plan.</p></div></div><AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}><div className="parts-grid">{query.data?.map((part) => {const available=part.on_hand-part.reserved;return <article className="part-card" key={part.id}><div className="part-icon">◇</div><div><span className="eyebrow">Engine maintenance</span><h2>{part.name.replace("Synthetic ", "")}</h2><p className="muted">Demonstration inventory · Record version {part.version}</p></div><div className="stock-number"><strong>{available}</strong><span>available now</span></div><div className="stock-track"><i style={{width:`${Math.min(100,(available/Math.max(1,part.on_hand))*100)}%`}} /></div><div className="part-facts"><span><b>{part.on_hand}</b> on hand</span><span><b>{part.reserved}</b> reserved</span><span><b>{part.lead_time_slots * 8} hr</b> replenishment</span></div></article>;})}</div></AsyncState><p className="footnote">Inventory quantities and lead times are synthetic demonstration inputs.</p></section>;
}
