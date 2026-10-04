"""Read-only inspection context from authoritative task and stock records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Component, MaintenanceTask, Part


def maintenance_context(session: Session, component_id: str) -> dict[str, object]:
    if session.get(Component, component_id) is None:
        raise LookupError(component_id)
    tasks = session.scalars(
        select(MaintenanceTask)
        .where(MaintenanceTask.component_id == component_id)
        .order_by(MaintenanceTask.id)
    ).all()
    rows = []
    for task in tasks:
        part = session.get(Part, task.required_part_id) if task.required_part_id else None
        rows.append(
            {
                "id": task.id,
                "title": task.title,
                "status": task.status,
                "mandatory": task.mandatory,
                "deadline_slot": task.deadline_slot,
                "duration_slots": task.duration_slots,
                "required_skill": task.required_skill,
                "part_id": task.required_part_id,
                "part_required": task.required_part_quantity,
                "part_available": None if part is None else part.on_hand,
                "version": task.version,
            }
        )
    return {"component_id": component_id, "slot_duration_hours": 8, "tasks": rows}


def plan_commitment(session: Session, plan_id: str) -> dict[str, object]:
    """Retained commitment rows; reading history never creates or releases stock."""
    from fleet_maintenance.persistence.models import Plan, Reservation, WorkRecord

    if session.get(Plan, plan_id) is None:
        raise LookupError(plan_id)
    reservations = session.scalars(
        select(Reservation).where(Reservation.plan_id == plan_id).order_by(Reservation.id)
    ).all()
    work = session.scalars(
        select(WorkRecord).where(WorkRecord.plan_id == plan_id).order_by(WorkRecord.id)
    ).all()
    return {
        "plan_id": plan_id,
        "reservations": [
            {"id": row.id, "part_id": row.part_id, "quantity": row.quantity, "status": row.status}
            for row in reservations
        ],
        "work": [
            {
                "id": row.id,
                "task_id": row.task_id,
                "status": row.status,
                "version": row.version,
                "consumed_quantity": row.consumed_quantity,
                "notes": row.notes,
                "started_at": row.started_at,
                "completed_at": row.completed_at,
            }
            for row in work
        ],
    }
