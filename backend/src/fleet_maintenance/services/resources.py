"""Versioned single-agency resources; trial resources are separate demonstration scopes."""

import uuid
from dataclasses import asdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.planning import ResourceInput
from fleet_maintenance.persistence.models import (
    MaintenanceResource,
    ResourceBooking,
    ResourceSlot,
)


def resource_records(
    session: Session, scope: str | None = None, *, lock: bool = False
) -> list[MaintenanceResource]:
    query = (
        select(MaintenanceResource)
        .where(MaintenanceResource.scope_component_id == scope)
        .order_by(MaintenanceResource.id)
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    return list(session.scalars(query))


def resource_inputs(records: list[MaintenanceResource]) -> tuple[ResourceInput, ...]:
    return tuple(
        ResourceInput(
            r.id,
            r.kind,
            tuple(r.capabilities),
            tuple((a, b) for a, b in r.available),
            r.capacity,
            r.valid_from,
            r.valid_until,
            tuple(r.aircraft_ids),
            r.version,
        )
        for r in records
    )


def seed_resources(session: Session, scope: str | None = None) -> None:
    """Explicitly synthetic, uninterrupted demo calendars. Never called in production setup."""
    for kind in ("crew", "bay"):
        identifier = f"{scope or 'demo'}-{kind}"
        if session.get(MaintenanceResource, identifier) is None:
            session.add(
                MaintenanceResource(
                    id=identifier,
                    kind=kind,
                    label=f"Synthetic {kind}",
                    capabilities=["engine"],
                    available=[[0, 14]],
                    scope_component_id=scope,
                )
            )
    session.flush()


def reserve_assignments(
    session: Session,
    plan_id: str,
    assignments: list[dict[str, object]],
    resources: list[MaintenanceResource],
) -> None:
    by_id = {resource.id: resource for resource in resources}
    for assignment in assignments:
        for kind in ("crew", "bay"):
            resource_id = str(assignment[f"{kind}_id"])
            resource = by_id[resource_id]
            unit = int(str(assignment.get(f"{kind}_unit", 0)))
            start, end = int(str(assignment["start"])), int(str(assignment["end"]))
            booking = ResourceBooking(
                id=f"booking-{uuid.uuid4().hex}",
                plan_id=plan_id,
                task_id=str(assignment["task_id"]),
                resource_id=resource_id,
                unit=unit,
                start_slot=start,
                end_slot=end,
            )
            session.add(booking)
            session.flush()
            session.add_all(
                [
                    ResourceSlot(
                        resource_id=resource_id, booking_id=booking.id, unit=unit, slot=slot
                    )
                    for slot in range(start, end)
                ]
            )
            resource.version += 1


def release_bookings(session: Session, plan_id: str, task_id: str, outcome: str) -> None:
    bookings = session.scalars(
        select(ResourceBooking)
        .where(
            ResourceBooking.plan_id == plan_id,
            ResourceBooking.task_id == task_id,
            ResourceBooking.status == "reserved",
        )
        .order_by(ResourceBooking.resource_id)
    ).all()
    for booking in bookings:
        resource = session.scalar(
            select(MaintenanceResource)
            .where(MaintenanceResource.id == booking.resource_id)
            .with_for_update()
        )
        assert resource is not None
        session.execute(delete(ResourceSlot).where(ResourceSlot.booking_id == booking.id))
        booking.status = outcome
        resource.version += 1


def resource_snapshot(session: Session, scope: str | None = None) -> list[dict[str, object]]:
    return [asdict(resource) for resource in resource_inputs(resource_records(session, scope))]
