from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import (
    Aircraft,
    Alert,
    Assessment,
    Component,
    MaintenanceTask,
    Observation,
    Part,
    Scenario,
    User,
)


def seed_demo(session: Session) -> bool:
    if session.scalar(select(Aircraft.id).limit(1)):
        return False
    session.add_all(
        [
            User(id="demo-planner", display_name="Demo Planner", role="planner"),
            User(id="demo-supervisor", display_name="Demo Supervisor", role="supervisor"),
            Aircraft(
                id="ac-syn-01", tail_number="SYN-001", label="Synthetic demonstrator aircraft 1"
            ),
            Aircraft(
                id="ac-syn-02", tail_number="SYN-002", label="Synthetic demonstrator aircraft 2"
            ),
            Component(
                id="cmp-eng-01",
                aircraft_id="ac-syn-01",
                serial_number="ENG-SYN-001",
                kind="engine",
                current_cycle=74,
            ),
            Component(
                id="cmp-eng-02",
                aircraft_id="ac-syn-02",
                serial_number="ENG-SYN-002",
                kind="engine",
                current_cycle=61,
            ),
            Part(id="part-filter", name="Synthetic engine filter", on_hand=1, lead_time_slots=4),
            Part(id="part-kit", name="Synthetic inspection kit", on_hand=2, lead_time_slots=2),
            MaintenanceTask(
                id="task-inspect-01",
                component_id="cmp-eng-01",
                title="Mandatory engine inspection",
                duration_slots=3,
                deadline_slot=8,
                required_skill="engine",
                required_part_id="part-kit",
                required_part_quantity=1,
            ),
            MaintenanceTask(
                id="task-filter-02",
                component_id="cmp-eng-02",
                title="Replace demonstration filter",
                duration_slots=2,
                earliest_slot=2,
                deadline_slot=10,
                required_skill="engine",
                required_part_id="part-filter",
                required_part_quantity=1,
            ),
            Assessment(
                id="asm-unavailable-01",
                component_id="cmp-eng-01",
                state="unavailable",
                estimate_cycles=None,
                lower_cycles=None,
                upper_cycles=None,
                model_version=None,
                input_version="synthetic-history-v1",
                quality_findings=[
                    {
                        "code": "model_unavailable",
                        "severity": "warning",
                        "message": "No evaluated model artifact is installed.",
                    }
                ],
            ),
            Alert(
                id="alert-quality-01",
                component_id="cmp-eng-01",
                state="data_unavailable",
                reason="Prediction unavailable; mandatory task remains active.",
                policy_version="demo-v1",
                assessment_id="asm-unavailable-01",
            ),
            Scenario(
                id="scenario-baseline",
                name="Synthetic baseline capacity",
                assumptions={
                    "horizon_hours": 24,
                    "aircraft_count": 2,
                    "maintenance_capacity": 1,
                    "maintenance_events": [[2, 3], [4, 2]],
                    "label": "synthetic",
                },
            ),
            Scenario(
                id="scenario-extra-bay",
                name="Synthetic additional capacity",
                assumptions={
                    "horizon_hours": 24,
                    "aircraft_count": 2,
                    "maintenance_capacity": 2,
                    "maintenance_events": [[2, 3], [4, 2]],
                    "label": "synthetic",
                },
            ),
        ]
    )
    session.flush()
    for component_id, base_cycle in (("cmp-eng-01", 70), ("cmp-eng-02", 57)):
        for offset in range(5):
            session.add(
                Observation(
                    component_id=component_id,
                    cycle=base_cycle + offset,
                    sensor="sensor_2",
                    value=642.0 + offset * 0.7,
                    unit="unknown_dataset_unit",
                    source_version="synthetic-demo-v1",
                )
            )
    session.commit()
    return True


def fleet_summary(session: Session) -> list[dict[str, object]]:
    aircraft = session.scalars(select(Aircraft).order_by(Aircraft.tail_number)).all()
    components = session.scalars(select(Component)).all()
    tasks = session.scalars(select(MaintenanceTask)).all()
    result = []
    for item in aircraft:
        owned = [c for c in components if c.aircraft_id == item.id]
        owned_ids = {c.id for c in owned}
        result.append(
            {
                "id": item.id,
                "tail_number": item.tail_number,
                "label": item.label,
                "provenance": item.provenance,
                "component_ids": sorted(c.id for c in owned),
                "components": len(owned),
                "open_tasks": sum(
                    t.status == "open" and t.component_id in owned_ids for t in tasks
                ),
            }
        )
    return result


def component_detail(session: Session, component_id: str) -> dict[str, object] | None:
    component = session.get(Component, component_id)
    if component is None:
        return None
    observations = session.scalars(
        select(Observation)
        .where(Observation.component_id == component_id)
        .order_by(Observation.cycle)
    ).all()
    assessment = session.scalars(
        select(Assessment)
        .where(Assessment.component_id == component_id)
        .order_by(Assessment.created_at.desc())
    ).first()
    return {
        "id": component.id,
        "aircraft_id": component.aircraft_id,
        "serial_number": component.serial_number,
        "kind": component.kind,
        "status": component.status,
        "current_cycle": component.current_cycle,
        "observations": [
            {
                "cycle": o.cycle,
                "sensor": o.sensor,
                "value": o.value,
                "unit": o.unit,
                "source_version": o.source_version,
            }
            for o in observations
        ],
        "assessment": None
        if assessment is None
        else {
            "id": assessment.id,
            "state": assessment.state,
            "estimate_cycles": assessment.estimate_cycles,
            "lower_cycles": assessment.lower_cycles,
            "upper_cycles": assessment.upper_cycles,
            "model_version": assessment.model_version,
            "input_version": assessment.input_version,
            "quality_findings": assessment.quality_findings,
        },
    }
