from dataclasses import asdict, dataclass
from statistics import fmean, stdev

from fleet_maintenance.science.simulation.environment import SimulationResult


@dataclass(frozen=True)
class SimulationSummary:
    replications: int
    mean_availability: float
    mean_downtime_aircraft_hours: float
    mean_queue_wait_hours: float
    availability_standard_deviation: float | None
    minimum_availability: float
    maximum_availability: float

    def as_dict(self) -> dict[str, int | float | None]:
        return asdict(self)


def summarize(results: tuple[SimulationResult, ...]) -> SimulationSummary:
    if not results:
        raise ValueError("At least one simulation result is required.")
    availability = [result.availability for result in results]
    return SimulationSummary(
        replications=len(results),
        mean_availability=fmean(availability),
        mean_downtime_aircraft_hours=fmean(
            result.downtime_aircraft_hours for result in results
        ),
        mean_queue_wait_hours=fmean(result.queue_wait_hours for result in results),
        availability_standard_deviation=stdev(availability) if len(results) > 1 else None,
        minimum_availability=min(availability),
        maximum_availability=max(availability),
    )
