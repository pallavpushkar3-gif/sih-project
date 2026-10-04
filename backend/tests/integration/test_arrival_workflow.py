import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Part, PartArrival
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.arrivals import record_arrival, schedule_arrival
from fleet_maintenance.services.planning import planning_snapshot, propose_plan


def test_expected_receipt_and_replay_preserve_stock_and_proposal_versions(
    isolated_session: Session,
):
    part = isolated_session.get(Part, "part-filter")
    part.on_hand = 0
    isolated_session.commit()
    item = schedule_arrival(
        isolated_session,
        "delivery-1",
        part.id,
        1,
        4,
        part.version,
        "Synthetic test delivery",
        "demo-logistics",
    )
    version = part.version
    replay = schedule_arrival(
        isolated_session,
        "delivery-1",
        part.id,
        1,
        4,
        version - 1,
        "Synthetic test delivery",
        "demo-logistics",
    )
    assert replay.id == item.id and part.on_hand == 0 and part.version == version
    assert len(isolated_session.scalars(select(PartArrival)).all()) == 1
    snapshot = planning_snapshot(isolated_session)
    assert snapshot["source"]["part_arrivals"][0]["slot"] == 4
    plan = propose_plan(isolated_session)
    assert plan.status == "proposed"
    assert next(row for row in plan.assignments if row["task_id"] == "task-filter-02")["start"] >= 4
    with pytest.raises(ApprovalConflict, match="Awaiting received"):
        approve_plan(isolated_session, plan.id, "demo-supervisor")
    isolated_session.rollback()
    record_arrival(
        isolated_session, item.id, "receive", 1, "Actual labelled fixture receipt", "demo-logistics"
    )
    assert part.on_hand == 1
    receipt_version = part.version
    record_arrival(
        isolated_session, item.id, "receive", 1, "Actual labelled fixture receipt", "demo-logistics"
    )
    assert part.on_hand == 1 and part.version == receipt_version
    with pytest.raises(ApprovalConflict, match="inputs changed"):
        approve_plan(isolated_session, plan.id, "demo-supervisor")
    isolated_session.rollback()
    updated = propose_plan(isolated_session)
    assert updated.input_version != plan.input_version
    approve_plan(isolated_session, updated.id, "demo-supervisor")
    assert part.on_hand == 0


def test_cancelled_delivery_creates_no_stock_and_cannot_be_received(isolated_session: Session):
    part = isolated_session.get(Part, "part-kit")
    before = part.on_hand
    item = schedule_arrival(
        isolated_session,
        "delivery-cancel",
        part.id,
        2,
        6,
        part.version,
        "Synthetic shipment",
        "demo-logistics",
    )
    record_arrival(isolated_session, item.id, "cancel", 1, "No longer expected", "demo-logistics")
    assert part.on_hand == before
    with pytest.raises(ApprovalConflict, match="version/state"):
        record_arrival(isolated_session, item.id, "receive", 1, "Too late", "demo-logistics")


@pytest.mark.parametrize("action", ["quarantine", "reject"])
def test_unaccepted_receipts_never_create_usable_stock(isolated_session: Session, action: str):
    part = isolated_session.get(Part, "part-kit")
    before = part.on_hand
    item = schedule_arrival(
        isolated_session,
        "delivery-quality",
        part.id,
        2,
        6,
        part.version,
        "Synthetic shipment",
        "logistics",
    )
    record_arrival(isolated_session, item.id, action, 1, "Quality issue", "logistics")
    record_arrival(isolated_session, item.id, action, 1, "Quality issue", "logistics")
    assert part.on_hand == before
    assert not planning_snapshot(isolated_session)["source"]["part_arrivals"]
    with pytest.raises(ApprovalConflict):
        record_arrival(
            isolated_session, item.id, "receive", 2, "Cannot bypass quality", "logistics"
        )
