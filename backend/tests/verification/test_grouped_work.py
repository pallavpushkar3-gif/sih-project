from fleet_maintenance.science.scheduling.constraints import validate_result
from fleet_maintenance.science.scheduling.formulation import PlanningInput, TaskInput
from fleet_maintenance.science.scheduling.solver import solve


def test_grouped_work_is_contiguous_without_reducing_required_duration():
    source = PlanningInput(
        14,
        (
            TaskInput("first", 2, 0, 8, "engine", component_id="component", group_id="grounding"),
            TaskInput("second", 3, 2, 10, "engine", component_id="component", group_id="grounding"),
        ),
        {"engine": 1},
        {},
    )
    result = solve(source)
    assert result.status == "optimal"
    assert not validate_result(source, result)
    first, second = result.assignments
    assert first.end == second.start and second.end - first.start == 5


def test_grouping_rejects_incompatible_components_and_windows():
    source = PlanningInput(
        14,
        (
            TaskInput("first", 2, 0, 3, "engine", component_id="a", group_id="grounding"),
            TaskInput("second", 3, 10, 14, "engine", component_id="b", group_id="grounding"),
        ),
        {"engine": 1},
        {},
    )
    result = solve(source)
    assert result.status == "invalid"
    assert any("one component" in reason for reason in result.diagnostics)
    assert any("windows" in reason for reason in result.diagnostics)
