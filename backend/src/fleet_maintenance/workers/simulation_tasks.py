from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.scenarios import run_saved_scenario
from fleet_maintenance.workers.celery_app import app


@app.task(name="simulation.run")  # type: ignore[untyped-decorator]
def run(scenario_id: str) -> str:
    with SessionLocal() as session:
        return run_saved_scenario(session, scenario_id).id
