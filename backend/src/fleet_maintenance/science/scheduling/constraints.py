from fleet_maintenance.science.scheduling.formulation import PlanningInput, PlanningResult


def validate_input(value: PlanningInput) -> list[str]:
    errors: list[str] = []
    if value.horizon <= 0:
        errors.append("Planning horizon must be positive.")
    seen: set[str] = set()
    required_parts: dict[str, int] = {}
    for task in value.tasks:
        if task.id in seen:
            errors.append(f"Duplicate task: {task.id}")
        seen.add(task.id)
        if task.duration <= 0 or task.earliest < 0 or task.deadline > value.horizon:
            errors.append(f"Invalid window for task {task.id}.")
        if task.earliest + task.duration > task.deadline:
            errors.append(f"Task {task.id} cannot fit in its window.")
        if task.fixed_start is not None and not (
            task.earliest <= task.fixed_start
            and task.fixed_start + task.duration <= task.deadline
        ):
            errors.append(f"Fixed start for task {task.id} is outside its window.")
        if value.skill_capacity.get(task.skill, 0) <= 0:
            errors.append(f"No capacity for skill {task.skill}.")
        if task.part_quantity < 0 or (task.part_quantity and not task.part_id):
            errors.append(f"Invalid part requirement for task {task.id}.")
        if task.part_id:
            required_parts[task.part_id] = required_parts.get(task.part_id, 0) + task.part_quantity
    for task in value.tasks:
        unknown = set(task.predecessors) - seen
        if unknown:
            errors.append(f"Task {task.id} has unknown predecessors: {', '.join(sorted(unknown))}.")
        if task.id in task.predecessors:
            errors.append(f"Task {task.id} cannot precede itself.")
    for part_id, quantity in required_parts.items():
        if value.part_stock.get(part_id, 0) < quantity:
            errors.append(f"Insufficient aggregate stock for part {part_id}.")
    return errors


def validate_result(source: PlanningInput, result: PlanningResult) -> list[str]:
    errors: list[str] = []
    by_id = {task.id: task for task in source.tasks}
    assigned = {item.task_id: item for item in result.assignments}
    if set(assigned) != set(by_id):
        errors.append("Assignments do not cover exactly the input tasks.")
    for task_id, assignment in assigned.items():
        task = by_id.get(task_id)
        if task and (assignment.start < task.earliest or assignment.end > task.deadline):
            errors.append(f"Task {task_id} violates its time window.")
        if task and assignment.end - assignment.start != task.duration:
            errors.append(f"Task {task_id} has an invalid duration.")
        if task and task.fixed_start is not None and assignment.start != task.fixed_start:
            errors.append(f"Task {task_id} moved from its fixed commitment.")
        if task:
            for predecessor_id in task.predecessors:
                predecessor = assigned.get(predecessor_id)
                if predecessor and predecessor.end > assignment.start:
                    errors.append(
                        f"Task {task_id} starts before predecessor {predecessor_id} completes."
                    )
    for skill, capacity in source.skill_capacity.items():
        relevant = [
            (assigned[t.id], t) for t in source.tasks if t.skill == skill and t.id in assigned
        ]
        for slot in range(source.horizon):
            if sum(a.start <= slot < a.end for a, _ in relevant) > capacity:
                errors.append(f"Skill {skill} exceeds capacity at slot {slot}.")
    return errors
