import type { Assessment } from "../../shared/api/client";

export function PredictionEvidenceCard({ assessment, cycle }: { assessment: Assessment | null; cycle: number }) {
  return <article className="card span-4"><span className="eyebrow">Evidence manifest</span><h3>What the planner receives</h3><div className="explanation-list"><div><span>Assessment state</span><strong>{assessment?.state ?? "Unavailable"}</strong></div><div><span>Input record</span><strong>{assessment?.input_version ?? "None"}</strong></div><div><span>Model used</span><strong>{assessment?.model_version ?? "None"}</strong></div><div><span>Evaluation point</span><strong>Cycle {cycle}</strong></div></div><p className="footnote">A withheld assessment contributes no numerical life window. The mandatory task remains authoritative.</p></article>;
}
