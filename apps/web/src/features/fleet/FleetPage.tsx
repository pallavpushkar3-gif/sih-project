import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import {
  api,
  arrayOf,
  isFleetItem,
  type FleetItem,
} from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";

export function FleetPage() {
  const query = useQuery({
    queryKey: ["fleet"],
    queryFn: () => api<FleetItem[]>("/fleet", undefined, arrayOf(isFleetItem)),
  });
  const openTasks = query.data?.reduce((total, item) => total + item.open_tasks, 0) ?? 0;
  return (
    <section>
      <h2>Fleet overview</h2>
      <p className="muted">Labelled synthetic mappings with traceable maintenance demand.</p>
      <div className="grid">
        <article className="card span-4">
          <span className="muted">Aircraft</span>
          <div className="metric">{query.data?.length ?? "—"}</div>
        </article>
        <article className="card span-4">
          <span className="muted">Open mandatory tasks</span>
          <div className="metric">{openTasks}</div>
        </article>
        <article className="card span-4">
          <span className="muted">Prediction support</span>
          <div className="metric">Blocked</div>
          <small className="muted">No evaluated model artifact</small>
        </article>
        <article className="card span-12">
          <AsyncState loading={query.isLoading} error={query.error} empty={!query.data?.length}>
            <table>
              <thead><tr><th>Tail</th><th>Label</th><th>Components</th><th>Open tasks</th><th>Provenance</th></tr></thead>
              <tbody>
                {query.data?.map((item) => (
                  <tr key={item.id}>
                    <td>{item.component_ids[0] ? <Link to={`/components/${item.component_ids[0]}`}>{item.tail_number}</Link> : item.tail_number}</td>
                    <td>{item.label}</td><td>{item.components}</td><td>{item.open_tasks}</td><td>{item.provenance}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </AsyncState>
        </article>
      </div>
    </section>
  );
}
