import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import MaintenanceResource, ResourceBooking, ResourceSlot
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import propose_plan
from fleet_maintenance.services.reservations import update_work


def test_resource_change_invalidates_proposal(isolated_session: Session):
    plan = propose_plan(isolated_session)
    crew = isolated_session.get(MaintenanceResource, "demo-crew")
    assert crew
    crew.available = [[4, 14]]
    crew.version += 1
    isolated_session.commit()
    with pytest.raises(ApprovalConflict, match="inputs changed"):
        approve_plan(isolated_session, plan.id, "supervisor")
    assert isolated_session.scalar(select(func.count(ResourceSlot.id))) == 0


def test_bookings_commit_and_release_with_work(isolated_session: Session):
    plan = propose_plan(isolated_session)
    approve_plan(isolated_session, plan.id, "supervisor")
    before = isolated_session.scalar(select(func.count(ResourceSlot.id)))
    assert before == sum(2 * (a["end"] - a["start"]) for a in plan.assignments)
    approve_plan(isolated_session, plan.id, "supervisor")
    assert isolated_session.scalar(select(func.count(ResourceSlot.id))) == before
    from fleet_maintenance.persistence.models import WorkRecord

    work = isolated_session.scalar(select(WorkRecord).where(WorkRecord.plan_id == plan.id))
    assert work
    update_work(isolated_session, work.id, "cancel", 1, "supervisor", "Cancel before starting")
    bookings = isolated_session.scalars(
        select(ResourceBooking).where(ResourceBooking.task_id == work.task_id)
    ).all()
    assert all(booking.status == "cancelled" for booking in bookings)
    assert isolated_session.scalar(select(func.count(ResourceSlot.id))) < before
