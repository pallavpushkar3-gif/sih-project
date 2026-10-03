from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import FleetItemResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.services.records import fleet_summary

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("", response_model=list[FleetItemResponse])
def list_fleet(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return fleet_summary(session)
