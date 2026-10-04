from fleet_maintenance.science.scheduling.formulation import PlanningInput, PlanningResult
from fleet_maintenance.science.scheduling.grouping import groups, validate_groups
from fleet_maintenance.science.scheduling.resources import compatible


def validate_input(value: PlanningInput) -> list[str]:
    errors: list[str] = []
    if value.horizon <= 0:
        errors.append("Planning horizon must be positive.")
    if value.slot_duration_hours <= 0:
        errors.append("Slot duration must be positive hours.")
    resource_ids: set[str] = set()
    for resource in value.resources:
        if resource.id in resource_ids:
            errors.append(f"Duplicate resource: {resource.id}")
        resource_ids.add(resource.id)
        if resource.kind not in {"crew", "bay"} or resource.capacity <= 0:
            errors.append(f"Invalid resource kind/capacity: {resource.id}")
        if resource.valid_from < 0 or resource.valid_until <= resource.valid_from:
            errors.append(f"Invalid qualification window: {resource.id}")
        if any(
            left < 0 or right <= left or right > value.horizon for left, right in resource.available
        ):
            errors.append(f"Invalid calendar window: {resource.id}")
    errors.extend(validate_groups(value))
    if any(quantity < 0 for quantity in value.part_stock.values()):
        errors.append("Part stock cannot be negative.")
    future_stock = dict(value.part_stock)
    for arrival in value.part_arrivals:
        if not arrival.part_id or arrival.quantity <= 0 or not 0 <= arrival.slot < value.horizon:
            errors.append("Part arrivals require positive quantities inside the planning horizon.")
        else:
            future_stock[arrival.part_id] = future_stock.get(arrival.part_id, 0) + arrival.quantity
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
            task.earliest <= task.fixed_start and task.fixed_start + task.duration <= task.deadline
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
        if future_stock.get(part_id, 0) < quantity:
            errors.append(f"Insufficient aggregate stock for part {part_id}.")
    return errors


def validate_result(source: PlanningInput, result: PlanningResult) -> list[str]:
    errors: list[str] = []
    by_id = {task.id: task for task in source.tasks}
    assigned = {item.task_id: item for item in result.assignments}
    resources = {resource.id: resource for resource in source.resources}
    occupancy: dict[tuple[str, int, int], str] = {}
    aircraft_occupancy: dict[tuple[str, int], str] = {}
    if len(assigned) != len(result.assignments):
        errors.append("Duplicate task assignments are not allowed.")
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
            if source.resources:
                for kind, identifier, unit in (
                    ("crew", assignment.crew_id, assignment.crew_unit),
                    ("bay", assignment.bay_id, assignment.bay_unit),
                ):
                    resource = resources.get(identifier or "")
                    if resource is None or resource.kind != kind or not compatible(resource, task):
                        errors.append(f"Task {task_id}: no eligible assigned {kind}.")
                        continue
                    if not 0 <= unit < resource.capacity:
                        errors.append(f"Task {task_id}: invalid {kind} capacity unit.")
                    if (
                        assignment.start < resource.valid_from
                        or assignment.end > resource.valid_until
                    ):
                        errors.append(f"Task {task_id}: {kind} qualification expires during work.")
                    fixed_id = task.fixed_crew_id if kind == "crew" else task.fixed_bay_id
                    fixed_unit = task.fixed_crew_unit if kind == "crew" else task.fixed_bay_unit
                    if fixed_id and unit != fixed_unit:
                        errors.append(f"Task {task_id}: committed {kind} unit changed.")
                    for slot in range(assignment.start, assignment.end):
                        if not any(left <= slot < right for left, right in resource.available):
                            errors.append(
                                f"Task {task_id}: {kind} shift/closure conflict at {slot}."
                            )
                        occupancy_key = (resource.id, unit, slot)
                        if occupancy_key in occupancy:
                            errors.append(f"Resource {resource.id} unit {unit} overlaps at {slot}.")
                        occupancy[occupancy_key] = task_id
            if task.aircraft_id:
                for slot in range(assignment.start, assignment.end):
                    aircraft_key = (task.aircraft_id, slot)
                    if aircraft_key in aircraft_occupancy:
                        errors.append(
                            f"Aircraft {task.aircraft_id} has overlapping work at {slot}."
                        )
                    aircraft_occupancy[aircraft_key] = task_id
            for predecessor_id in task.predecessors:
                predecessor = assigned.get(predecessor_id)
                if predecessor and predecessor.end > assignment.start:
                    errors.append(
                        f"Task {task_id} starts before predecessor {predecessor_id} completes."
                    )
    for key, tasks in groups(source).items():
        for previous, current in zip(tasks, tasks[1:], strict=False):
            if (
                previous.id in assigned
                and current.id in assigned
                and assigned[previous.id].end != assigned[current.id].start
            ):
                errors.append(f"Group {key} does not form contiguous work.")
    for skill, capacity in source.skill_capacity.items():
        relevant = [
            (assigned[t.id], t) for t in source.tasks if t.skill == skill and t.id in assigned
        ]
        for slot in range(source.horizon):
            if sum(a.start <= slot < a.end for a, _ in relevant) > capacity:
                errors.append(f"Skill {skill} exceeds capacity at slot {slot}.")
    for part_id in {task.part_id for task in source.tasks if task.part_id}:
        consumption = sorted(
            {
                assigned[t.id].start
                for t in source.tasks
                if t.part_id == part_id and t.id in assigned
            }
        )
        for slot in consumption:
            supplied = source.part_stock.get(part_id, 0) + sum(
                arrival.quantity
                for arrival in source.part_arrivals
                if arrival.part_id == part_id and arrival.slot <= slot
            )
            used = sum(
                t.part_quantity
                for t in source.tasks
                if t.part_id == part_id and t.id in assigned and assigned[t.id].start <= slot
            )
            if used > supplied:
                errors.append(
                    f"Part {part_id} unavailable at slot {slot}: need {used}, supplied {supplied}."
                )
    return errors
