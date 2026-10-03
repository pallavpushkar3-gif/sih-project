import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import AuditEvent, Part
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import propose_plan


def test_stale_proposal_is_rejected_without_commit(isolated_session: Session):
    plan = propose_plan(isolated_session)
    part = isolated_session.get(Part, "part-kit")
    assert part is not None
    part.version += 1
    isolated_session.commit()

    with pytest.raises(ApprovalConflict, match="inputs changed"):
        approve_plan(isolated_session, plan.id, "demo-supervisor")

    isolated_session.refresh(plan)
    assert plan.status == "proposed"
    assert isolated_session.scalars(select(AuditEvent)).all() == []
