from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.domain.contracts.api import InventoryPartResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Part, PartArrival, Reservation
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.arrivals import record_arrival, schedule_arrival
from fleet_maintenance.services.inventory import adjust_stock

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
            # The stored counter is uncommitted stock; physical on-hand also
            # includes units already set aside for approved work.
            "on_hand": p.on_hand + reserved.get(p.id, 0),
            "reserved": reserved.get(p.id, 0),
            "lead_time_slots": p.lead_time_slots,
            "version": p.version,
            "provenance": "synthetic",
        }
        for p in session.scalars(select(Part).order_by(Part.name)).all()
    ]


class StockAdjustment(BaseModel):
    delta_free_stock: int = Field(strict=True, ge=-1000000, le=1000000)
    expected_version: int = Field(strict=True, ge=1)
    reason: str = Field(min_length=1, max_length=1000)
    command_id: str = Field(min_length=1, max_length=80)


@router.post("/{part_id}/adjustments")
def adjustment(
    part_id: str,
    body: StockAdjustment,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role not in {"logistics", "supervisor"}:
        raise HTTPException(403, "Logistics or supervisor role required")
    try:
        part = adjust_stock(
            session,
            part_id,
            body.delta_free_stock,
            body.expected_version,
            body.reason,
            body.command_id,
            actor.id,
        )
        return {"id": part.id, "free_stock": part.on_hand, "version": part.version}
    except LookupError:
        raise HTTPException(404, "Part not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


class ArrivalRequest(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    part_id: str = Field(min_length=1, max_length=64)
    quantity: int = Field(strict=True, ge=1, le=1000000)
    arrival_slot: int = Field(strict=True, ge=0, le=13)
    expected_part_version: int = Field(strict=True, ge=1)
    reason: str = Field(min_length=1, max_length=1000)


class ArrivalOutcome(BaseModel):
    action: Literal["receive", "cancel", "quarantine", "reject"]
    expected_version: int = Field(strict=True, ge=1)
    reason: str = Field(min_length=1, max_length=1000)


class ArrivalResponse(BaseModel):
    id: str
    part_id: str
    quantity: int
    arrival_slot: int
    status: Literal["expected", "received", "cancelled", "quarantined", "rejected"]
    version: int
    reason: str
    created_at: datetime
    received_at: datetime | None
    provenance: Literal["synthetic"]
    slot_duration_hours: Literal[8]


def arrival_response(item: PartArrival) -> dict[str, object]:
    return {
        "id": item.id,
        "part_id": item.part_id,
        "quantity": item.quantity,
        "arrival_slot": item.arrival_slot,
        "status": item.status,
        "version": item.version,
        "reason": item.reason,
        "created_at": item.created_at,
        "received_at": item.received_at,
        "provenance": "synthetic",
        "slot_duration_hours": 8,
    }


@router.get("/arrivals", response_model=list[ArrivalResponse])
def arrivals(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    return [
        arrival_response(item)
        for item in session.scalars(
            select(PartArrival).order_by(PartArrival.created_at.desc())
        ).all()
    ]


@router.post("/arrivals", response_model=ArrivalResponse)
def expected_delivery(
    body: ArrivalRequest,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role not in {"logistics", "supervisor"}:
        raise HTTPException(403, "Logistics or supervisor role required")
    try:
        return arrival_response(
            schedule_arrival(
                session,
                body.id,
                body.part_id,
                body.quantity,
                body.arrival_slot,
                body.expected_part_version,
                body.reason,
                actor.id,
            )
        )
    except LookupError:
        raise HTTPException(404, "Part not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/arrivals/{arrival_id}/outcome", response_model=ArrivalResponse)
def delivery_outcome(
    arrival_id: str,
    body: ArrivalOutcome,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role not in {"logistics", "supervisor"}:
        raise HTTPException(403, "Logistics or supervisor role required")
    try:
        return arrival_response(
            record_arrival(
                session, arrival_id, body.action, body.expected_version, body.reason, actor.id
            )
        )
    except LookupError:
        raise HTTPException(404, "Delivery not found") from None
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc
