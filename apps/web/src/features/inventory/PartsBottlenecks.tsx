import type { InventoryPart } from "../../shared/api/client";

export function PartsBottlenecks({ parts }: { parts: InventoryPart[] }) {
  const constrained = parts.filter((part) => part.on_hand - part.reserved <= 0);
  return <div className={`bottleneck-console ${constrained.length ? "blocked" : "clear"}`}><span>{constrained.length ? "Parts attention required" : "Parts available"}</span><strong>{constrained.length ? `${constrained.length} item prevents a feasible plan` : "Current stock supports the queued work"}</strong><small>{constrained.length ? constrained.map((part) => part.name.replace("Synthetic ", "")).join(", ") : "Approval still rechecks authoritative quantities."}</small></div>;
}
