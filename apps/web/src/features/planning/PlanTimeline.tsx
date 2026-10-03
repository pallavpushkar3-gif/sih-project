import type { Plan } from "../../shared/api/client";

export function PlanTimeline({ plan }: { plan: Plan }) {
  if (!plan.assignments.length) return null;
  return <div className="tactical-timeline" aria-label="Maintenance timeline"><div className="timeline-axis"><span>H+00</span><span>H+08</span><span>H+16</span><span>H+24</span><span>H+32</span></div>{plan.assignments.map((assignment,index)=><div className="timeline-row" key={assignment.task_id}><span>{assignment.task_id.includes("inspect")?"SYN-001 · Engine inspection":"SYN-002 · Filter replacement"}</span><div><i className={`timeline-block tone-${index}`} style={{left:`${Math.min(80,assignment.start*20)}%`,width:`${Math.max(18,(assignment.end-assignment.start)*20)}%`}}>{(assignment.end-assignment.start)*8} hr</i></div></div>)}</div>;
}
