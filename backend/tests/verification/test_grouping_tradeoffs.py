from fleet_maintenance.science.scheduling.formulation import (
    Assignment,
    PlanningInput,
    PlanningResult,
    TaskInput,
)
from fleet_maintenance.science.scheduling.solver import solve
from fleet_maintenance.science.scheduling.tradeoffs import grouping_metrics


def test_shared_grounding_retains_the_early_maintenance_cost():
    source = PlanningInput(
        10,
        (
            TaskInput(
                "a", 1, 0, 7, "engine", fixed_start=1, component_id="engine", group_id="visit"
            ),
            TaskInput("b", 2, 0, 9, "engine", component_id="engine", group_id="visit"),
        ),
        {"engine": 1},
        {},
    )
    grouped = solve(source)
    assert grouped.status == "optimal"
    grouped_metrics = grouping_metrics(source, grouped, {"a": 1, "b": 6}, 8)
    separate_source = PlanningInput(
        10,
        (
            TaskInput("a", 1, 0, 7, "engine", fixed_start=1, component_id="engine"),
            TaskInput("b", 2, 0, 9, "engine", component_id="engine"),
        ),
        {"engine": 1},
        {},
    )
    separate = PlanningResult("feasible", (Assignment("a", 1, 2), Assignment("b", 6, 8)))
    separate_metrics = grouping_metrics(separate_source, separate, {"a": 1, "b": 6}, 8)
    assert separate_metrics["component_grounding_episodes"] == 2
    assert grouped_metrics["component_grounding_episodes"] == 1
    assert grouped_metrics["grounding_slots"] == separate_metrics["grounding_slots"] == 3
    assert grouped_metrics["early_maintenance_slots"] == 4
    assert grouped_metrics["synthetic_discarded_cycles"] == 32
    assert separate_metrics["early_maintenance_slots"] == 0
