from dataclasses import dataclass

from fleet_maintenance.science.simulation.environment import ScenarioInput
from fleet_maintenance.science.simulation.metrics import SimulationSummary


@dataclass(frozen=True)
class PolicyComparison:
    baseline: SimulationSummary
    candidate: SimulationSummary
    availability_delta: float
    downtime_delta_aircraft_hours: float
    queue_wait_delta_hours: float


def assert_comparable(baseline: ScenarioInput, candidate: ScenarioInput) -> None:
    if baseline.horizon_hours != candidate.horizon_hours:
        raise ValueError("Scenario horizons differ.")
    if baseline.aircraft_count != candidate.aircraft_count:
        raise ValueError("Scenario fleet mappings differ.")
    if baseline.maintenance_events != candidate.maintenance_events:
        raise ValueError("Scenario maintenance events differ.")


def compare(
    baseline_input: ScenarioInput,
    baseline: SimulationSummary,
    candidate_input: ScenarioInput,
    candidate: SimulationSummary,
) -> PolicyComparison:
    assert_comparable(baseline_input, candidate_input)
    if baseline.replications != candidate.replications:
        raise ValueError("Scenario replication counts differ.")
    return PolicyComparison(
        baseline,
        candidate,
        candidate.mean_availability - baseline.mean_availability,
        candidate.mean_downtime_aircraft_hours - baseline.mean_downtime_aircraft_hours,
        candidate.mean_queue_wait_hours - baseline.mean_queue_wait_hours,
    )
