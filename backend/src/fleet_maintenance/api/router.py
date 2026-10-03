from fastapi import APIRouter

from fleet_maintenance.api.routes import (
    access,
    alerts,
    assessments,
    components,
    events,
    fleet,
    healthcheck,
    inventory,
    jobs,
    plans,
    scenarios,
)

router = APIRouter()
for route in (
    healthcheck.router,
    access.router,
    fleet.router,
    components.router,
    assessments.router,
    alerts.router,
    plans.router,
    inventory.router,
    scenarios.router,
    jobs.router,
    events.router,
):
    router.include_router(route)
