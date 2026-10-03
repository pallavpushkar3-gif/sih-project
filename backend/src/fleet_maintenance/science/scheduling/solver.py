from ortools.sat.python import cp_model

from fleet_maintenance.science.scheduling.constraints import validate_input, validate_result
from fleet_maintenance.science.scheduling.formulation import (
    Assignment,
    PlanningInput,
    PlanningResult,
)


def solve(source: PlanningInput, time_limit_seconds: float = 5.0) -> PlanningResult:
    errors = validate_input(source)
    if errors:
        return PlanningResult("invalid", diagnostics=tuple(errors))
    if not source.tasks:
        return PlanningResult("optimal", objective=0.0, best_bound=0.0)
    model = cp_model.CpModel()
    starts: dict[str, cp_model.IntVar] = {}
    ends: dict[str, cp_model.IntVar] = {}
    intervals: dict[str, cp_model.IntervalVar] = {}
    for task in source.tasks:
        starts[task.id] = model.new_int_var(
            task.earliest, task.deadline - task.duration, f"start_{task.id}"
        )
        ends[task.id] = model.new_int_var(
            task.earliest + task.duration, task.deadline, f"end_{task.id}"
        )
        intervals[task.id] = model.new_interval_var(
            starts[task.id], task.duration, ends[task.id], f"interval_{task.id}"
        )
        if task.fixed_start is not None:
            model.add(starts[task.id] == task.fixed_start)
        for predecessor_id in task.predecessors:
            model.add(starts[task.id] >= ends[predecessor_id])
    for skill, capacity in source.skill_capacity.items():
        skill_intervals = [intervals[t.id] for t in source.tasks if t.skill == skill]
        if skill_intervals:
            model.add_cumulative(skill_intervals, [1] * len(skill_intervals), capacity)
    makespan = model.new_int_var(0, source.horizon, "makespan")
    model.add_max_equality(makespan, list(ends.values()))
    model.minimize(makespan)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    status = solver.solve(model)
    names = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.UNKNOWN: "unknown",
        cp_model.MODEL_INVALID: "invalid",
    }
    label = names.get(status, "failed")
    if label not in {"optimal", "feasible"}:
        return PlanningResult(label)
    assignments = tuple(
        Assignment(task.id, solver.value(starts[task.id]), solver.value(ends[task.id]))
        for task in source.tasks
    )
    result = PlanningResult(
        label,
        assignments,
        objective=solver.objective_value,
        best_bound=solver.best_objective_bound,
    )
    violations = validate_result(source, result)
    return result if not violations else PlanningResult("failed", diagnostics=tuple(violations))
