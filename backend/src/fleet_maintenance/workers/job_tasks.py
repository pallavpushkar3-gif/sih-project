from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.jobs import (
    JobConflict,
    accept_result,
    claim_job,
    confirm_cancellation,
    fail_attempt,
)
from fleet_maintenance.services.planning import propose_plan
from fleet_maintenance.services.scenarios import run_saved_scenario
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
            return
        attempt = job.attempt
        kind = job.kind
        payload = job.input_payload
        try:
            result: dict[str, object]
            if kind == "planning":
                result = {"plan_id": propose_plan(session, f"plan-for-{job_id}").id}
            elif kind == "simulation":
                scenario_id = str(payload["scenario_id"])
                result = {
                    "run_id": run_saved_scenario(
                        session, scenario_id, run_id=f"sim-for-{job_id}"
                    ).id
                }
            else:
                fail_attempt(session, job_id, attempt, "unsupported_job_kind")
                return
            session.refresh(job)
            if job.state == "cancellation_requested":
                confirm_cancellation(session, job_id, attempt)
            else:
                accept_result(session, job_id, attempt, result)
        except (KeyError, LookupError, ValueError):
            fail_attempt(session, job_id, attempt, "invalid_job_input")
        except JobConflict:
            return
