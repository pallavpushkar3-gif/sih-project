"""Work outcomes atomically consume or release reservations without changing history."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    AuditEvent,
    MaintenanceTask,
    Part,
    Plan,
    Reservation,
    WorkRecord,
)
from fleet_maintenance.services.approvals import ApprovalConflict


def update_work(
    session: Session,
    work_id: str,
    action: str,
    expected_version: int,
    actor: str,
    notes: str,
    *,
    commit: bool = True,
) -> WorkRecord:
    hint = session.get(WorkRecord, work_id)
    if hint is None:
        raise LookupError(work_id)
    plan = session.scalar(select(Plan).where(Plan.id == hint.plan_id).with_for_update())
    assert plan is not None
    work = session.scalar(
        select(WorkRecord)
        .where(WorkRecord.id == work_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    assert work is not None
    if work.version != expected_version:
        raise ApprovalConflict("Work version changed; reload before recording an outcome.")
    task = session.scalar(
        select(MaintenanceTask).where(MaintenanceTask.id == work.task_id).with_for_update()
    )
    assert task is not None
    if action == "start":
        if work.status != "approved":
            raise ApprovalConflict("Only approved work can start.")
        work.status = task.status = "in_progress"
        work.started_at = datetime.now(UTC)
    elif action in {"complete", "cancel"}:
        if work.status not in {"approved", "in_progress"}:
            raise ApprovalConflict("Work has already reached a terminal outcome.")
        if action == "cancel" and work.status == "in_progress":
            raise ApprovalConflict("Started work requires an explicit completion outcome.")
        if action == "complete" and work.status != "in_progress":
            raise ApprovalConflict("Start work before completing it.")
        if task.required_part_id and task.required_part_quantity:
            reservation = session.scalar(
                select(Reservation)
                .where(
                    Reservation.plan_id == work.plan_id,
                    Reservation.part_id == task.required_part_id,
                )
                .with_for_update()
            )
            if (
                reservation is None
                or reservation.status != "reserved"
                or reservation.quantity < task.required_part_quantity
            ):
                raise ApprovalConflict("The expected reservation is unavailable.")
            reservation.quantity -= task.required_part_quantity
            if reservation.quantity == 0:
                reservation.status = "closed"
            if action == "cancel":
                part = session.scalar(
                    select(Part).where(Part.id == task.required_part_id).with_for_update()
                )
                assert part is not None
                part.on_hand += task.required_part_quantity
                part.version += 1
            else:
                work.consumed_quantity = task.required_part_quantity
        work.status = "completed" if action == "complete" else "cancelled"
        task.status = "completed" if action == "complete" else "open"
        work.completed_at = datetime.now(UTC)
    else:
        raise ValueError("Unknown work action")
    work.notes = notes
    work.version += 1
    task.version += 1
    session.add(
        AuditEvent(
            actor=actor,
            action=f"work.{action}",
            subject_id=work.id,
            details={
                "version": work.version,
                "notes": notes,
                "consumed_quantity": work.consumed_quantity,
            },
        )
    )
    session.flush()
    states = set(
        session.scalars(select(WorkRecord.status).where(WorkRecord.plan_id == work.plan_id)).all()
    )
    if states <= {"completed", "cancelled"}:
        plan.status = (
            "completed"
            if states == {"completed"}
            else "cancelled"
            if states == {"cancelled"}
            else "closed"
        )
    elif "in_progress" in states:
        plan.status = "in_progress"
    if commit:
        session.commit()
    else:
        session.flush()
    return work
