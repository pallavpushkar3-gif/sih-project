"""Explicit synthetic grounding and early-maintenance metrics for checked schedules."""

from fleet_maintenance.science.scheduling.constraints import validate_result
from fleet_maintenance.science.scheduling.formulation import PlanningInput, PlanningResult


def grouping_metrics(
    source: PlanningInput,
    result: PlanningResult,
    preferred_starts: dict[str, int],
    cycles_per_slot: float,
) -> dict[str, float | int]:
    import math

    if not math.isfinite(cycles_per_slot) or cycles_per_slot <= 0:
        raise ValueError("Grouping cycle conversion must be finite and positive")
    if validate_result(source, result):
        raise ValueError("Tradeoffs require an independently valid schedule")
    if set(preferred_starts) != {task.id for task in source.tasks}:
        raise ValueError("Every task requires an explicit preferred maintenance start")
    by_id = {task.id: task for task in source.tasks}
    component_intervals: dict[str, list[tuple[int, int]]] = {}
    early = 0
    for assignment in result.assignments:
        task = by_id[assignment.task_id]
        if not task.component_id:
            raise ValueError("Grounding metrics require a component identity")
        component_intervals.setdefault(task.component_id, []).append(
            (assignment.start, assignment.end)
        )
        early += max(0, preferred_starts[task.id] - assignment.start)
    groundings, occupied = 0, 0
    for intervals in component_intervals.values():
        end = -1
        for start, finish in sorted(intervals):
            if start > end:
                groundings += 1
                occupied += finish - start
            else:
                occupied += max(0, finish - end)
            end = max(end, finish)
    return {
        "component_grounding_episodes": groundings,
        "grounding_slots": occupied,
        "early_maintenance_slots": early,
        "synthetic_discarded_cycles": early * cycles_per_slot,
    }
