from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import (
    Actor,
    current_actor,
    require_planner,
    require_supervisor,
)
from fleet_maintenance.domain.contracts.api import JobResponse, PlanCommitmentResponse, PlanResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Plan
from fleet_maintenance.science.scheduling.solver import solve
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import planning_snapshot, propose_plan, restore_source

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/{plan_id}/comparison", response_model=JobResponse)
def compare_saved_plan(
    plan_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    from fleet_maintenance.api.routes.jobs import serialize as serialize_job
    from fleet_maintenance.services.jobs import submit_job
    from fleet_maintenance.services.plan_simulation import plan_payload

    require_planner(actor)
    plan = session.get(Plan, plan_id)
    if plan is None:
        raise HTTPException(404, "Plan not found")
    try:
        return serialize_job(
            submit_job(session, "plan_simulation", plan_payload(plan), owner=actor.id)
        )
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


def serialize(p: Plan) -> dict[str, object]:
    return {
        "id": p.id,
        "input_snapshot": p.input_snapshot,
        "objective": p.objective,
        "best_bound": p.best_bound,
        "parent_id": p.parent_id,
        "status": p.status,
        "solver_status": p.solver_status,
        "input_version": p.input_version,
        "assignments": p.assignments,
        "diagnostics": p.diagnostics,
        "created_at": p.created_at,
        "approved_at": p.approved_at,
        "approved_by": p.approved_by,
    }


@router.get("", response_model=list[PlanResponse])
def list_plans(
    session: Session = Depends(get_session), scope_component_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict[str, object]]:
    query = select(Plan).order_by(Plan.created_at.desc(), Plan.id.desc())
    if scope_component_id:
        query = query.where(
            Plan.input_snapshot["scope_component_id"].as_string() == scope_component_id
        )
    return [
        serialize(p) for p in session.scalars(query.offset(offset).limit(limit)).all()
    ]


@router.post("/proposals", response_model=PlanResponse)
def create_proposal(
    session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    try:
        snapshot = planning_snapshot(session)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    session.rollback()
    result = solve(restore_source(snapshot))
    return serialize(propose_plan(session, snapshot=snapshot, computed_result=result))


@router.post("/{plan_id}/approve", response_model=PlanResponse)
def approve(
    plan_id: str, session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_supervisor(actor)
    try:
        return serialize(approve_plan(session, plan_id, actor.id))
    except LookupError:
        raise HTTPException(404, "Plan not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/{plan_id}/revisions", response_model=PlanResponse)
def revise(
    plan_id: str, session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    parent = session.get(Plan, plan_id)
    if parent is None:
        raise HTTPException(404, "Plan not found")
    scope_value = parent.input_snapshot.get("scope_component_id")
    try:
        snapshot = planning_snapshot(session, str(scope_value) if scope_value else None)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if "advisory" in parent.input_snapshot:
        snapshot["advisory"] = parent.input_snapshot["advisory"]
    session.rollback()
    result = solve(restore_source(snapshot))
    proposal = propose_plan(session, commit=False, snapshot=snapshot, computed_result=result)
    proposal.parent_id = plan_id
    session.commit()
    return serialize(proposal)


@router.post("/{plan_id}/rejection", response_model=PlanResponse)
def reject(
    plan_id: str, session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    from fleet_maintenance.persistence.models import AuditEvent

    require_supervisor(actor)
    plan = session.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if plan is None:
        raise HTTPException(404, "Plan not found")
    if plan.status not in {"proposed", "rejected"}:
        raise HTTPException(409, "Only proposed plans can be rejected")
    if plan.status != "rejected":
        plan.status = "rejected"
        session.add(
            AuditEvent(
                actor=actor.id,
                action="plan.rejected",
                subject_id=plan.id,
                details={"input_version": plan.input_version},
            )
        )
        session.commit()
    return serialize(plan)


@router.get("/{plan_id}/commitment", response_model=PlanCommitmentResponse)
def commitment(plan_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    from fleet_maintenance.services.inspection import plan_commitment

    try:
        return plan_commitment(session, plan_id)
    except LookupError:
        raise HTTPException(404, "Plan not found") from None
