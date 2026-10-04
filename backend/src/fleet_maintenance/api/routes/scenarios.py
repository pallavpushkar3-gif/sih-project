from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, FiniteFloat, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor, require_planner
from fleet_maintenance.domain.contracts.api import ScenarioResponse, SimulationRunResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Scenario, SimulationRun
from fleet_maintenance.science.simulation.replications import run_scenario
from fleet_maintenance.services.scenarios import run_saved_scenario, scenario_source

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
        if not s.assumptions.get("customer_trial") and not s.assumptions.get("plan_sha256")
    ]


@router.post("/{scenario_id}/runs", response_model=SimulationRunResponse)
def run(
    scenario_id: str,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    require_planner(actor)
    try:
        scenario = session.get(Scenario, scenario_id)
        if scenario is None:
            raise LookupError(scenario_id)
        values = dict(scenario.assumptions)
        version = scenario.version
        session.rollback()
        result = run_scenario(scenario_source(values))
        current = session.get(Scenario, scenario_id)
        if current is None or current.version != version or current.assumptions != values:
            raise HTTPException(409, "Scenario changed during calculation")
        r = run_saved_scenario(session, scenario_id, computed_result=result)
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
def runs(
    session: Session = Depends(get_session),
    plan_id: str | None = None,
    scenario_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict[str, object]]:
    query = select(SimulationRun).order_by(
        SimulationRun.created_at.desc().nulls_last(), SimulationRun.id.desc()
    )
    if plan_id:
        query = query.where(SimulationRun.metrics["plan_id"].as_string() == plan_id)
    if scenario_id:
        query = query.where(SimulationRun.scenario_id == scenario_id)
    return [
        {
            "id": r.id,
            "scenario_id": r.scenario_id,
            "policy": r.policy,
            "seed": r.seed,
            "availability": r.availability,
            "metrics": r.metrics,
        }
        for r in session.scalars(query.offset(offset).limit(limit)).all()
    ]


class ScenarioRevision(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    expected_version: int = Field(strict=True, ge=1)
    horizon_hours: FiniteFloat = Field(gt=0, le=8760)
    aircraft_count: int = Field(strict=True, ge=1, le=10000)
    maintenance_capacity: int = Field(strict=True, ge=1, le=10000)
    part_available_hours: FiniteFloat = Field(default=0.0, ge=0)
    maintenance_events: list[tuple[FiniteFloat, FiniteFloat]] = Field(max_length=10000)

    @model_validator(mode="after")
    def validate_events(self) -> "ScenarioRevision":
        if self.part_available_hours >= self.horizon_hours:
            raise ValueError("Part availability must precede the horizon")
        if len(self.maintenance_events) > self.aircraft_count:
            raise ValueError("Each event represents a separate aircraft in this demonstrator")
        if any(
            arrival < 0 or arrival >= self.horizon_hours or duration <= 0
            for arrival, duration in self.maintenance_events
        ):
            raise ValueError("Events require valid arrivals and positive durations")
        return self


@router.post("/{scenario_id}/revisions", response_model=ScenarioResponse)
def revision(
    scenario_id: str,
    body: ScenarioRevision,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    import uuid

    from fleet_maintenance.persistence.models import AuditEvent

    require_planner(actor)
    parent = session.get(Scenario, scenario_id)
    if parent is None:
        raise HTTPException(404, "Scenario not found")
    if parent.version != body.expected_version:
        raise HTTPException(409, "Scenario version changed")
    values = body.model_dump(mode="json", exclude={"name", "expected_version"})
    values.update({"label": "synthetic", "parent_scenario_id": scenario_id})
    item = Scenario(
        id=f"scenario-{uuid.uuid4().hex}",
        name=body.name,
        version=parent.version + 1,
        assumptions=values,
        provenance="synthetic",
    )
    session.add(item)
    session.add(
        AuditEvent(
            actor=actor.id,
            action="scenario.revised",
            subject_id=item.id,
            details={"parent_id": scenario_id, "version": item.version},
        )
    )
    session.commit()
    return {
        "id": item.id,
        "name": item.name,
        "version": item.version,
        "assumptions": item.assumptions,
        "provenance": item.provenance,
    }
