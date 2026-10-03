from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fleet_maintenance.domain.contracts.api import AssessmentDetailResponse
from fleet_maintenance.persistence.database import get_session
from fleet_maintenance.persistence.models import Assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment(
    assessment_id: str, session: Session = Depends(get_session)
) -> dict[str, object]:
    item = session.get(Assessment, assessment_id)
    if item is None:
        raise HTTPException(404, "Assessment not found")
    return {
        "id": item.id,
        "component_id": item.component_id,
        "state": item.state,
        "estimate_cycles": item.estimate_cycles,
        "lower_cycles": item.lower_cycles,
        "upper_cycles": item.upper_cycles,
        "model_version": item.model_version,
        "input_version": item.input_version,
        "quality_findings": item.quality_findings,
        "explanation": {
            "state": "unavailable",
            "reason": "No evaluated model artifact is installed.",
        },
    }
