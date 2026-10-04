"""Eligibility semantics; validation checks every assigned interval independently."""

from fleet_maintenance.domain.contracts.planning import ResourceInput, TaskInput


def compatible(resource: ResourceInput, task: TaskInput) -> bool:
    capability = task.skill if resource.kind == "crew" else task.component_kind
    fixed = task.fixed_crew_id if resource.kind == "crew" else task.fixed_bay_id
    return (
        capability in resource.capabilities
        and (not resource.aircraft_ids or task.aircraft_id in resource.aircraft_ids)
        and (fixed is None or resource.id == fixed)
    )


def allowed_starts(resource: ResourceInput, task: TaskInput) -> list[int]:
    return [
        start
        for start in range(task.earliest, task.deadline - task.duration + 1)
        if resource.valid_from <= start
        and start + task.duration <= resource.valid_until
        and all(
            any(left <= slot < right for left, right in resource.available)
            for slot in range(start, start + task.duration)
        )
    ]
