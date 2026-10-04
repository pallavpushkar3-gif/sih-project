"""Conservative same-component grouping: contiguous work, no invented duration savings."""

from fleet_maintenance.science.scheduling.formulation import PlanningInput, TaskInput


def groups(source: PlanningInput) -> dict[str, tuple[TaskInput, ...]]:
    result: dict[str, list[TaskInput]] = {}
    for task in source.tasks:
        if task.group_id:
            result.setdefault(task.group_id, []).append(task)
    return {key: tuple(sorted(tasks, key=lambda task: task.id)) for key, tasks in result.items()}


def validate_groups(source: PlanningInput) -> list[str]:
    errors = []
    for key, tasks in groups(source).items():
        if (
            not tasks[0].component_id
            or len({task.component_id for task in tasks}) != 1
            or len({task.skill for task in tasks}) != 1
        ):
            errors.append(f"Group {key} requires one component and one qualified skill.")
        earliest, latest, offset = 0, source.horizon, 0
        for task in tasks:
            earliest = max(earliest, task.earliest - offset)
            latest = min(latest, task.deadline - task.duration - offset)
            if task.fixed_start is not None:
                earliest = max(earliest, task.fixed_start - offset)
                latest = min(latest, task.fixed_start - offset)
            offset += task.duration
        if earliest > latest:
            errors.append(f"Group {key} cannot fit its members' windows and fixed commitments.")
    return errors
