from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import ComponentDetailResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.services.records import component_detail

router = APIRouter(prefix="/components", tags=["components"])


@router.get("/{component_id}", response_model=ComponentDetailResponse)
def get_component(component_id: str, session: Session = Depends(get_session)) -> dict[str, object]:
    result = component_detail(session, component_id)
    if result is None:
        raise HTTPException(404, "Component not found")
    return result
