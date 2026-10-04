"""Immutable scheduling contracts. Intervals are half-open integer slots."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskInput:
    id: str
    duration: int
    earliest: int
    deadline: int
    skill: str
    part_id: str | None = None
    part_quantity: int = 0
    fixed_start: int | None = None
    predecessors: tuple[str, ...] = ()
    component_id: str | None = None
    group_id: str | None = None
    component_kind: str = "engine"
    aircraft_id: str | None = None
    fixed_crew_id: str | None = None
    fixed_bay_id: str | None = None
    fixed_crew_unit: int = 0
    fixed_bay_unit: int = 0


@dataclass(frozen=True)
class PartArrivalInput:
    part_id: str
    slot: int
    quantity: int


@dataclass(frozen=True)
class ResourceInput:
    id: str
    kind: str
    capabilities: tuple[str, ...]
    available: tuple[tuple[int, int], ...]
    capacity: int = 1
    valid_from: int = 0
    valid_until: int = 14
    aircraft_ids: tuple[str, ...] = ()
    version: int = 1


@dataclass(frozen=True)
class PlanningInput:
    horizon: int
    tasks: tuple[TaskInput, ...]
    skill_capacity: dict[str, int]
    part_stock: dict[str, int]
    part_arrivals: tuple[PartArrivalInput, ...] = field(default_factory=tuple)
    resources: tuple[ResourceInput, ...] = field(default_factory=tuple)
    slot_duration_hours: int = 8
    time_zone: str = "Asia/Kolkata"
    epoch_utc: str | None = None


@dataclass(frozen=True)
class Assignment:
    task_id: str
    start: int
    end: int
    crew_id: str | None = None
    bay_id: str | None = None
    crew_unit: int = 0
    bay_unit: int = 0


@dataclass(frozen=True)
class PlanningResult:
    status: str
    assignments: tuple[Assignment, ...] = ()
    diagnostics: tuple[str, ...] = ()
    objective: float | None = None
    best_bound: float | None = None
