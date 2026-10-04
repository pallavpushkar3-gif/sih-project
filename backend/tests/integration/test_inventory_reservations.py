import os
import threading
import uuid

import pytest
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from fleet_maintenance.api.routes.inventory import inventory
from fleet_maintenance.persistence.models import (
    Aircraft,
    AuditEvent,
    Component,
    MaintenanceTask,
    Part,
    Plan,
    Reservation,
    WorkRecord,
)
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import current_input_version, propose_plan


def test_approval_reserves_exact_stock_once(isolated_session: Session):
    plan = propose_plan(isolated_session)
    before = {part.id: part.on_hand for part in isolated_session.scalars(select(Part)).all()}

    approve_plan(isolated_session, plan.id, "demo-supervisor")
    after_first = {part.id: part.on_hand for part in isolated_session.scalars(select(Part)).all()}
    reservation_count = isolated_session.scalar(select(func.count(Reservation.id)))

    approve_plan(isolated_session, plan.id, "demo-supervisor")
    after_retry = {part.id: part.on_hand for part in isolated_session.scalars(select(Part)).all()}

    assert before["part-kit"] - after_first["part-kit"] == 1
    assert before["part-filter"] - after_first["part-filter"] == 1
    assert reservation_count == 2
    assert after_retry == after_first
    assert isolated_session.scalar(select(func.count(Reservation.id))) == 2


def test_inventory_reports_physical_stock_and_free_stock_after_approval(
    isolated_session: Session,
):
    before = {item["id"]: item for item in inventory(isolated_session)}
    plan = propose_plan(isolated_session)
    approve_plan(isolated_session, plan.id, "demo-supervisor")
    after = {item["id"]: item for item in inventory(isolated_session)}

    for part_id in ("part-kit", "part-filter"):
        assert after[part_id]["on_hand"] == before[part_id]["on_hand"]
        assert after[part_id]["reserved"] == 1
        part = isolated_session.get(Part, part_id)
        assert part is not None
        assert after[part_id]["on_hand"] - after[part_id]["reserved"] == part.on_hand


@pytest.mark.integration
def test_postgres_concurrent_approvals_cannot_double_reserve_stock():
    database_url = os.environ.get("FLEET_DATABASE_URL", "")
    if not database_url.startswith("postgresql"):
        pytest.skip("PostgreSQL is required for row-lock concurrency evidence.")

    engine = create_engine(database_url, pool_pre_ping=True)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid.uuid4().hex[:10]
    aircraft_id = f"ac-race-{suffix}"
    component_id = f"cmp-race-{suffix}"
    part_id = f"part-race-{suffix}"
    task_id = f"task-race-{suffix}"
    plan_ids = (f"plan-race-a-{suffix}", f"plan-race-b-{suffix}")
    try:
        with sessions.begin() as session:
            session.add(Aircraft(id=aircraft_id, tail_number=f"RACE-{suffix}", label="race test"))
            session.flush()
            session.add(
                Component(
                    id=component_id,
                    aircraft_id=aircraft_id,
                    serial_number=f"RACE-ENG-{suffix}",
                    kind="engine",
                )
            )
            session.add(Part(id=part_id, name="race part", on_hand=1))
            session.flush()
            session.add(
                MaintenanceTask(
                    id=task_id,
                    component_id=component_id,
                    title="race task",
                    duration_slots=1,
                    deadline_slot=5,
                    required_skill="engine",
                    required_part_id=part_id,
                    required_part_quantity=1,
                )
            )
        with sessions() as session:
            tasks = list(
                session.scalars(
                    select(MaintenanceTask).where(MaintenanceTask.status == "open")
                ).all()
            )
            parts = list(session.scalars(select(Part)).all())
            version = current_input_version(tasks, parts)
            session.add_all(
                [
                    Plan(
                        id=plan_id,
                        status="proposed",
                        solver_status="feasible",
                        input_version=version,
                        assignments=[{"task_id": task_id, "start": 0, "end": 1}],
                    )
                    for plan_id in plan_ids
                ]
            )
            session.commit()

        barrier = threading.Barrier(2)
        outcomes: list[str] = []
        outcome_lock = threading.Lock()

        def attempt(plan_id: str) -> None:
            with sessions() as session:
                barrier.wait()
                try:
                    approve_plan(session, plan_id, "race-supervisor")
                    outcome = "approved"
                except ApprovalConflict:
                    outcome = "conflict"
                with outcome_lock:
                    outcomes.append(outcome)

        threads = [threading.Thread(target=attempt, args=(plan_id,)) for plan_id in plan_ids]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        assert all(not thread.is_alive() for thread in threads)
        assert sorted(outcomes) == ["approved", "conflict"]

        with sessions() as session:
            part = session.get(Part, part_id)
            assert part is not None and part.on_hand == 0
            count = session.scalar(
                select(func.count(Reservation.id)).where(Reservation.part_id == part_id)
            )
            assert count == 1
    finally:
        with sessions.begin() as session:
            session.execute(delete(WorkRecord).where(WorkRecord.plan_id.in_(plan_ids)))
            session.execute(delete(Reservation).where(Reservation.plan_id.in_(plan_ids)))
            session.execute(delete(AuditEvent).where(AuditEvent.subject_id.in_(plan_ids)))
            session.execute(delete(Plan).where(Plan.id.in_(plan_ids)))
            session.execute(delete(MaintenanceTask).where(MaintenanceTask.id == task_id))
            session.execute(delete(Part).where(Part.id == part_id))
            session.execute(delete(Component).where(Component.id == component_id))
            session.execute(delete(Aircraft).where(Aircraft.id == aircraft_id))
        engine.dispose()
