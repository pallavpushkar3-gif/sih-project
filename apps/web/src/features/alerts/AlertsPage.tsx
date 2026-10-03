import { useQuery } from "@tanstack/react-query";

import { api, arrayOf, isAlert, type Alert } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

export function AlertsPage() {
  const query = useQuery({ queryKey: ["alerts"], queryFn: () => api<Alert[]>("/alerts", undefined, arrayOf(isAlert)) });
  return <section><h2>Alert history</h2><p className="muted">Policy transitions remain distinct from acknowledgement and mandatory work.</p><article className="card"><AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}><table><thead><tr><th>Component</th><th>State</th><th>Reason</th><th>Policy</th></tr></thead><tbody>{query.data?.map((alert) => <tr key={alert.id}><td>{alert.component_id}</td><td><StatusBadge status={alert.state} /></td><td>{alert.reason}</td><td>{alert.policy_version}</td></tr>)}</tbody></table></AsyncState></article></section>;
}
