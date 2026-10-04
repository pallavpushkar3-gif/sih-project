"""Deterministic earliest-release FIFO baseline, with the same hard constraints."""

from dataclasses import replace
from itertools import product

from fleet_maintenance.domain.contracts.planning import Assignment, PlanningInput, PlanningResult
from fleet_maintenance.science.scheduling.constraints import validate_input, validate_result
from fleet_maintenance.science.scheduling.resources import compatible


def fifo_schedule(source: PlanningInput) -> PlanningResult:
    errors = validate_input(source)
    if errors:
        return PlanningResult("invalid", diagnostics=tuple(errors))
    assigned: list[Assignment] = []
    tasks = sorted(
        source.tasks,
        key=lambda task: (
            task.fixed_start is None,
            task.earliest,
            task.group_id or task.id,
            task.id,
        ),
    )
    completed: set[str] = set()
    while tasks:
        eligible = next((task for task in tasks if set(task.predecessors) <= completed), None)
        if eligible is None:
            return PlanningResult("infeasible", diagnostics=("FIFO has cyclic precedence.",))
        candidates = {
            kind: [
                (r.id, unit)
                for r in source.resources
                if r.kind == kind and compatible(r, eligible)
                for unit in range(r.capacity)
            ]
            if source.resources
            else [(None, 0)]
            for kind in ("crew", "bay")
        }
        placement = None
        for start in range(eligible.earliest, eligible.deadline - eligible.duration + 1):
            for crew, bay in product(candidates["crew"], candidates["bay"]):
                trial = Assignment(
                    eligible.id, start, start + eligible.duration, crew[0], bay[0], crew[1], bay[1]
                )
                covered = completed | {eligible.id}
                prefix = replace(source, tasks=tuple(t for t in source.tasks if t.id in covered))
                if not validate_result(
                    prefix, PlanningResult("feasible", tuple(assigned + [trial]))
                ):
                    placement = trial
                    break
            if placement is not None:
                break
        if placement is None:
            return PlanningResult(
                "infeasible",
                diagnostics=(
                    f"FIFO cannot place {eligible.id} without relaxing a hard constraint.",
                ),
            )
        assigned.append(placement)
        completed.add(eligible.id)
        tasks.remove(eligible)
    return PlanningResult(
        "feasible",
        tuple(assigned),
        objective=max(
            (assignment.end for assignment in assigned),
            default=0,
        ),
    )
