from dataclasses import dataclass

import simpy

from fleet_maintenance.science.simulation.environment import ScenarioInput, SimulationResult


@dataclass
class _EventTrace:
    arrival: float
    start: float | None = None
    end: float | None = None


def run_scenario(source: ScenarioInput, seed: int = 26249) -> SimulationResult:
    if source.horizon_hours <= 0 or source.aircraft_count <= 0 or source.maintenance_capacity <= 0:
        raise ValueError("Scenario dimensions and capacities must be positive.")
    if len(source.maintenance_events) > source.aircraft_count:
        raise ValueError("The reference scenario supports at most one event per aircraft.")
    for arrival, duration in source.maintenance_events:
        if arrival < 0 or arrival >= source.horizon_hours or duration <= 0:
            raise ValueError("Maintenance arrivals and durations must fit the scenario domain.")

    env = simpy.Environment()
    bay = simpy.Resource(env, capacity=source.maintenance_capacity)
    completed = 0
    traces: list[_EventTrace] = []

    def maintenance(arrival: float, duration: float):  # type: ignore[no-untyped-def]
        nonlocal completed
        trace = _EventTrace(arrival)
        traces.append(trace)
        yield env.timeout(arrival)
        with bay.request() as request:
            yield request
            trace.start = float(env.now)
            yield env.timeout(duration)
            trace.end = float(env.now)
            completed += 1

    for arrival, duration in source.maintenance_events:
        env.process(maintenance(arrival, duration))
    env.run(until=source.horizon_hours)
    downtime = sum(
        max(
            0.0,
            min(
                float(source.horizon_hours if trace.end is None else trace.end),
                source.horizon_hours,
            )
            - trace.arrival,
        )
        for trace in traces
    )
    queue_wait = sum(
        max(
            0.0,
            float(source.horizon_hours if trace.start is None else trace.start) - trace.arrival,
        )
        for trace in traces
    )
    possible = source.horizon_hours * source.aircraft_count
    availability = max(0.0, (possible - downtime) / possible)
    return SimulationResult(availability, downtime, queue_wait, completed, seed)
