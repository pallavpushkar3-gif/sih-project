"""Real separate-connection approval and database invariant evidence."""

import os
import threading
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    Aircraft,
    Component,
    MaintenanceResource,
    MaintenanceTask,
    Plan,
    ResourceBooking,
    ResourceSlot,
)
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import planning_snapshot


@pytest.mark.integration
def test_postgres_competing_crew_bay_approvals_and_database_exclusion():
    url = os.environ.get("FLEET_DATABASE_URL", "")
    if not url.startswith("postgresql"):
        pytest.skip("Requires an isolated PostgreSQL verification database")
    engine = create_engine(url)
    prefix = f"resource-race-{uuid.uuid4().hex[:8]}"
    with Session(engine) as session:
        session.add(Aircraft(id=prefix, tail_number=prefix, label="resource verification"))
        session.flush()
        component = f"{prefix}-engine"
        session.add(
            Component(id=component, aircraft_id=prefix, serial_number=prefix, kind="engine")
        )
        for kind in ("crew", "bay"):
            session.add(
                MaintenanceResource(
                    id=f"{prefix}-{kind}",
                    label=kind,
                    kind=kind,
                    capabilities=["test-skill" if kind == "crew" else "engine"],
                    available=[[0, 14]],
                )
            )
        session.flush()
        for number in (1, 2):
            session.add(
                MaintenanceTask(
                    id=f"{prefix}-t{number}",
                    component_id=component,
                    title="exclusive resources",
                    duration_slots=1,
                    deadline_slot=14,
                    required_skill="test-skill",
                )
            )
        session.commit()
        snapshot = planning_snapshot(session)
        for number in (1, 2):
            session.add(
                Plan(
                    id=f"{prefix}-p{number}",
                    status="proposed",
                    solver_status="feasible",
                    input_version=snapshot["input_version"],
                    input_snapshot=snapshot["source"],
                    assignments=[
                        {
                            "task_id": f"{prefix}-t{number}",
                            "start": 0,
                            "end": 1,
                            "crew_id": f"{prefix}-crew",
                            "bay_id": f"{prefix}-bay",
                        }
                    ],
                )
            )
        session.commit()
    barrier = threading.Barrier(2)
    outcomes = []

    def attempt(number):
        with Session(engine) as session:
            barrier.wait(timeout=10)
            try:
                approve_plan(session, f"{prefix}-p{number}", "resource-test")
                outcomes.append("approved")
            except ApprovalConflict:
                session.rollback()
                outcomes.append("conflict")

    threads = [threading.Thread(target=attempt, args=(number,)) for number in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=15)
    assert all(not thread.is_alive() for thread in threads)
    assert sorted(outcomes) == ["approved", "conflict"]
    with Session(engine) as session:
        slots = session.scalars(
            select(ResourceSlot).where(ResourceSlot.resource_id == f"{prefix}-bay")
        ).all()
        assert len(slots) == 1
        original = slots[0]
        # Bypass all application prechecks: the database still rejects exclusive overlap.
        booking = ResourceBooking(
            id=f"{prefix}-manual",
            plan_id=f"{prefix}-p1",
            task_id=f"{prefix}-t2",
            resource_id=f"{prefix}-bay",
            unit=0,
            start_slot=0,
            end_slot=1,
        )
        session.add(booking)
        session.flush()
        session.add(
            ResourceSlot(
                resource_id=original.resource_id,
                booking_id=booking.id,
                unit=original.unit,
                slot=original.slot,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    engine.dispose()
