"""An administrator configures resources for one isolated agency workspace."""

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import AuditEvent, MaintenanceResource, ResourceSlot
from fleet_maintenance.services.resources import resource_inputs, resource_records

router = APIRouter(prefix="/resources", tags=["resources"])


class ResourceConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["crew", "bay"]
    label: str = Field(min_length=1, max_length=160)
    capabilities: list[str] = Field(min_length=1, max_length=50)
    available: list[list[int]] = Field(max_length=100)
    aircraft_ids: list[str] = Field(default_factory=list, max_length=1000)
    capacity: int = Field(default=1, ge=1, le=100)
    valid_from: int = Field(default=0, ge=0, le=13)
    valid_until: int = Field(default=14, ge=1, le=14)
    expected_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def intervals(self) -> "ResourceConfiguration":
        if self.valid_until <= self.valid_from:
            raise ValueError("Qualification must have a positive validity interval")
        if any(len(row) != 2 or not 0 <= row[0] < row[1] <= 14 for row in self.available):
            raise ValueError("Calendar windows require [start, end] inside fourteen 8-hour slots")
        if any(not item or len(item) > 64 for item in self.capabilities + self.aircraft_ids):
            raise ValueError("Capability/aircraft identifiers must be nonempty and bounded")
        return self


@router.get("")
def resources(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    records = resource_records(session)
    return [
        {
            **asdict(value),
            "label": record.label,
            "unit": "8_hour_slots",
            "provenance": "configured demonstrator resource",
        }
        for value, record in zip(resource_inputs(records), records, strict=True)
    ]


@router.put("/{resource_id}")
def configure(
    resource_id: str,
    body: ResourceConfiguration,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role != "administrator":
        raise HTTPException(403, "Administrator role required to configure resources")
    if not resource_id or len(resource_id) > 64 or resource_id.startswith("trial-"):
        raise HTTPException(422, "Invalid operational resource identifier")
    item = session.scalar(
        select(MaintenanceResource).where(MaintenanceResource.id == resource_id).with_for_update()
    )
    if item is None:
        if body.expected_version is not None:
            raise HTTPException(409, "Resource does not exist")
        item = MaintenanceResource(id=resource_id, **body.model_dump(exclude={"expected_version"}))
        session.add(item)
    else:
        if item.version != body.expected_version:
            raise HTTPException(409, "Resource version changed; refresh configuration")
        if session.scalar(
            select(ResourceSlot.id).where(ResourceSlot.resource_id == item.id).limit(1)
        ):
            raise HTTPException(
                409, "Resource has active bookings; release work before reconfiguration"
            )
        if item.kind != body.kind:
            raise HTTPException(409, "Resource kind is immutable; create a new resource")
        for key, value in body.model_dump(exclude={"expected_version", "kind"}).items():
            setattr(item, key, value)
        item.version += 1
    try:
        session.flush()
        session.add(
            AuditEvent(
                actor=actor.id,
                action="resource.configured",
                subject_id=item.id,
                details={"version": item.version, "unit": "8_hour_slots"},
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(409, "Resource changed concurrently; refresh configuration") from exc
    return {"id": item.id, "version": item.version}
