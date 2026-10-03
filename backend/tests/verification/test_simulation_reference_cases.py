from fleet_maintenance.science.simulation.environment import ScenarioInput
from fleet_maintenance.science.simulation.replications import run_scenario


def test_single_aircraft_reference_case():
    result = run_scenario(ScenarioInput(10, 1, 1, ((2, 3),)))
    assert result.completed_events == 1
    assert result.downtime_aircraft_hours == 3
    assert result.availability == 0.7


def test_capacity_queue_increases_downtime():
    one = run_scenario(ScenarioInput(10, 2, 1, ((0, 3), (0, 3))))
    two = run_scenario(ScenarioInput(10, 2, 2, ((0, 3), (0, 3))))
    assert one.downtime_aircraft_hours == 9
    assert two.downtime_aircraft_hours == 6
    assert one.queue_wait_hours == 3
    assert two.queue_wait_hours == 0


def test_event_crossing_horizon_counts_partial_downtime():
    result = run_scenario(ScenarioInput(10, 1, 1, ((8, 5),)))
    assert result.completed_events == 0
    assert result.downtime_aircraft_hours == 2
    assert result.availability == 0.8


def test_reference_contract_rejects_more_events_than_aircraft():
    import pytest

    with pytest.raises(ValueError, match="at most one event per aircraft"):
        run_scenario(ScenarioInput(10, 1, 1, ((1, 1), (4, 1))))
