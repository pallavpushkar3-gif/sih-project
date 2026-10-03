from fleet_maintenance.science.scheduling.formulation import PlanningInput, PlanningResult


def result_summary(source: PlanningInput, result: PlanningResult) -> dict[str, object]:
    return {
        "status": result.status,
        "task_count": len(source.tasks),
        "assignment_count": len(result.assignments),
        "objective": result.objective,
        "best_bound": result.best_bound,
        "diagnostics": list(result.diagnostics),
    }
