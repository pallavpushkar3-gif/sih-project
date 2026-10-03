from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    AuditEvent,
    MaintenanceTask,
    Part,
    Plan,
    Reservation,
)
from fleet_maintenance.services.planning import current_input_version


class ApprovalConflict(Exception):
    pass


def approve_plan(session: Session, plan_id: str, actor: str) -> Plan:
    plan = session.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if plan is None:
        raise LookupError(plan_id)
    if plan.status == "approved":
        return plan
    if plan.status != "proposed":
        raise ApprovalConflict("Only a usable proposed plan can be approved.")
    tasks = list(
        session.scalars(
            select(MaintenanceTask).where(MaintenanceTask.status == "open").with_for_update()
        ).all()
    )
    parts = list(session.scalars(select(Part).with_for_update()).all())
    if current_input_version(tasks, parts) != plan.input_version:
        raise ApprovalConflict("Plan inputs changed; generate a new proposal.")
    part_by_id = {p.id: p for p in parts}
    task_by_id = {t.id: t for t in tasks}
    required: dict[str, int] = {}
    for assignment in plan.assignments:
        task = task_by_id.get(str(assignment["task_id"]))
        if task and task.required_part_id:
            required[task.required_part_id] = (
                required.get(task.required_part_id, 0) + task.required_part_quantity
            )
    for part_id, quantity in required.items():
        part = part_by_id[part_id]
        if part.on_hand < quantity:
            raise ApprovalConflict(f"Insufficient stock for {part_id}.")
        part.on_hand -= quantity
        part.version += 1
        session.add(Reservation(plan_id=plan.id, part_id=part_id, quantity=quantity))
    plan.status = "approved"
    plan.approved_at = datetime.now(UTC)
    plan.approved_by = actor
    session.add(
        AuditEvent(
            actor=actor,
            action="plan.approved",
            subject_id=plan.id,
            details={"input_version": plan.input_version},
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ApprovalConflict("Approval already committed or conflicted.") from exc
    session.refresh(plan)
    return plan
