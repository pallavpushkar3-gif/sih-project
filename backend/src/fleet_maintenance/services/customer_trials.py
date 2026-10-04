"""Local sales trials compose the real ingestion, jobs, planning and work services."""

import hashlib
import json
import math
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.demo import (
    HistoryImport,
    TrialCatalogResponse,
    TrialRequest,
    TrialResponse,
)
from fleet_maintenance.domain.contracts.records import WorkspaceFixture
from fleet_maintenance.persistence.models import (
    Assessment,
    AuditEvent,
    MaintenanceTask,
    ModelRegistration,
    Scenario,
)
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.arrivals import schedule_arrival
from fleet_maintenance.services.imports import import_history
from fleet_maintenance.services.planning import planning_snapshot
from fleet_maintenance.services.workspace import import_fixture
from fleet_maintenance.settings import get_settings

MODEL_ID = "customer-trial-v1"
POLICY = "trial-lower-bound-window-v1"


def catalog(session: Session) -> TrialCatalogResponse:
    path = get_settings().artifact_root / "customer-trial-sample.json"
    model = session.get(ModelRegistration, MODEL_ID)
    if not path.is_file() or model is None:
        return TrialCatalogResponse(
            available=False,
            reason="The local trial model and history have not been installed.",
            model_id=None,
            history=None,
            source_sha256=None,
        )
    sample = json.loads(path.read_text())
    history = HistoryImport.model_validate(sample["history"])
    return TrialCatalogResponse(
        available=True,
        reason="Simulated FD001 history and a calibrated baseline are installed.",
        model_id=model.id,
        history=history,
        source_sha256=sample["source_sha256"],
    )


def get_trial(session: Session, trial_id: str) -> TrialResponse:
    item = session.get(Scenario, trial_id)
    if item is None or not item.assumptions.get("customer_trial"):
        raise LookupError(trial_id)
    return TrialResponse.model_validate(item.assumptions["trial"])


