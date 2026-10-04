import pytest

from fleet_maintenance.science.simulation.environment import ScenarioInput
from fleet_maintenance.science.simulation.replications import run_scenario


def test_delivery_wait_extends_grounding_without_using_bay_capacity():
    baseline = run_scenario(ScenarioInput(24, 2, 1, ((0, 2), (0, 2))))
    delayed = run_scenario(ScenarioInput(24, 2, 1, ((0, 2), (0, 2)), 5))
    assert baseline.downtime_aircraft_hours == 6
    assert delayed.downtime_aircraft_hours == 16
    assert delayed.part_wait_hours == 10
    assert delayed.queue_wait_hours == baseline.queue_wait_hours == 2
    assert delayed.completed_events == 2
    assert delayed.availability == pytest.approx(32 / 48)


def test_delivery_after_one_event_changes_only_waiting_event():
    result = run_scenario(ScenarioInput(24, 2, 2, ((0, 2), (10, 2)), 5))
    assert result.part_wait_hours == 5
    assert result.queue_wait_hours == 0
    assert result.downtime_aircraft_hours == 9
