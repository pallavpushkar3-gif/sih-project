import hashlib
import json
import uuid
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    MaintenanceTask,
    Part,
    PartArrival,
    Plan,
    WorkRecord,
)
from fleet_maintenance.science.scheduling.formulation import (
    PartArrivalInput,
    PlanningInput,
    PlanningResult,
    TaskInput,
)
from fleet_maintenance.science.scheduling.solver import solve


def current_input_version(tasks: list[MaintenanceTask], parts: list[Part]) -> str:
    payload = {
        "tasks": [
            (
                t.id,
                t.version,
                t.status,
                t.duration_slots,
                t.earliest_slot,
                t.deadline_slot,
                t.required_skill,
                t.required_part_id,
                t.required_part_quantity,
                t.fixed_start,
                t.predecessors,
                t.component_id,
                t.grouping_key,
                t.mandatory,
            )
            for t in sorted(tasks, key=lambda x: x.id)
        ],
        "parts": [(p.id, p.version, p.on_hand) for p in sorted(parts, key=lambda x: x.id)],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def planning_snapshot(session: Session) -> dict[str, object]:
    tasks = list(
        session.scalars(
            select(MaintenanceTask)
            .where(MaintenanceTask.status == "open")
            .order_by(MaintenanceTask.id)
        ).all()
    )
    parts = list(session.scalars(select(Part).order_by(Part.id)).all())
    source = PlanningInput(
        horizon=14,
        tasks=tuple(
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
            for t in tasks
        )
        + committed_tasks(session),
        skill_capacity={"engine": 1},
        part_stock={p.id: p.on_hand for p in parts},
        part_arrivals=tuple(
            PartArrivalInput(a.part_id, a.arrival_slot, a.quantity)
            for a in session.scalars(
                select(PartArrival).where(PartArrival.status == "expected").order_by(PartArrival.id)
            ).all()
        ),
    )
    return {"source": asdict(source), "input_version": current_input_version(tasks, parts)}


def committed_tasks(session: Session) -> tuple[TaskInput, ...]:
    rows = session.execute(
        select(WorkRecord, MaintenanceTask, Plan)
        .join(MaintenanceTask, MaintenanceTask.id == WorkRecord.task_id)
        .join(Plan, Plan.id == WorkRecord.plan_id)
        .where(WorkRecord.status.in_(["approved", "in_progress"]))
    ).all()
    tasks = []
    for work, task, plan in rows:
        assignment = next(a for a in plan.assignments if a["task_id"] == task.id)
        start, end = int(str(assignment["start"])), int(str(assignment["end"]))
        tasks.append(
            TaskInput(
                f"hold:{work.id}", end - start, start, end, task.required_skill, fixed_start=start
            )
        )
    return tuple(tasks)


def restore_source(snapshot: dict[str, object]) -> PlanningInput:
    from typing import Any, cast

    values = cast(dict[str, Any], snapshot["source"])
    return PlanningInput(
        horizon=values["horizon"],
        tasks=tuple(TaskInput(**row) for row in values["tasks"]),
        skill_capacity=values["skill_capacity"],
        part_stock=values["part_stock"],
        part_arrivals=tuple(PartArrivalInput(**row) for row in values.get("part_arrivals", [])),
    )


def propose_plan(
    session: Session,
    plan_id: str | None = None,
    *,
    commit: bool = True,
    snapshot: dict[str, object] | None = None,
    computed_result: PlanningResult | None = None,
) -> Plan:
    if plan_id is not None:
        existing = session.get(Plan, plan_id)
        if existing is not None:
            return existing
    snapshot = snapshot or planning_snapshot(session)
    source = restore_source(snapshot)
    result = computed_result if computed_result is not None else solve(source)
    plan = Plan(
        id=plan_id or f"plan-{uuid.uuid4().hex[:10]}",
        status="proposed" if result.status in {"optimal", "feasible"} else result.status,
        solver_status=result.status,
        input_version=str(snapshot["input_version"]),
        input_snapshot=asdict(source),
        objective=result.objective,
        best_bound=result.best_bound,
        assignments=[
            {"task_id": a.task_id, "start": a.start, "end": a.end}
            for a in result.assignments
            if not a.task_id.startswith("hold:")
        ],
        diagnostics=list(result.diagnostics)
        + (
            [
                "Expected deliveries are assumptions; approval requires "
                "received stock and a current proposal."
            ]
            if source.part_arrivals
            else []
        ),
    )
    session.add(plan)
    if commit:
        session.commit()
        session.refresh(plan)
    else:
        session.flush()
    return plan
