from fleet_maintenance.persistence.database import SessionLocal
from fleet_maintenance.services.planning import propose_plan
from fleet_maintenance.workers.celery_app import app


@app.task(name="planning.propose")  # type: ignore[untyped-decorator]
def propose() -> str:
    with SessionLocal() as session:
        return propose_plan(session).id
