from fleet_maintenance.science.scheduling.constraints import validate_result
from fleet_maintenance.science.scheduling.formulation import PlanningInput, TaskInput
from fleet_maintenance.science.scheduling.solver import solve


def test_solver_output_passes_independent_constraints():
    source = PlanningInput(
        10,
        (TaskInput("a", 3, 0, 7, "engine"), TaskInput("b", 2, 0, 8, "engine")),
        {"engine": 1},
        {},
    )
    result = solve(source)
    assert result.status == "optimal"
    assert validate_result(source, result) == []


def test_invalid_stock_is_not_mislabeled_infeasible():
    source = PlanningInput(
        10, (TaskInput("a", 1, 0, 5, "engine", "part", 2),), {"engine": 1}, {"part": 1}
    )
    assert solve(source).status == "invalid"


def test_shared_stock_is_validated_across_all_tasks():
    source = PlanningInput(
        10,
        (
            TaskInput("a", 1, 0, 5, "engine", "part", 1),
            TaskInput("b", 1, 0, 5, "engine", "part", 1),
        ),
        {"engine": 1},
        {"part": 1},
    )
    result = solve(source)
    assert result.status == "invalid"
    assert result.diagnostics == ("Insufficient aggregate stock for part part.",)


def test_precedence_and_fixed_commitment_are_preserved():
    source = PlanningInput(
        10,
        (
            TaskInput("a", 2, 0, 5, "engine", fixed_start=1),
            TaskInput("b", 2, 0, 8, "engine", predecessors=("a",)),
        ),
        {"engine": 1},
        {},
    )
    result = solve(source)
    assert result.status == "optimal"
    assert validate_result(source, result) == []
    assignments = {item.task_id: item for item in result.assignments}
    assert assignments["a"].start == 1
    assert assignments["b"].start >= assignments["a"].end


def test_empty_task_set_is_a_valid_empty_schedule():
    result = solve(PlanningInput(10, (), {"engine": 1}, {}))
    assert result.status == "optimal"
    assert result.assignments == ()
    assert result.objective == 0.0
