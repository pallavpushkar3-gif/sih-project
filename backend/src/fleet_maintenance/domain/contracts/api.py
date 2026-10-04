from datetime import datetime

from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    id: str
    role: str
    authentication: str


class HealthResponse(BaseModel):
    status: str
    database: str | None = None


class FleetItemResponse(BaseModel):
    id: str
    tail_number: str
    label: str
    provenance: str
    component_ids: list[str]
    components: int = Field(ge=0)
    open_tasks: int = Field(ge=0)


class ObservationResponse(BaseModel):
    cycle: int = Field(ge=0)
    sensor: str
    value: float
    unit: str
    source_version: str


class QualityFindingResponse(BaseModel):
    code: str
    severity: str
    message: str


class AssessmentSummaryResponse(BaseModel):
    id: str
    state: str
    estimate_cycles: float | None
    lower_cycles: float | None
    upper_cycles: float | None
    model_version: str | None
    input_version: str
    quality_findings: list[QualityFindingResponse]


class ComponentDetailResponse(BaseModel):
    id: str
    aircraft_id: str
    serial_number: str
    kind: str
    status: str
    current_cycle: int = Field(ge=0)
    observations: list[ObservationResponse]
    assessment: AssessmentSummaryResponse | None


class ExplanationStateResponse(BaseModel):
    state: str
    reason: str


class AssessmentDetailResponse(AssessmentSummaryResponse):
    component_id: str
    cutoff_cycle: int | None = None
    evidence: dict[str, object] = Field(default_factory=dict)
    explanation: ExplanationStateResponse


class AlertAcknowledgementResponse(BaseModel):
    actor: str
    created_at: datetime


class AlertResponse(BaseModel):
    id: str
    component_id: str
    state: str
    reason: str
    policy_version: str
    assessment_id: str | None
    acknowledged_by: str | None
    acknowledgements: list[AlertAcknowledgementResponse]
    episode_id: str | None = None
    policy_context: dict[str, object] = Field(default_factory=dict)


class InventoryPartResponse(BaseModel):
    id: str
    name: str
    on_hand: int = Field(ge=0)
    reserved: int = Field(ge=0)
    lead_time_slots: int = Field(ge=0)
    version: int = Field(ge=1)
    provenance: str


class PlanAssignmentResponse(BaseModel):
    task_id: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    crew_id: str | None = None
    bay_id: str | None = None
    crew_unit: int = Field(default=0, ge=0)
    bay_unit: int = Field(default=0, ge=0)


class PlanResponse(BaseModel):
    input_snapshot: dict[str, object] = Field(default_factory=dict)
    objective: float | None = None
    best_bound: float | None = None
    parent_id: str | None = None
    id: str
    status: str
    solver_status: str
    input_version: str
    assignments: list[PlanAssignmentResponse]
    diagnostics: list[str]
    created_at: datetime
    approved_at: datetime | None
    approved_by: str | None


class ScenarioResponse(BaseModel):
    id: str
    name: str
    version: int = Field(ge=1)
    assumptions: dict[str, object]
    provenance: str


class SimulationRunResponse(BaseModel):
    id: str
    scenario_id: str
    policy: str
    seed: int
    availability: float = Field(ge=0, le=1)
    metrics: dict[str, object]


class JobResponse(BaseModel):
    id: str
    kind: str
    state: str
    attempt: int = Field(ge=0)
    result: dict[str, object] | None


class InspectionTaskResponse(BaseModel):
    id: str
    title: str
    status: str
    mandatory: bool
    deadline_slot: int
    duration_slots: int
    required_skill: str
    part_id: str | None
    part_required: int
    part_available: int | None
    version: int


class ComponentMaintenanceResponse(BaseModel):
    component_id: str
    slot_duration_hours: int
    tasks: list[InspectionTaskResponse]


class ReservationHistoryResponse(BaseModel):
    id: int
    part_id: str
    quantity: int
    status: str


class WorkHistoryResponse(BaseModel):
    id: str
    task_id: str
    status: str
    version: int
    consumed_quantity: int
    notes: str
    started_at: datetime | None
    completed_at: datetime | None


class PlanCommitmentResponse(BaseModel):
    plan_id: str
    reservations: list[ReservationHistoryResponse]
    work: list[WorkHistoryResponse]
