from copy import deepcopy

import pytest
from sqlalchemy.orm import Session

from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.plan_simulation import calculate, plan_payload, save_comparison
from fleet_maintenance.services.planning import propose_plan


def test_comparison_retains_exact_plan_and_rejects_changed_inputs(isolated_session: Session):
    plan = propose_plan(isolated_session)
    payload = plan_payload(plan)
    result = calculate(payload)
    saved = save_comparison(isolated_session, payload, result, "comparison-fixed")
    isolated_session.commit()
    assert saved.metrics["plan_id"] == plan.id
    assert saved.metrics["plan_sha256"] == payload["plan_sha256"]
    assert save_comparison(isolated_session, payload, result, saved.id).id == saved.id
    assignments = deepcopy(plan.assignments)
    assignments[0]["end"] += 1
    plan.assignments = assignments
    isolated_session.commit()
    with pytest.raises(ApprovalConflict, match="changed after submission"):
        save_comparison(isolated_session, payload, result, "changed")
