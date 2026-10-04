"""Persist comparisons tied to the exact immutable plan calculation inputs."""

import hashlib
import json
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.planning import Assignment
from fleet_maintenance.persistence.models import Plan, Scenario, SimulationRun
from fleet_maintenance.science.simulation.plan_comparison import compare_plan
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.planning import restore_source


def plan_payload(plan: Plan) -> dict[str, object]:
    if plan.solver_status not in {"optimal", "feasible"} or not plan.assignments:
        raise ApprovalConflict("A usable saved plan is required for comparison")
    if not plan.input_snapshot.get("resources"):
        raise ApprovalConflict("This legacy plan has no resource snapshot; generate a fresh plan")
    data = {
        "plan_id": plan.id,
        "input_version": plan.input_version,
        "input_snapshot": plan.input_snapshot,
        "assignments": plan.assignments,
    }
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return {**data, "plan_sha256": digest}


def calculate(payload: dict[str, object]) -> dict[str, object]:
    source = restore_source({"source": payload["input_snapshot"]})
    assignments = tuple(
        Assignment(**cast(dict[str, Any], a))
        for a in cast(list[dict[str, object]], payload["assignments"])
    )
    # Existing booked work stays fixed and contributes to shared resource/exposure constraints.
    holds = tuple(
        Assignment(
            t.id,
            t.earliest,
            t.deadline,
            t.fixed_crew_id,
            t.fixed_bay_id,
            t.fixed_crew_unit,
            t.fixed_bay_unit,
        )
        for t in source.tasks
        if t.id.startswith("hold:")
    )
    return {
        **compare_plan(source, assignments + holds),
        "plan_id": payload["plan_id"],
        "plan_sha256": payload["plan_sha256"],
        "input_version": payload["input_version"],
        "input_snapshot": payload["input_snapshot"],
    }


def save_comparison(
    session: Session,
    payload: dict[str, object],
    result: dict[str, object],
    run_id: str,
) -> SimulationRun:
    # Serialize the per-plan scenario registration as well as result identity checks.
    plan = session.scalar(
        select(Plan)
        .where(Plan.id == str(payload["plan_id"]))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if plan is None or plan_payload(plan)["plan_sha256"] != payload["plan_sha256"]:
        raise ApprovalConflict("Plan calculation inputs changed after submission")
    previous = session.get(SimulationRun, run_id)
    if previous:
        return previous
    scenario_id = f"plan-case-{str(payload['plan_sha256'])[:32]}"
    scenario = session.get(Scenario, scenario_id)
    if scenario is None:
        session.add(Scenario(id=scenario_id, name=f"Actual plan {plan.id}", assumptions=payload))
        session.flush()
    first_case = cast(list[dict[str, Any]], result["cases"])[0]
    actual = first_case["actual"]
    record = SimulationRun(
        id=run_id,
        scenario_id=scenario_id,
        policy="actual-plan-v1",
        seed=26249,
        availability=actual["availability"],
        metrics=result,
    )
    session.add(record)
    session.flush()
    return record
