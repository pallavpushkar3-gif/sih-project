from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioInput:
    horizon_hours: float
    aircraft_count: int
    maintenance_capacity: int
    maintenance_events: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class SimulationResult:
    availability: float
    downtime_aircraft_hours: float
    queue_wait_hours: float
    completed_events: int
    seed: int
