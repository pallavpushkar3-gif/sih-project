"""Version-checked free-stock corrections, with command replay and audit evidence."""

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import AuditEvent, CommandRecord, Part
from fleet_maintenance.services.approvals import ApprovalConflict


def adjust_stock(
    session: Session,
    part_id: str,
    delta: int,
    expected_version: int,
    reason: str,
    command_id: str,
    actor: str,
) -> Part:
    key = hashlib.sha256(f"{actor}:stock:{command_id}".encode()).hexdigest()
    digest = hashlib.sha256(
        json.dumps([part_id, delta, expected_version, reason]).encode()
    ).hexdigest()
    part = session.scalar(select(Part).where(Part.id == part_id).with_for_update())
    if part is None:
        raise LookupError(part_id)
    previous = session.get(CommandRecord, key)
    if previous:
        if previous.payload_hash != digest:
            raise ApprovalConflict("Command identifier was already used for a different adjustment")
        return part
    if part.version != expected_version or part.on_hand + delta < 0:
        raise ApprovalConflict(
            "Stock version changed or correction would reduce free stock below zero"
        )
    part.on_hand += delta
    part.version += 1
    session.add(
        CommandRecord(
            id=key, actor=actor, kind="stock.adjusted", payload_hash=digest, result_id=part_id
        )
    )
    session.add(
        AuditEvent(
            actor=actor,
            action="stock.adjusted",
            subject_id=part_id,
            details={
                "delta_free_stock": delta,
                "reason": reason,
                "version": part.version,
                "command_id": command_id,
            },
        )
    )
    session.commit()
    return part
