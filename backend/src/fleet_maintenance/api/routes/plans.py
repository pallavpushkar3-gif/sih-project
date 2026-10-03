from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_planner
from fleet_maintenance.domain.contracts.api import PlanResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Plan
from fleet_maintenance.services.approvals import ApprovalConflict, approve_plan
from fleet_maintenance.services.planning import propose_plan

router = APIRouter(prefix="/plans", tags=["plans"])


def serialize(p: Plan) -> dict[str, object]:
    return {
        "id": p.id,
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
def list_plans(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        serialize(p) for p in session.scalars(select(Plan).order_by(Plan.created_at.desc())).all()
    ]


@router.post("/proposals", response_model=PlanResponse)
def create_proposal(
    session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    return serialize(propose_plan(session))


@router.post("/{plan_id}/approve", response_model=PlanResponse)
def approve(
    plan_id: str, session: Session = Depends(get_session), actor: Actor = Depends(current_actor)
) -> dict[str, object]:
    require_planner(actor)
    try:
        return serialize(approve_plan(session, plan_id, actor.id))
    except LookupError:
        raise HTTPException(404, "Plan not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc
