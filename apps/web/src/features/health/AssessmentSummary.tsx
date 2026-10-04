import type { Assessment } from "../../shared/api/client";
export function AssessmentSummary({assessment,level}:{assessment:Assessment|null|undefined;level?:number}){
  const available=!!assessment&&['available','eligible','qualified'].includes(assessment.state)&&assessment.estimate_cycles!==null;
  const lower=assessment?.lower_cycles,upper=assessment?.upper_cycles,estimate=assessment?.estimate_cycles;
  const interval=available&&lower!=null&&upper!=null&&estimate!=null&&upper>=lower;
  const minimum=interval?Math.min(lower,estimate):0,maximum=interval?Math.max(upper,estimate):0;
  const position=(value:number)=>maximum===minimum?150:20+(value-minimum)/(maximum-minimum)*260;
  const marker=interval?position(estimate):150,lowPoint=interval?position(lower):150,highPoint=interval?position(upper):150;
  return <div className="assessment-summary"><span>Estimated remaining life</span><strong>{available?estimate?.toFixed(1):'—'}<small>{available?'cycles':'Data unavailable'}</small></strong>{interval?<><svg viewBox="0 0 300 48" role="img" aria-label={`Estimated ${estimate.toFixed(1)} cycles, interval ${lower.toFixed(1)} to ${upper.toFixed(1)} cycles`}><line x1={lowPoint} y1="22" x2={highPoint} y2="22" stroke="var(--accent)" strokeWidth="3"/><path d={`M${lowPoint} 12v20M${highPoint} 12v20`} stroke="var(--accent)" strokeWidth="2"/><circle cx={marker} cy="22" r="6" fill="var(--text-primary)"/></svg><p>{lower.toFixed(1)}–{upper.toFixed(1)} cycles{level!==undefined?` · Nominal ${(level*100).toFixed(0)}% prediction interval`:' · Prediction interval'}</p></>:<p>No eligible prediction interval.</p>}<p className="interval-meaning">A prediction range, not an individual engine’s failure probability. Public C-MAPSS engine histories are simulated.</p></div>;
}
