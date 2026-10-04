from typing import cast

from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.science.scheduling.solver import solve
from fleet_maintenance.science.simulation.replications import run_scenario
from fleet_maintenance.services.assessments import assess
from fleet_maintenance.services.jobs import (
    JobConflict,
    accept_result,
    claim_job,
    confirm_cancellation,
    fail_attempt,
)
from fleet_maintenance.services.planning import planning_snapshot, propose_plan, restore_source
from fleet_maintenance.services.scenarios import run_saved_scenario, scenario_source
from fleet_maintenance.workers.celery_app import app


@app.task(name="events.observe", ignore_result=True)  # type: ignore[untyped-decorator]
def observe(_: dict[str, object]) -> None:
    """Consume a confirmed notification; PostgreSQL remains authoritative."""


@app.task(name="jobs.execute", ignore_result=True)  # type: ignore[untyped-decorator]
def execute(job_id: str) -> None:
    with SessionLocal() as session:
        try:
            job = claim_job(session, job_id)
        except JobConflict:
            session.rollback()
            return
        attempt = job.attempt
        kind = job.kind
        payload = job.input_payload
        session.rollback()
        try:
            result: dict[str, object]
            if kind == "planning":
                if not payload:
                    payload = planning_snapshot(session)
                    session.rollback()
                computed_plan = solve(restore_source(payload))
                result = {
                    "plan_id": propose_plan(
                        session,
                        f"plan-for-{job_id}",
                        commit=False,
                        snapshot=payload,
                        computed_result=computed_plan,
                    ).id
                }
            elif kind == "simulation":
                scenario_id = str(payload["scenario_id"])
                from fleet_maintenance.persistence.models import Scenario

                computed_simulation = run_scenario(
                    scenario_source(cast(dict[str, object], payload["assumptions"]))
                )
                saved = session.get(Scenario, scenario_id)
                if (
                    saved is None
                    or saved.version != payload.get("version")
                    or saved.assumptions != payload.get("assumptions")
                ):
                    raise ValueError("Scenario inputs changed after submission")
                result = {
                    "run_id": run_saved_scenario(
                        session,
                        scenario_id,
                        run_id=f"sim-for-{job_id}",
                        commit=False,
                        computed_result=computed_simulation,
                    ).id
                }
            elif kind == "assessment":
                import numpy as np

                from fleet_maintenance.artifacts.storage import artifact_directory, verify_hashes
                from fleet_maintenance.persistence.models import ImportRecord, ModelRegistration
                from fleet_maintenance.science.prediction.inference import predict_history
                from fleet_maintenance.settings import get_settings

                history = session.get(ImportRecord, str(payload["import_id"]))
                model = session.get(ModelRegistration, str(payload["model_id"]))
                if history is None or model is None:
                    raise ValueError("Assessment inputs unavailable")
                cutoff = int(str(payload["cutoff_cycle"]))
                rows = history.rows[:cutoff]
                minimum = int(str(model.manifest["minimum_history_cycles"]))
                directory = artifact_directory(
                    get_settings().artifact_root, model.artifact_directory
                )
                hashes = model.hashes
                session.rollback()
                computed_prediction = None
                if cutoff >= minimum and all(
                    value is not None
                    for row in rows
                    for value in cast(list[float | None], row["values"])
                ):
                    verify_hashes(directory, hashes)
                    computed_prediction = predict_history(
                        directory,
                        np.asarray([row["values"] for row in rows], dtype=np.float64),
                        cutoff,
                    )
                result = {
                    "assessment_id": assess(
                        session,
                        str(payload["import_id"]),
                        str(payload["model_id"]),
                        int(str(payload["cutoff_cycle"])),
                        assessment_id=f"asm-for-{job_id}",
                        commit=False,
                        computed_prediction=computed_prediction,
                    ).id
                }
            else:
                fail_attempt(session, job_id, attempt, "unsupported_job_kind")
                return
            accept_result(session, job_id, attempt, result)
        except (KeyError, LookupError, ValueError):
            session.rollback()
            fail_attempt(session, job_id, attempt, "invalid_job_input")
        except JobConflict:
            session.rollback()
            session.refresh(job)
            if job.state == "cancellation_requested" and job.attempt == attempt:
                confirm_cancellation(session, job_id, attempt)
        except Exception:
            session.rollback()
            try:
                fail_attempt(session, job_id, attempt, "worker_execution_failed")
            except JobConflict:
                session.rollback()
            raise
