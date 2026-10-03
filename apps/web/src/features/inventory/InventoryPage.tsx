import { useQuery } from "@tanstack/react-query";

import { api, arrayOf, isInventoryPart, type InventoryPart } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";

export function InventoryPage() {
  const query = useQuery({ queryKey: ["inventory"], queryFn: () => api<InventoryPart[]>("/inventory", undefined, arrayOf(isInventoryPart)) });
  return <section><h2>Parts and bottlenecks</h2><p className="muted">Quantities and lead times are explicitly synthetic demonstration inputs.</p><article className="card"><AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}><table><thead><tr><th>Part</th><th>Available</th><th>Reserved</th><th>Lead time</th><th>Version</th></tr></thead><tbody>{query.data?.map((part) => <tr key={part.id}><td>{part.name}</td><td>{part.on_hand}</td><td>{part.reserved}</td><td>{part.lead_time_slots} slots</td><td>{part.version}</td></tr>)}</tbody></table></AsyncState></article></section>;
}
