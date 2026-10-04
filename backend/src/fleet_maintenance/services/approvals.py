import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    AuditEvent,
    MaintenanceTask,
    Part,
    PartArrival,
    Plan,
    Reservation,
    WorkRecord,
)
from fleet_maintenance.science.scheduling.constraints import validate_input, validate_result
from fleet_maintenance.science.scheduling.formulation import (
    Assignment,
    PartArrivalInput,
    PlanningInput,
    PlanningResult,
    TaskInput,
)
from fleet_maintenance.services.planning import committed_tasks, current_input_version


class ApprovalConflict(Exception):
    pass


def approve_plan(session: Session, plan_id: str, actor: str) -> Plan:
    plan = session.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if plan is None:
        raise LookupError(plan_id)
    if plan.approved_at is not None:
        return plan
    if plan.status != "proposed":
        raise ApprovalConflict("Only a usable proposed plan can be approved.")
    tasks = list(
        session.scalars(
            select(MaintenanceTask)
            .where(MaintenanceTask.status == "open")
            .order_by(MaintenanceTask.id)
            .with_for_update()
        ).all()
    )
    parts = list(session.scalars(select(Part).order_by(Part.id).with_for_update()).all())
    if current_input_version(tasks, parts) != plan.input_version:
        raise ApprovalConflict("Plan inputs changed; generate a new proposal.")
    part_by_id = {p.id: p for p in parts}
    task_by_id = {t.id: t for t in tasks}
    assigned_ids = [str(a["task_id"]) for a in plan.assignments]
    if not assigned_ids or len(set(assigned_ids)) != len(assigned_ids):
        raise ApprovalConflict("Plan must have unique task assignments.")
    if any(task_id not in task_by_id for task_id in assigned_ids):
        raise ApprovalConflict("Plan contains unavailable tasks.")
    selected = [task_by_id[task_id] for task_id in assigned_ids]
    holds = committed_tasks(session)
    source = PlanningInput(
        14,
        tuple(
            TaskInput(
                t.id,
                t.duration_slots,
                t.earliest_slot,
                t.deadline_slot,
                t.required_skill,
                t.required_part_id,
                t.required_part_quantity,
                t.fixed_start,
                tuple(t.predecessors),
                component_id=t.component_id,
                group_id=t.grouping_key,
            )
            for t in selected
        )
        + holds,
        {"engine": 1},
        {p.id: p.on_hand for p in parts},
        tuple(
            PartArrivalInput(a.part_id, a.arrival_slot, a.quantity)
            for a in session.scalars(
                select(PartArrival).where(PartArrival.status == "expected").order_by(PartArrival.id)
            ).all()
        ),
    )
    result = PlanningResult(
        "feasible",
        tuple(
            Assignment(str(a["task_id"]), int(str(a["start"])), int(str(a["end"])))
            for a in plan.assignments
        )
        + tuple(Assignment(t.id, t.earliest, t.deadline) for t in holds),
    )
    violations = validate_input(source) + validate_result(source, result)
    if violations:
        raise ApprovalConflict("Plan violates current hard constraints: " + "; ".join(violations))
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
            raise ApprovalConflict(
                f"Awaiting received stock for {part_id}; "
                "receive deliveries and regenerate the proposal."
            )
        part.on_hand -= quantity
        part.version += 1
        session.add(Reservation(plan_id=plan.id, part_id=part_id, quantity=quantity))
    for task_id in assigned_ids:
        task = task_by_id[task_id]
        task.status = "approved"
        task.version += 1
        session.add(
            WorkRecord(
                id=f"work-{uuid.uuid5(uuid.NAMESPACE_URL, plan.id + ':' + task_id).hex}",
                plan_id=plan.id,
                task_id=task_id,
            )
        )
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
