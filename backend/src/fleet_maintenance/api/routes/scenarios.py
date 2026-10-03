from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_planner
from fleet_maintenance.domain.contracts.api import ScenarioResponse, SimulationRunResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Scenario, SimulationRun
from fleet_maintenance.services.scenarios import run_saved_scenario

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
def scenarios(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {
            "id": s.id,
            "name": s.name,
            "version": s.version,
            "assumptions": s.assumptions,
            "provenance": s.provenance,
        }
        for s in session.scalars(select(Scenario)).all()
    ]


@router.post("/{scenario_id}/runs", response_model=SimulationRunResponse)
def run(
    scenario_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_planner(actor)
    try:
        r = run_saved_scenario(session, scenario_id)
    except LookupError:
        raise HTTPException(404, "Scenario not found") from None
    return {
        "id": r.id,
        "scenario_id": r.scenario_id,
        "policy": r.policy,
        "seed": r.seed,
        "availability": r.availability,
        "metrics": r.metrics,
    }


@router.get("/runs/all", response_model=list[SimulationRunResponse])
def runs(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        {
            "id": r.id,
            "scenario_id": r.scenario_id,
            "policy": r.policy,
            "seed": r.seed,
            "availability": r.availability,
            "metrics": r.metrics,
        }
        for r in session.scalars(select(SimulationRun)).all()
    ]
