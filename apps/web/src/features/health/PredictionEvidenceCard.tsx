import type { Assessment } from "../../shared/api/client";
import { Icon } from "../../shared/ui/Icon";
import { StatusBadge } from "../../shared/ui/StatusBadge";
export function PredictionEvidenceCard({ assessment, cycle }: { assessment: Assessment | null; cycle: number }) {
  return <article className="card span-4 evidence-card"><div className="card-heading"><div><span className="eyebrow">TRACEABLE EVIDENCE</span><h2>Assessment record</h2></div><Icon name="file" size={20}/></div><StatusBadge status={assessment?.state ?? "unavailable"}/><dl className="evidence-list"><div><dt>Assessment identity</dt><dd>{assessment?.id ?? "No assessment recorded"}</dd></div><div><dt>Input version</dt><dd>{assessment?.input_version ?? "No input snapshot"}</dd></div><div><dt>Model version</dt><dd>{assessment?.model_version ?? "No model installed"}</dd></div><div><dt>Latest component usage</dt><dd>{cycle} operating cycles</dd></div></dl><div className="evidence-note"><Icon name="file" size={16}/><p>Unavailable or withheld assessments contribute no numerical life window to planning.</p></div></article>;
}
