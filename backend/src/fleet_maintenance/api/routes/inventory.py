from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import InventoryPartResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Part, Reservation

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryPartResponse])
def inventory(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    reserved = dict(
        session.execute(
            select(Reservation.part_id, func.sum(Reservation.quantity))
            .where(Reservation.status == "reserved")
            .group_by(Reservation.part_id)
        ).all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "on_hand": p.on_hand,
            "reserved": reserved.get(p.id, 0),
            "lead_time_slots": p.lead_time_slots,
            "version": p.version,
            "provenance": "synthetic",
        }
        for p in session.scalars(select(Part).order_by(Part.name)).all()
    ]
