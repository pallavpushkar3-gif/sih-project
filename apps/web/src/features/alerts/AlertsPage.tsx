import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, arrayOf, isAlert, type Alert } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { StatusBadge } from "../../shared/ui/StatusBadge";

export function AlertsPage() {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["alerts"],
    queryFn: () => api<Alert[]>("/alerts", undefined, arrayOf(isAlert)),
  });
  const acknowledge = useMutation({
    mutationFn: (id: string) =>
      api<Alert>(
        `/alerts/${id}/acknowledgements`,
        {
          method: "POST",
          headers: { "X-Demo-Role": "engineer", "X-Demo-User": "demo-engineer" },
        },
        isAlert,
      ),
    onSuccess: () => client.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <section>
      <h2>Alert history</h2>
      <p className="muted">
        Policy transitions remain distinct from acknowledgement and mandatory work.
      </p>
      {acknowledge.error && <div className="state error">{acknowledge.error.message}</div>}
      <article className="card">
        <AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}>
          <table>
            <thead>
              <tr>
                <th>Component</th><th>State</th><th>Reason</th><th>Policy</th><th>Reviews</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {query.data?.map((alert) => (
                <tr key={alert.id}>
                  <td>{alert.component_id}</td>
                  <td><StatusBadge status={alert.state} /></td>
                  <td>{alert.reason}</td>
                  <td>{alert.policy_version}</td>
                  <td>
                    {alert.acknowledgements.length
                      ? alert.acknowledgements.map((item) => item.actor).join(", ")
                      : "Unacknowledged"}
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() => acknowledge.mutate(alert.id)}
                      disabled={acknowledge.isPending}
                    >
                      Record technical review
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </AsyncState>
      </article>
    </section>
  );
}
