from fastapi import APIRouter, Depends

from fleet_maintenance.api.dependencies import current_actor
from fleet_maintenance.api.routes import (
    access,
    alerts,
    assessments,
    components,
    events,
    evidence,
    fleet,
    healthcheck,
    inventory,
    jobs,
    plans,
    scenarios,
    work,
    workspace,
)

router = APIRouter()
router.include_router(healthcheck.router)
router.include_router(access.router)
for route in (
    fleet.router,
    components.router,
    assessments.router,
    alerts.router,
    plans.router,
    inventory.router,
    scenarios.router,
    jobs.router,
    events.router,
    work.router,
    workspace.router,
    evidence.router,
):
    router.include_router(route, dependencies=[Depends(current_actor)])
