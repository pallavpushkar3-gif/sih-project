"""Atomic fixture ingestion; duplicate imports and conflicts retain explicit provenance."""

import hashlib
from collections.abc import Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.records import FixtureRecord, WorkspaceFixture
from fleet_maintenance.persistence.database import Base
from fleet_maintenance.persistence.models import (
    Aircraft,
    AuditEvent,
    CommandRecord,
    Component,
    MaintenanceTask,
    Part,
)
from fleet_maintenance.services.approvals import ApprovalConflict


def import_fixture(session: Session, body: WorkspaceFixture, actor: str) -> dict[str, int]:
    digest = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    key = hashlib.sha256(f"fixture:{body.source_version}".encode()).hexdigest()
    counts = {
        "aircraft": len(body.aircraft),
        "components": len(body.components),
        "parts": len(body.parts),
        "tasks": len(body.tasks),
    }
    previous = session.get(CommandRecord, key)
    if previous:
        if previous.payload_hash != digest:
            raise ApprovalConflict("Fixture source version already has different content")
        return counts
    groups: list[tuple[type[Base], Sequence[FixtureRecord]]] = [
        (Aircraft, body.aircraft),
        (Component, body.components),
        (Part, body.parts),
        (MaintenanceTask, body.tasks),
    ]
    try:
        for model, records in groups:
            identifiers = [record.id for record in records]
            if len(set(identifiers)) != len(identifiers):
                raise ValueError("Duplicate identifiers in fixture")
            for record in records:
                if session.get(model, record.id):
                    raise ApprovalConflict("Fixture would overwrite an existing record")
                values = record.model_dump()
                if model is Component and session.get(Aircraft, str(values["aircraft_id"])) is None:
                    raise ValueError("Component references an unknown aircraft")
                if (
                    model is MaintenanceTask
                    and session.get(Component, str(values["component_id"])) is None
                ):
                    raise ValueError("Task references an unknown component")
                session.add(model(**values))
            session.flush()
        for task in body.tasks:
            if task.earliest_slot + task.duration_slots > task.deadline_slot:
                raise ValueError("Task cannot fit its scheduling window")
            if (
                task.fixed_start is not None
                and not task.earliest_slot
                <= task.fixed_start
                <= task.deadline_slot - task.duration_slots
            ):
                raise ValueError("Fixed task start is outside its window")
            if task.required_part_quantity and (
                not task.required_part_id or session.get(Part, task.required_part_id) is None
            ):
                raise ValueError("Task requires an unknown part")
            if task.id in task.predecessors or any(
                session.get(MaintenanceTask, predecessor) is None
                for predecessor in task.predecessors
            ):
                raise ValueError("Task has invalid predecessor references")
        session.add(
            CommandRecord(
                id=key,
                actor=actor,
                kind="workspace.imported",
                payload_hash=digest,
                result_id=key,
            )
        )
        session.add(
            AuditEvent(
                actor=actor,
                action="workspace.imported",
                subject_id=key,
                details={
                    "sha256": digest,
                    "source_version": body.source_version,
                    "provenance": "synthetic",
                    "scheduling_unit": body.scheduling_unit,
                    "accepted_counts": counts,
                    "rejected_counts": 0,
                    "policy": "strict_atomic",
                },
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ApprovalConflict(
            "Fixture contains conflicting identifiers or invalid relationships"
        ) from exc
    except (ValueError, ApprovalConflict):
        session.rollback()
        raise
    return counts