def create_trial(session: Session, body: TrialRequest, actor: str) -> TrialResponse:
    digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    existing = session.get(Scenario, body.id)
    if existing:
        if existing.assumptions.get("request_sha256") != digest:
            raise ApprovalConflict(
                "Trial identity already has different inputs; create a new trial."
            )
        return get_trial(session, body.id)
    installed = catalog(session)
    if not installed.available or installed.model_id is None:
        raise ValueError(installed.reason)
    history = body.history or installed.history
    assert history is not None
    if body.cutoff_cycle > len(history.rows):
        raise ValueError("Selected cutoff exceeds the supplied history.")
    component, part, task = f"{body.id}-engine", f"{body.id}-kit", f"{body.id}-task"
    fixture = WorkspaceFixture.model_validate(
        {
            "source_version": body.id,
            "provenance": "synthetic",
            "scheduling_unit": "8_hour_slots",
            "aircraft": [
                {
                    "id": body.id,
                    "tail_number": f"TRIAL-{body.id[6:18]}",
                    "label": body.aircraft_label,
                }
            ],
            "components": [{"id": component, "aircraft_id": body.id, "serial_number": component}],
            "parts": [
                {
                    "id": part,
                    "name": f"{body.aircraft_label} · trial inspection kit",
                    "on_hand": body.spare_on_hand,
                }
            ],
            "tasks": [
                {
                    "id": task,
                    "component_id": component,
                    "title": "Customer trial engine inspection",
                    "duration_slots": body.duration_slots,
                    "deadline_slot": body.deadline_slot,
                    "required_part_id": part,
                    "required_part_quantity": 1,
                }
            ],
        }
    )
    import_fixture(session, fixture, actor, commit=False)
    from fleet_maintenance.services.resources import seed_resources

    seed_resources(session, component)
    record = import_history(
        session,
        component,
        body.id,
        history.engine_identity,
        [row.model_dump() for row in history.rows[: body.cutoff_cycle]],
        None,
        actor,
        commit=False,
    )
    arrival_id = f"{body.id}-delivery" if body.spare_on_hand == 0 else None
    if arrival_id:
        schedule_arrival(
            session,
            arrival_id,
            part,
            1,
            body.arrival_slot,
            1,
            "Synthetic delivery entered in customer trial",
            actor,
            commit=False,
        )
    response = TrialResponse(
        **body.model_dump(exclude={"history"}),
        component_id=component,
        part_id=part,
        import_id=record.id,
        model_id=installed.model_id,
        arrival_id=arrival_id,
        baseline_scenario_id=f"{body.id}-ready",
        supply_scenario_id=f"{body.id}-supply",
        engine_identity=history.engine_identity,
        history_sha256=record.sha256,
        history_origin="User-supplied FD001-format history"
        if body.history
        else "NASA C-MAPSS simulated validation engine",
    )
    # Matched single-aircraft workload; only parts readiness changes. No forecast-failure model.
    for scenario_id, name, ready in (
        (response.baseline_scenario_id, "Spare ready now", 0),
        (
            response.supply_scenario_id,
            "Your entered supply",
            0 if body.spare_on_hand else body.arrival_slot * 8,
        ),
    ):
        session.add(
            Scenario(
                id=scenario_id,
                name=f"{body.aircraft_label} · {name}",
                assumptions={
                    "horizon_hours": 112,
                    "aircraft_count": 1,
                    "maintenance_capacity": 1,
                    "part_available_hours": ready,
                    "maintenance_events": [[0, body.duration_slots * 8]],
                    "label": "synthetic",
                    "trial_id": body.id,
                    "component_id": component,
                    "comparison": "same workload; only part readiness differs",
                },
            )
        )
    session.add(
        Scenario(
            id=body.id,
            name=f"Customer trial · {body.aircraft_label}",
            assumptions={
                "customer_trial": True,
                "request_sha256": digest,
                "trial": response.model_dump(),
                "component_id": component,
                "part_id": part,
            },
        )
    )
    session.add(
        AuditEvent(
            actor=actor,
            action="customer_trial.created",
            subject_id=body.id,
            details={
                "request_sha256": digest,
                "history_sha256": record.sha256,
                "model_id": installed.model_id,
            },
        )
    )
    session.commit()
    return response


def trial_planning_snapshot(session: Session, trial_id: str) -> dict[str, object]:
    trial = get_trial(session, trial_id)
    assessment = session.scalar(
        select(Assessment)
        .where(
            Assessment.component_id == trial.component_id,
            Assessment.model_version == trial.model_id,
            Assessment.input_version == trial.import_id,
            Assessment.cutoff_cycle == trial.cutoff_cycle,
        )
        .order_by(Assessment.created_at.desc(), Assessment.id.desc())
        .limit(1)
    )
    if assessment is None or assessment.state != "available" or assessment.lower_cycles is None:
        raise ApprovalConflict(
            "A matching available AI assessment is required. Review data quality first."
        )
    # Explicit demonstration policy: remaining cycles / assumed usage => hours, rounded down.
    hours = assessment.lower_cycles * 24 / trial.cycles_per_day
    effective = min(trial.deadline_slot, math.floor(hours / 8))
    task = session.get(MaintenanceTask, f"{trial.id}-task")
    assert task is not None
    if task.status != "open":
        raise ApprovalConflict(
            "This trial already has committed work. Create a new trial to change inputs."
        )
    if task.deadline_slot != effective:
        task.deadline_slot = effective
        task.version += 1
    session.flush()
    snapshot = planning_snapshot(session, trial.component_id)
    snapshot["advisory"] = cast(
        dict[str, Any],
        {
            "policy": POLICY,
            "assessment_id": assessment.id,
            "model_id": trial.model_id,
            "input_version": trial.import_id,
            "cycles_per_day": trial.cycles_per_day,
            "lower_cycles": assessment.lower_cycles,
            "projected_lower_hours": hours,
            "mandatory_deadline_hours": trial.deadline_slot * 8,
            "effective_deadline_hours": effective * 8,
            "meaning": "Synthetic review window; not a certified maintenance limit.",
        },
    )
    return snapshot
