"""Bounded synthetic benchmark for resources; no operator workload acceptance."""

import platform
import time
from dataclasses import asdict

from fleet_maintenance.domain.contracts.planning import PlanningInput, ResourceInput, TaskInput
from fleet_maintenance.science.scheduling.baseline import fifo_schedule
from fleet_maintenance.science.scheduling.constraints import validate_result
from fleet_maintenance.science.scheduling.solver import solve


def run_benchmark() -> dict[str, object]:
    instances = []
    for count in (4, 8, 16, 24):
        source = PlanningInput(
            14,
            tuple(
                TaskInput(f"task-{i:02}", 1 + i % 2, 0, 14, "engine", aircraft_id=f"aircraft-{i}")
                for i in range(count)
            ),
            {"engine": 2},
            {},
            resources=(
                ResourceInput("crew", "crew", ("engine",), ((0, 4), (6, 14)), capacity=2),
                ResourceInput("bay", "bay", ("engine",), ((0, 14),), capacity=2),
            ),
        )
        measurements = []
        for _ in range(5):
            start = time.perf_counter()
            result = solve(source)
            runtime = time.perf_counter() - start
            if result.status in {"optimal", "feasible"}:
                assert not validate_result(source, result)
            measurements.append({"runtime_seconds": runtime, **asdict(result)})
        baseline = fifo_schedule(source)
        instances.append(
            {
                "tasks": count,
                "source": asdict(source),
                "optimizer": measurements,
                "FIFO": asdict(baseline),
            }
        )
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scope": "synthetic 112-hour grid, two crew/bay units, crew closure hours 32–48",
        "instances": instances,
        "acceptance": "constraint checks only; customer scaling pending",
    }
