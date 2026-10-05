import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, arrayOf, isFleetItem } from "../../shared/api/client";
import { AsyncState } from "../../shared/ui/AsyncState";
import { Icon } from "../../shared/ui/Icon";

export function OverviewPage() {
  const fleet = useQuery({ queryKey: ['fleet'], queryFn: () => api('/fleet', undefined, arrayOf(isFleetItem)) });
  const open = fleet.data?.filter(aircraft => aircraft.open_tasks > 0 && !aircraft.id.startsWith("trial-"));
  return <section className="overview-page">
    <div className="overview-hero"><div className="overview-intro"><span className="eyebrow">AIRCRAFT MAINTENANCE DECISIONS</span><h1>Know what needs attention.<br/>Plan what happens next.</h1><p>Review AI estimates of remaining engine life, understand the evidence, and check maintenance options against available parts and crew.</p><div className="overview-actions"><Link className="button" to="/demo">Try it with your data<Icon name="arrow" size={18}/></Link><Link className="text-link" to="/ai">How the AI helps</Link></div><p className="footnote">Demonstrator · Simulated engine histories and synthetic logistics. Estimates support human review.</p></div><Link className="overview-aircraft" to="/demo"><img src={`${import.meta.env.BASE_URL}models/aircraft-poster.png`} alt="Illustrative aircraft used in the interactive trial"/><span>Explore the aircraft. Test a maintenance decision.<Icon name="arrow" size={18}/></span></Link></div>
    <ol className="decision-steps" aria-label="Maintenance decision flow">
      <li><span>1</span><div><h2>Review a component</h2><p>Choose an aircraft. Check its engine estimate, uncertainty and data quality.</p></div></li>
      <li><span>2</span><div><h2>Check maintenance options</h2><p>Review recorded tasks, parts and crew. Calculate a schedule; compare what-if outcomes when useful.</p></div></li>
      <li><span>3</span><div><h2>Review approval & work</h2><p>A supervisor reviews the exact proposal. Follow its reservations and recorded work outcomes.</p></div></li>
    </ol>
    <article className="card overview-work"><div className="card-heading"><div><h2>Aircraft with open maintenance work</h2><p>Recorded tasks awaiting action. This list does not classify aircraft safety or predicted engine health.</p></div></div>
      <AsyncState loading={fleet.isLoading} error={fleet.error} empty={!open?.length} emptyMessage="No open maintenance tasks recorded" onRetry={() => void fleet.refetch()}>
        <ul>{open?.map(aircraft => <li key={aircraft.id}><div><strong>{aircraft.tail_number}</strong><p>{aircraft.open_tasks} open task{aircraft.open_tasks === 1 ? '' : 's'} · {aircraft.provenance}</p></div><Link className="button-secondary" to={aircraft.component_ids[0] ? `/components/${encodeURIComponent(aircraft.component_ids[0])}` : '/fleet/register'} aria-label={`Review ${aircraft.tail_number}`}>Review aircraft<Icon name="arrow" size={16}/></Link></li>)}</ul>
      </AsyncState>
    </article>
  </section>;
}
