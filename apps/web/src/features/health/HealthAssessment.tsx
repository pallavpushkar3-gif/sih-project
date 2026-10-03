import type { Assessment } from "../../shared/api/client";

export function HealthAssessment({ assessment }: { assessment: Assessment | null }) {
  return <article className="metric-card warning"><span>Assessment state</span><strong>{assessment?.state === "eligible" ? "Eligible" : "Withheld"}</strong><small>{assessment?.model_version ? `Model ${assessment.model_version}` : "No numerical estimate substituted"}</small></article>;
}
