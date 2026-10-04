"""Expected deliveries are planning assumptions until an audited physical receipt."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import AuditEvent, Part, PartArrival
from fleet_maintenance.services.approvals import ApprovalConflict


def schedule_arrival(
    session: Session,
    arrival_id: str,
    part_id: str,
    quantity: int,
    slot: int,
    expected_part_version: int,
    reason: str,
    actor: str,
    *,
    commit: bool = True,
) -> PartArrival:
    if quantity <= 0 or not 0 <= slot < 14:
        raise ValueError("Delivery quantity and slot are outside the supported horizon")
    part = session.scalar(select(Part).where(Part.id == part_id).with_for_update())
    if part is None:
        raise LookupError(part_id)
    existing = session.get(PartArrival, arrival_id)
    if existing is not None:
        if (
            existing.part_id,
            existing.quantity,
            existing.arrival_slot,
            existing.reason,
            existing.actor,
        ) != (part_id, quantity, slot, reason, actor):
            raise ApprovalConflict("Delivery identity was already used for different content")
        return existing
    if part.version != expected_part_version:
        raise ApprovalConflict("Part version changed; reload inventory")
    item = PartArrival(
        id=arrival_id,
        part_id=part_id,
        quantity=quantity,
        arrival_slot=slot,
        reason=reason,
        actor=actor,
    )
    session.add(item)
    part.version += 1
    session.add(
        AuditEvent(
            actor=actor,
            action="arrival.expected",
            subject_id=item.id,
            details={
                "part_id": part_id,
                "quantity": quantity,
                "slot": slot,
                "reason": reason,
                "part_version": part.version,
            },
        )
    )
    try:
        if commit:
            session.commit()
        else:
            session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise ApprovalConflict("Delivery identity conflicted; reload and retry") from exc
    session.refresh(item)
    return item


def record_arrival(
    session: Session, arrival_id: str, action: str, expected_version: int, reason: str, actor: str
) -> PartArrival:
    hint = session.get(PartArrival, arrival_id)
    if hint is None:
        raise LookupError(arrival_id)
    # Match stock-command lock order; serialize receipts against approvals and adjustments.
    part = session.scalar(select(Part).where(Part.id == hint.part_id).with_for_update())
    assert part is not None
    item = session.scalar(
        select(PartArrival)
        .where(PartArrival.id == arrival_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    assert item is not None
    target = {"receive": "received", "cancel": "cancelled",
              "quarantine": "quarantined", "reject": "rejected"}.get(action)
    if target is None:
        raise ValueError("Unknown delivery outcome")
    if item.status == target:
        return item  # Safe replay never credits stock twice.
    if item.version != expected_version or item.status != "expected":
        raise ApprovalConflict("Delivery version/state changed; reload before recording an outcome")
    item.status = target
    item.version += 1
    part.version += 1
    if action == "receive":
        part.on_hand += item.quantity
        item.received_at = datetime.now(UTC)
    elif action in {"quarantine", "reject"}:
        item.received_at = datetime.now(UTC)
        # Physical receipt alone does not make quarantined/rejected units usable.
    session.add(
        AuditEvent(
            actor=actor,
            action=f"arrival.{target}",
            subject_id=item.id,
            details={
                "quantity": item.quantity,
                "part_id": item.part_id,
                "reason": reason,
                "version": item.version,
                "part_version": part.version,
            },
        )
    )
    session.commit()
    session.refresh(item)
    return item
