import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api, arrayOf, isAlert, type Alert } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

export function AlertsPage() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["alerts"], queryFn: () => api<Alert[]>("/alerts", undefined, arrayOf(isAlert)) });
  const acknowledge = useMutation({
    mutationFn: (id: string) => api<Alert>(`/alerts/${id}/acknowledgements`, { method: "POST", headers: { "X-Demo-Role": "engineer", "X-Demo-User": "demo-engineer" } }, isAlert),
    onSuccess: () => client.invalidateQueries({ queryKey: ["alerts"] }),
  });
  const open = query.data?.filter((alert) => !alert.acknowledgements.length).length ?? 0;
  return (
    <section>
      <div className="page-title"><div><span className="eyebrow">Technical attention</span><h1>Review what needs action</h1><p>Every alert explains why it exists, what remains protected, and whether a reviewer has seen it.</p></div><div className="title-stat"><strong>{open}</strong><span>Awaiting review</span></div></div>
      {acknowledge.error && <div className="state error">{acknowledge.error.message}</div>}
      <AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}>
        <div className="attention-list">
          {query.data?.map((alert) => {
            const reviewed = alert.acknowledgements.length > 0;
            return <article className="attention-card" key={alert.id}>
              <div className="attention-icon">!</div>
              <div className="attention-body">
                <div className="attention-meta"><span>Aircraft SYN-001 · Engine</span><StatusBadge status={alert.state} /></div>
                <h2>Health estimate needs technical review</h2>
                <p>{alert.reason}</p>
                <div className="why-box"><strong>Why this matters</strong><span>No life estimate is shown because the evidence is not approved. The mandatory inspection remains on the work plan.</span></div>
                <div className="attention-footer"><div><span>Policy</span><strong>{alert.policy_version}</strong></div><div><span>Review status</span><strong>{reviewed ? `Reviewed by ${alert.acknowledgements.map((item) => item.actor).join(", ")}` : "Awaiting technical review"}</strong></div></div>
              </div>
              <div className="attention-actions"><Link className="button ghost-light" to="/components/cmp-eng-01">View evidence</Link><button className="secondary" onClick={() => acknowledge.mutate(alert.id)} disabled={acknowledge.isPending || reviewed}>{reviewed ? "Review recorded" : "Record technical review"}</button></div>
            </article>;
          })}
        </div>
      </AsyncState>
    </section>
  );
}
