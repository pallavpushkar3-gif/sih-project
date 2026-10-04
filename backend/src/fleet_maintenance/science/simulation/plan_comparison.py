"""Actual-plan event simulation. No stochastic failure law is inferred from RUL."""

from dataclasses import asdict

import simpy

from fleet_maintenance.domain.contracts.planning import Assignment, PlanningInput, PlanningResult
from fleet_maintenance.science.scheduling.baseline import fifo_schedule
from fleet_maintenance.science.scheduling.constraints import validate_input, validate_result


def simulate_plan(
    source: PlanningInput,
    assignments: tuple[Assignment, ...],
    *,
    duration_multiplier: float = 1,
) -> dict[str, object]:
    if duration_multiplier < 1 or duration_multiplier > 2:
        raise ValueError("Duration scenario multiplier must be between one and two")
    violations = validate_input(source) + validate_result(
        source, PlanningResult("feasible", assignments)
    )
    if violations:
        raise ValueError("Invalid simulation plan: " + "; ".join(violations))
    env = simpy.Environment()
    slot = source.slot_duration_hours
    horizon = source.horizon * slot
    trace: list[dict[str, object]] = []
    units = {
        (r.id, unit): simpy.Resource(env, capacity=1)
        for r in source.resources
        for unit in range(r.capacity)
    }
    tasks = {task.id: task for task in source.tasks}
    completed_at: dict[str, float] = {}
    completions = {task.id: env.event() for task in source.tasks}
    starts: dict[str, float] = {}
    resource_window_violations: list[str] = []
    for arrival in source.part_arrivals:
        trace.append(
            {
                "task_id": arrival.part_id,
                "event": "expected_delivery",
                "hour": arrival.slot * slot,
                "quantity": arrival.quantity,
            }
        )

    def work(assignment: Assignment):  # type: ignore[no-untyped-def]
        task = tasks[assignment.task_id]
        planned = assignment.start * slot
        yield env.timeout(planned)
        for predecessor in task.predecessors:
            yield completions[predecessor]
        requests = []
        # Acquire in one global order so overrun scenarios cannot deadlock on partial claims.
        keys = sorted(
            (identifier, unit)
            for identifier, unit in (
                (assignment.crew_id, assignment.crew_unit),
                (assignment.bay_id, assignment.bay_unit),
            )
            if identifier is not None
        )
        for key in keys:
            request = units[key].request()
            requests.append(request)
            yield request
        started = float(env.now)
        starts[task.id] = started
        finish = started + task.duration * slot * duration_multiplier
        trace.append(
            {
                "task_id": task.id,
                "event": "started",
                "hour": started,
                "planned_hour": planned,
                "crew_id": assignment.crew_id,
                "bay_id": assignment.bay_id,
            }
        )
        for resource in source.resources:
            if resource.id in {assignment.crew_id, assignment.bay_id} and (
                finish > resource.valid_until * slot
                or not any(
                    left * slot <= started and finish <= right * slot
                    for left, right in resource.available
                )
            ):
                resource_window_violations.append(task.id + ":" + resource.id)
        yield env.timeout(task.duration * slot * duration_multiplier)
        for request in requests:
            request.resource.release(request)
        completed_at[task.id] = float(env.now)
        trace.append({"task_id": task.id, "event": "completed", "hour": float(env.now)})
        completions[task.id].succeed()

    for assignment in sorted(assignments, key=lambda a: (a.start, a.task_id)):
        env.process(work(assignment))
    # Execute starts at the horizon for zero work? Valid tasks have start < horizon.
    env.run(until=horizon + 0.000001)
    # Every released task grounds its aircraft, including work still waiting at the horizon.
    intervals: dict[str, list[tuple[float, float]]] = {}
    for task in source.tasks:
        aircraft = task.aircraft_id or task.component_id or task.id
        intervals.setdefault(aircraft, []).append(
            (task.earliest * slot, min(float(horizon), completed_at.get(task.id, horizon)))
        )
    waits = [max(0.0, starts.get(a.task_id, horizon) - a.start * slot) for a in assignments]
    downtime = 0.0
    for aircraft_intervals in intervals.values():
        right = 0.0
        for left, end in sorted(aircraft_intervals):
            downtime += max(0.0, end - max(left, right))
            right = max(right, end)
    fleet = {t.aircraft_id or t.component_id or t.id for t in source.tasks}
    denominator = len(fleet) * horizon
    return {
        "availability": None if not denominator else 1 - downtime / denominator,
        "downtime_aircraft_hours": downtime,
        "exposure_aircraft_hours": denominator,
        "resource_wait_hours": sum(waits),
        "completed_tasks": len(completed_at),
        "late_tasks": sum(
            completed_at.get(t.id, float("inf")) > t.deadline * slot for t in source.tasks
        ),
        "resource_window_violations": sorted(resource_window_violations),
        "trace": sorted(
            trace, key=lambda event: (float(str(event["hour"])), str(event["task_id"]))
        ),
        "cost": None,
    }


def compare_plan(source: PlanningInput, assignments: tuple[Assignment, ...]) -> dict[str, object]:
    baseline = fifo_schedule(source)
    cases = []
    for name, multiplier in (
        ("declared duration", 1.0),
        ("25% overrun", 1.25),
        ("50% overrun", 1.5),
    ):
        actual = simulate_plan(source, assignments, duration_multiplier=multiplier)
        reference = (
            simulate_plan(source, baseline.assignments, duration_multiplier=multiplier)
            if baseline.status == "feasible"
            else None
        )
        cases.append(
            {
                "name": name,
                "duration_multiplier": multiplier,
                "actual": actual,
                "baseline": reference,
                "downtime_difference_hours": None
                if reference is None
                else float(str(actual["downtime_aircraft_hours"]))
                - float(str(reference["downtime_aircraft_hours"])),
            }
        )
    return {
        "method": "actual-plan-assumption-scenarios-v1",
        "label": "simulated projection",
        "baseline_policy": "earliest-release FIFO with identical hard constraints",
        "baseline_status": baseline.status,
        "baseline_diagnostics": baseline.diagnostics,
        "baseline_assignments": [asdict(a) for a in baseline.assignments],
        "cases": cases,
        "availability_definition": "Aircraft unavailable from task earliest release to completion; "
        "overlapping grounding intervals count once per aircraft, over the recorded horizon.",
        "failure_model": None,
        "cost_inputs": None,
        "randomness": "deterministic scenario envelope",
        "limitations": "Overruns are assumption-based sensitivity, not probabilities. "
        "Resource-window overruns are reported as violations; this stress replay does not "
        "authorize overtime or replan automatically. Expected deliveries follow the frozen "
        "snapshot; cancellation or delivery changes require a new plan and comparison. "
        "No failure or airworthiness model is inferred.",
    }
