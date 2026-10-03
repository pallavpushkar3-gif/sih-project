import type { Plan } from "../../shared/api/client";

function explain(diagnostic:string){if(diagnostic.includes("Insufficient aggregate stock")&&diagnostic.includes("part-filter"))return "Not enough available filters. Open Supply bay, inspect replenishment time, then calculate a new version.";return diagnostic;}
export function ConstraintDetails({plan}:{plan:Plan}){if(plan.solver_status!=="invalid"&&!plan.diagnostics.length)return null;return <div className="plan-blocker"><span>!</span><div><strong>{plan.solver_status==="invalid"?"No feasible schedule was created":"Constraint notes"}</strong><p>{explain(plan.diagnostics[0]??"The current mission inputs need review.")}</p></div></div>;}
