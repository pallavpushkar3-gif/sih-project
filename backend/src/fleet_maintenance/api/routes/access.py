from fastapi import APIRouter, Depends

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.domain.contracts.api import SessionResponse

router = APIRouter(prefix="/access", tags=["access"])


@router.get("/session", response_model=SessionResponse)
def session(actor: Actor = Depends(current_actor)) -> dict[str, str]:
    return {"id": actor.id, "role": actor.role, "authentication": "demonstration header"}
