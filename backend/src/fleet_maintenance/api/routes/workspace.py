from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fleet_maintenance.api.dependencies import Actor, current_actor
from fleet_maintenance.domain.contracts.records import WorkspaceFixture
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.services.approvals import ApprovalConflict
from fleet_maintenance.services.workspace import import_fixture

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.post("/fixtures")
def fixtures(
    body: WorkspaceFixture,
    session: Session = Depends(get_session),
    actor: Actor = Depends(current_actor),
) -> dict[str, object]:
    if actor.role != "administrator":
        raise HTTPException(403, "Administrator role required")
    try:
        counts = import_fixture(session, body, actor.id)
        return {
            "source_version": body.source_version,
            "accepted_counts": counts,
            "rejected_counts": 0,
            "policy": "strict_atomic",
            "provenance": "synthetic",
        }
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except ApprovalConflict as exc:
        raise HTTPException(409, str(exc)) from exc
