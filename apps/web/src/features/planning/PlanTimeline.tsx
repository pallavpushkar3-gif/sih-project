import type { Plan } from "../../shared/api/client";
export function PlanTimeline({ plan }: { plan: Plan }) {
  if (!plan.assignments.length) return null;
  const end = Math.max(...plan.assignments.map((assignment) => assignment.end), 1);
  const extent = Math.ceil(end / 4) * 4;
  return <div className="timeline-scroll"><div className="tactical-timeline" role="img" aria-label={`Maintenance timeline. ${plan.assignments.length} tasks over ${extent * 8} hours. Exact start and end values are in the assignment table.`}><div className="timeline-axis"><span>Task</span><div>{Array.from({ length: 5 }, (_, index) => <span key={index}>{index * extent * 2}h</span>)}</div></div>{plan.assignments.map((assignment, index) => <div className="timeline-row" key={assignment.task_id}><span title={assignment.task_id}>{assignment.task_id}</span><div className="timeline-track"><span className={`timeline-block tone-${index % 3}`} style={{ left: `${assignment.start / extent * 100}%`, width: `${(assignment.end-assignment.start) / extent * 100}%` }}><span>{(assignment.end-assignment.start)*8}h</span></span></div></div>)}</div></div>;
}
