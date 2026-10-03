import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import MaintenanceTask, Part, Plan
from fleet_maintenance.science.scheduling.formulation import PlanningInput, TaskInput
from fleet_maintenance.science.scheduling.solver import solve


def current_input_version(tasks: list[MaintenanceTask], parts: list[Part]) -> str:
    payload = {
        "tasks": [(t.id, t.version, t.status) for t in sorted(tasks, key=lambda x: x.id)],
        "parts": [(p.id, p.version, p.on_hand) for p in sorted(parts, key=lambda x: x.id)],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def propose_plan(session: Session, plan_id: str | None = None) -> Plan:
    if plan_id is not None:
        existing = session.get(Plan, plan_id)
        if existing is not None:
            return existing
    tasks = list(
        session.scalars(select(MaintenanceTask).where(MaintenanceTask.status == "open")).all()
    )
    parts = list(session.scalars(select(Part)).all())
    stock = {p.id: p.on_hand for p in parts}
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
            )
            for t in tasks
        ),
        skill_capacity={"engine": 1},
        part_stock=stock,
    )
    result = solve(source)
    plan = Plan(
        id=plan_id or f"plan-{uuid.uuid4().hex[:10]}",
        status="proposed" if result.status in {"optimal", "feasible"} else result.status,
        solver_status=result.status,
        input_version=current_input_version(tasks, parts),
        assignments=[
            {"task_id": a.task_id, "start": a.start, "end": a.end} for a in result.assignments
        ],
        diagnostics=list(result.diagnostics),
    )
    session.add(plan)
    session.commit()
    session.refresh(plan)
    return plan
