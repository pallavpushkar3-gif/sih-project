from fleet_maintenance.science.scheduling.constraints import validate_input, validate_result
from fleet_maintenance.science.scheduling.formulation import (
    Assignment,
    PlanningInput,
    PlanningResult,
    TaskInput,
)
from fleet_maintenance.science.scheduling.objective import makespan


def _fits(
    source: PlanningInput,
    task: TaskInput,
    start: int,
    assignments: dict[str, Assignment],
) -> bool:
    if task.part_id:
        candidates = {**assignments, task.id: Assignment(task.id, start, start + task.duration)}
        part_tasks = [t for t in source.tasks if t.part_id == task.part_id and t.id in candidates]
        for slot in {candidates[t.id].start for t in part_tasks}:
            supplied = source.part_stock.get(task.part_id, 0) + sum(
                a.quantity
                for a in source.part_arrivals
                if a.part_id == task.part_id and a.slot <= slot
            )
            used = sum(t.part_quantity for t in part_tasks if candidates[t.id].start <= slot)
            if used > supplied:
                return False
    capacity = source.skill_capacity[task.skill]
    relevant = [
        item
        for task_id, item in assignments.items()
        if next(candidate for candidate in source.tasks if candidate.id == task_id).skill
        == task.skill
    ]
    return all(
        sum(item.start <= slot < item.end for item in relevant) < capacity
        for slot in range(start, start + task.duration)
    )


def earliest_deadline_first(source: PlanningInput) -> PlanningResult:
    """Construct a transparent list schedule without backtracking.

    An infeasible result means this baseline did not construct a schedule; it is
    not a proof that the planning instance is mathematically infeasible.
    """

    errors = validate_input(source)
    if errors:
        return PlanningResult("invalid", diagnostics=tuple(errors))
    assignments: dict[str, Assignment] = {}
    by_id = {task.id: task for task in source.tasks}
    fixed = sorted(
        (task for task in source.tasks if task.fixed_start is not None),
        key=lambda task: (task.fixed_start, task.id),
    )
    for task in fixed:
        start = task.fixed_start
        assert start is not None
        if not _fits(source, task, start, assignments):
            return PlanningResult(
                "infeasible", diagnostics=(f"Baseline cannot place fixed task {task.id}.",)
            )
        assignments[task.id] = Assignment(task.id, start, start + task.duration)

    remaining = {task.id for task in source.tasks if task.id not in assignments}
    while remaining:
        ready = [
            by_id[task_id]
            for task_id in remaining
            if set(by_id[task_id].predecessors) <= set(assignments)
        ]
        if not ready:
            return PlanningResult(
                "infeasible", diagnostics=("Baseline found cyclic or unsatisfied precedence.",)
            )
        task = min(ready, key=lambda item: (item.deadline, item.earliest, item.id))
        predecessor_end = max(
            (assignments[item].end for item in task.predecessors), default=task.earliest
        )
        earliest = max(task.earliest, predecessor_end)
        start = next(
            (
                candidate
                for candidate in range(earliest, task.deadline - task.duration + 1)
                if _fits(source, task, candidate, assignments)
            ),
            None,
        )
        if start is None:
            return PlanningResult(
                "infeasible", diagnostics=(f"Baseline cannot place task {task.id}.",)
            )
        assignments[task.id] = Assignment(task.id, start, start + task.duration)
        remaining.remove(task.id)

    ordered = tuple(assignments[task.id] for task in source.tasks)
    result = PlanningResult("feasible", ordered, objective=makespan(ordered))
    violations = validate_result(source, result)
    return result if not violations else PlanningResult("failed", diagnostics=tuple(violations))
