import uuid
from typing import cast

from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import Scenario, SimulationRun
from fleet_maintenance.science.simulation.environment import ScenarioInput, SimulationResult
from fleet_maintenance.science.simulation.replications import run_scenario


def run_saved_scenario(
    session: Session,
    scenario_id: str,
    policy: str = "configured",
    run_id: str | None = None,
    *,
    commit: bool = True,
    computed_result: SimulationResult | None = None,
) -> SimulationRun:
    if run_id is not None:
        existing = session.get(SimulationRun, run_id)
        if existing is not None:
            return existing
    scenario = session.get(Scenario, scenario_id)
    if scenario is None:
        raise LookupError(scenario_id)
    values = scenario.assumptions
    result = (
        computed_result if computed_result is not None else run_scenario(scenario_source(values))
    )
    record = SimulationRun(
        id=run_id or f"sim-{uuid.uuid4().hex[:10]}",
        scenario_id=scenario.id,
        policy=policy,
        seed=result.seed,
        availability=result.availability,
        metrics={
            "downtime_aircraft_hours": result.downtime_aircraft_hours,
            "queue_wait_hours": result.queue_wait_hours,
            "part_wait_hours": result.part_wait_hours,
            "completed_events": result.completed_events,
            "label": "simulated projection",
            "scenario_version": scenario.version,
            "assumptions": values,
        },
    )
    session.add(record)
    if commit:
        session.commit()
        session.refresh(record)
    else:
        session.flush()
    return record


def scenario_source(values: dict[str, object]) -> ScenarioInput:
    horizon = values.get("horizon_hours")
    aircraft_count = values.get("aircraft_count")
    capacity = values.get("maintenance_capacity")
    events = values.get("maintenance_events")
    if not isinstance(horizon, (int, float)) or isinstance(horizon, bool):
        raise ValueError("Scenario horizon_hours must be numeric.")
    if not isinstance(aircraft_count, int) or isinstance(aircraft_count, bool):
        raise ValueError("Scenario aircraft_count must be an integer.")
    if not isinstance(capacity, int) or isinstance(capacity, bool):
        raise ValueError("Scenario maintenance_capacity must be an integer.")
    if not isinstance(events, list):
        raise ValueError("Scenario maintenance_events must be a list.")
    event_rows = cast(list[object], events)
    parsed_events: list[tuple[float, float]] = []
    for event in event_rows:
        if not isinstance(event, list) or len(event) != 2:
            raise ValueError("Each maintenance event must contain arrival and duration.")
        arrival, duration = event
        if (
            isinstance(arrival, bool)
            or not isinstance(arrival, (int, float))
            or isinstance(duration, bool)
            or not isinstance(duration, (int, float))
        ):
            raise ValueError("Maintenance event values must be numeric.")
        parsed_events.append((float(arrival), float(duration)))
    part_available = values.get("part_available_hours", 0.0)
    if isinstance(part_available, bool) or not isinstance(part_available, (int, float)):
        raise ValueError("Part availability must be numeric hours")
    return ScenarioInput(
        float(horizon),
        aircraft_count,
        capacity,
        tuple(parsed_events),
        float(part_available),
    )
