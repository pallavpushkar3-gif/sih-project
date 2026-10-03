import type { Alert } from "../../shared/api/client";

export function AlertHistory({ alert }: { alert: Alert }) {
  return <div className="history-rail"><span className="history-event active"><i /><b>Signal created</b><small>{alert.reason}</small></span>{alert.acknowledgements.map((item) => <span className="history-event" key={item.created_at}><i /><b>Technical review recorded</b><small>{item.actor} · {new Date(item.created_at).toLocaleString()}</small></span>)}</div>;
}
