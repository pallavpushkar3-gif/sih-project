from dataclasses import dataclass


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


@dataclass(frozen=True)
class PlanningInput:
    horizon: int
    tasks: tuple[TaskInput, ...]
    skill_capacity: dict[str, int]
    part_stock: dict[str, int]


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
