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


@dataclass(frozen=True)
class PartArrivalInput:
    part_id: str
    slot: int
    quantity: int


@dataclass(frozen=True)
class PlanningInput:
    horizon: int
    tasks: tuple[TaskInput, ...]
    skill_capacity: dict[str, int]
    part_stock: dict[str, int]
    part_arrivals: tuple[PartArrivalInput, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Assignment:
    task_id: str
    start: int
    end: int


@dataclass(frozen=True)
class PlanningResult:
    status: str
    assignments: tuple[Assignment, ...] = ()
    diagnostics: tuple[str, ...] = ()
    objective: float | None = None
    best_bound: float | None = None
