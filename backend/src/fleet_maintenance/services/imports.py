"""Immutable complete histories with explicit correction ancestry."""

import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleet_maintenance.persistence.models import AuditEvent, Component, ImportRecord
from fleet_maintenance.services.approvals import ApprovalConflict


def import_history(
    session: Session,
    component_id: str,
    source_version: str,
    engine_identity: str,
    rows: list[dict[str, object]],
    previous_id: str | None,
    actor: str,
) -> ImportRecord:
    component = session.scalar(
        select(Component).where(Component.id == component_id).with_for_update()
    )
    if component is None:
        raise LookupError(component_id)
    digest = hashlib.sha256(
        json.dumps(
            {"identity": engine_identity, "rows": rows}, sort_keys=True, allow_nan=False
        ).encode()
    ).hexdigest()
    existing = session.scalar(
        select(ImportRecord).where(
            ImportRecord.component_id == component_id, ImportRecord.source_version == source_version
        )
    )
    if existing:
        if existing.sha256 != digest or existing.previous_id != previous_id:
            raise ApprovalConflict("Source version already exists with different content.")
        return existing
    latest = session.scalar(
        select(ImportRecord)
        .where(ImportRecord.component_id == component_id)
        .order_by(ImportRecord.created_at.desc(), ImportRecord.id.desc())
        .limit(1)
    )
    if (latest.id if latest else None) != previous_id:
        raise ApprovalConflict("Correction must reference the current import version.")
    if latest and latest.engine_identity != engine_identity:
        raise ApprovalConflict("Corrections cannot change the engine identity.")
    record = ImportRecord(
        id=f"import-{uuid.uuid4().hex}",
        component_id=component_id,
        source_version=source_version,
        engine_identity=engine_identity,
        sha256=digest,
        rows=rows,
        previous_id=previous_id,
        actor=actor,
    )
    session.add(record)
    component.current_cycle = len(rows)
    session.add(
        AuditEvent(
            actor=actor,
            action="history.imported",
            subject_id=record.id,
            details={
                "sha256": digest,
                "previous_id": previous_id,
                "source_version": source_version,
            },
        )
    )
    session.commit()
    return record
