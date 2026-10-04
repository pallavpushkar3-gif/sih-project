from dataclasses import replace

import pytest

from fleet_maintenance.domain.contracts.planning import (
    Assignment,
    PlanningInput,
    ResourceInput,
    TaskInput,
)
from fleet_maintenance.science.simulation.plan_comparison import compare_plan, simulate_plan


def inputs() -> PlanningInput:
    return PlanningInput(
        8,
        (TaskInput("t", 2, 0, 8, "engine", aircraft_id="aircraft"),),
        {"engine": 1},
        {},
        resources=(
            ResourceInput("crew", "crew", ("engine",), ((0, 8),), valid_until=8),
            ResourceInput("bay", "bay", ("engine",), ((0, 8),), valid_until=8),
        ),
    )


def test_changed_actual_plan_changes_trace_and_can_be_worse_than_baseline():
    source = inputs()
    early = (Assignment("t", 0, 2, "crew", "bay"),)
    late = (replace(early[0], start=3, end=5),)
    first = simulate_plan(source, early)
    second = simulate_plan(source, late)
    assert first["downtime_aircraft_hours"] == 16
    assert second["downtime_aircraft_hours"] == 40
    assert second["trace"][0]["hour"] == 24
    comparison = compare_plan(source, late)
    assert comparison["cases"][0]["downtime_difference_hours"] == 24
    assert comparison["failure_model"] is None


def test_equal_schedule_shows_zero_benefit_and_cost_is_unknown():
    result = compare_plan(inputs(), (Assignment("t", 0, 2, "crew", "bay"),))
    assert result["cases"][0]["downtime_difference_hours"] == 0
    assert result["cases"][0]["actual"]["cost"] is None


def test_invalid_plan_is_not_simulated():
    with pytest.raises(ValueError, match="eligible assigned bay"):
        simulate_plan(inputs(), (Assignment("t", 0, 2, "crew", "unknown"),))


def test_waiting_work_remains_grounded_at_horizon_and_overrun_is_visible():
    source = replace(
        inputs(),
        horizon=4,
        tasks=(
            TaskInput("first", 2, 0, 4, "engine", aircraft_id="one"),
            TaskInput("waiting", 2, 0, 4, "engine", aircraft_id="two"),
        ),
        resources=tuple(replace(r, available=((0, 4),), valid_until=4) for r in inputs().resources),
    )
    result = simulate_plan(
        source,
        (
            Assignment("first", 0, 2, "crew", "bay"),
            Assignment("waiting", 2, 4, "crew", "bay"),
        ),
        duration_multiplier=2,
    )
    assert result["downtime_aircraft_hours"] == 64
    assert result["completed_tasks"] == 1
    assert result["late_tasks"] == 1
    assert "waiting:crew" in result["resource_window_violations"]
