import type { ComponentDetail } from "../../shared/api/client";

export function ComponentHistory({ observations }: { observations: ComponentDetail["observations"] }) {
  const latest = observations.at(-1);
  return <div className="history-summary"><div><span>OBSERVATIONS</span><strong>{observations.length}</strong></div><div><span>LATEST CYCLE</span><strong>{latest?.cycle ?? "—"}</strong></div><div><span>SENSOR</span><strong>{latest?.sensor ?? "—"}</strong></div><div><span>UNIT</span><strong>{latest?.unit ?? "—"}</strong></div></div>;
}
