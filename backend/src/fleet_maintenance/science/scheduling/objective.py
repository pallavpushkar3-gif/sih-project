from fleet_maintenance.science.scheduling.formulation import Assignment


def makespan(assignments: tuple[Assignment, ...]) -> float:
    return float(max((assignment.end for assignment in assignments), default=0))
