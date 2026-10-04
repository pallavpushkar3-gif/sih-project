"""Explicit local customer-trial inputs; the prediction units remain cycles."""

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

from fleet_maintenance.domain.contracts.health import HistoryImport as HistoryImport
from fleet_maintenance.domain.contracts.health import HistoryRow as HistoryRow


class TrialRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(pattern=r"^trial-[a-f0-9]{32}$")
    aircraft_label: str = Field(min_length=1, max_length=80)
    cutoff_cycle: int = Field(ge=1, le=10000)
    cycles_per_day: FiniteFloat = Field(gt=0, le=120)
    duration_slots: int = Field(ge=1, le=14)
    deadline_slot: int = Field(ge=1, le=14)
    spare_on_hand: int = Field(ge=0, le=10)
    arrival_slot: int = Field(ge=0, le=13)
    history: HistoryImport | None = None


class TrialResponse(BaseModel):
    id: str
    aircraft_label: str
    component_id: str
    part_id: str
    import_id: str
    model_id: str
    cutoff_cycle: int
    cycles_per_day: float
    duration_slots: int
    deadline_slot: int
    spare_on_hand: int
    arrival_slot: int
    arrival_id: str | None
    baseline_scenario_id: str
    supply_scenario_id: str
    engine_identity: str
    history_sha256: str
    history_origin: str


class TrialCatalogResponse(BaseModel):
    available: bool
    reason: str
    model_id: str | None
    history: HistoryImport | None
    source_sha256: str | None
