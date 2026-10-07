"""Cannibalization planner ("Frankenstein solver").

Grounded aircraft that are blocked only by a missing part can be unblocked by moving a
serviceable unit of the same type from another grounded aircraft. This module picks those
swaps greedily to unblock as many aircraft as possible with the least labour, then checks
the greedy answer against the exact optimum.

Rules:
- Recipients are grounded aircraft whose open work is waiting for a part: agency work in the
  awaiting-spares phase, or started workspace work whose part request is still open or ordered.
- Donors are grounded aircraft that will not be unblocked by this plan. A donor gives up a
  component of the needed type only if it is healthy (state healthy, health index >= 80) and
  not itself under work. Mission-capable aircraft are never robbed.
- Parts that Project Forge can print are not robbed: printing takes ``PRINT_DAYS``.
- Parts arriving through supply within ``MIN_WAIT_DAYS`` are not robbed either.
- An aircraft counts as unblocked only when every part it waits for is covered.

Labour is an assumption on synthetic data: removing a unit and fitting it each take
``SWAP_SHARE`` of the type's repair effort, and a cross-base move adds handling time.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore[import-untyped]

from fleet_maintenance.science.fleet.bundle import FleetBundle
from fleet_maintenance.science.fleet.catalog import PRINT_DAYS
from fleet_maintenance.science.fleet.decisions import (
    AVAILABILITY_STATES,
    MAN_HOURS_PER_REPAIR_DAY,
    Overlay,
    component_states,
    effective_aircraft_state,
    open_recorded,
)

SWAP_SHARE = 0.25  # assumption: removal or fitting is a quarter of the type's repair effort
CROSS_BASE_HOURS = 6.0  # assumption: packing, transport handling and receipt inspection
DONOR_MIN_HI = 80.0
MIN_WAIT_DAYS = 3.0  # a part arriving sooner than this is not worth a robbery
EXACT_LIMIT = 14  # recipients; above this the exact check is skipped
_INFEASIBLE = 1e9


@dataclass(frozen=True)
class Need:
    aircraft: str
    type_code: str
    part_number: str
    component_id: str | None
    work_order: str
    wait_days: float  # days until the part would arrive through supply


@dataclass(frozen=True)
class Donor:
    aircraft: str
    component_id: str
    type_code: str
    hi: float
    base: str


def _hours(type_row: dict[str, Any]) -> float:
    return round(float(type_row["repair_days"]) * MAN_HOURS_PER_REPAIR_DAY * SWAP_SHARE, 1)


def _swap_hours(bundle: FleetBundle, need: Need, donor: Donor) -> float:
    type_row = bundle.types[bundle.part_index[need.part_number]]
    base = bundle.aircraft[bundle.aircraft_index[need.aircraft]]["base"]
    return round(2 * _hours(type_row) + (CROSS_BASE_HOURS if donor.base != base else 0.0), 1)


def _wait_days(bundle: FleetBundle, day: int, part_number: str) -> float:
    arrivals = [r["arrival_day"] - day for r in bundle.receipts_after(day)
                if r["part"] == part_number and r["arrival_day"] > day]
    lead = float(bundle.types[bundle.part_index[part_number]]["lead_time_days"])
    return float(min(arrivals)) if arrivals else lead


def gather(bundle: FleetBundle, offset: int, overlay: Overlay) -> dict[str, Any]:
    """Grounded aircraft, the parts they wait for, and the healthy units that could donate."""
    day = bundle.replay_start_day + offset
    states = effective_aircraft_state(bundle, offset, overlay)
    grounded = {bundle.aircraft[i]["id"] for i, value in enumerate(states) if value > 0}
    needs: list[Need] = []
    for wo in open_recorded(bundle, day + 1, overlay):
        if wo["aircraft"] in grounded and wo["part"] is not None and \
                bundle.work_order_phase(wo, day) == "awaiting_spares":
            slot = wo["slot"]
            needs.append(Need(
                wo["aircraft"], bundle.types[bundle.part_index[wo["part"]]]["code"], wo["part"],
                bundle.slots[slot]["id"] if slot is not None else None, wo["id"],
                _wait_days(bundle, day, wo["part"])))
    for work in overlay.in_work():
        if work.get("part") and overlay.parts_status(work["id"]) in ("open", "ordered"):
            needs.append(Need(
                work["aircraft"], bundle.types[bundle.part_index[work["part"]]]["code"],
                work["part"], work.get("component_id"), work["id"],
                _wait_days(bundle, day, work["part"])))
    rows = component_states(bundle, offset, overlay)
    needed_components = {n.component_id for n in needs}
    donors = [
        Donor(r["aircraft"], r["id"], r["type"], r["hi"],
              bundle.aircraft[bundle.aircraft_index[r["aircraft"]]]["base"])
        for r in rows
        if r["aircraft"] in grounded and r["state"] == "healthy" and r["hi"] >= DONOR_MIN_HI
        and r["work_order"] is None and r["id"] not in needed_components
    ]
    return {"day": day, "states": states, "grounded": grounded, "needs": needs, "donors": donors}


def _assign(bundle: FleetBundle, needs: list[Need],
            donors: list[Donor]) -> tuple[list[tuple[Need, Donor]], float] | None:
    """Least-labour assignment covering every need, or None if one cannot be covered."""
    if not needs:
        return [], 0.0
    if not donors:
        return None
    cost = np.full((len(needs), len(donors)), _INFEASIBLE)
    for i, need in enumerate(needs):
        for j, donor in enumerate(donors):
            if donor.type_code == need.type_code and donor.aircraft != need.aircraft:
                cost[i, j] = _swap_hours(bundle, need, donor)
    if len(needs) > len(donors):
        return None
    rows, cols = linear_sum_assignment(cost)
    if any(cost[r, c] >= _INFEASIBLE for r, c in zip(rows, cols, strict=True)):
        return None
    pairs = [(needs[r], donors[c]) for r, c in zip(rows, cols, strict=True)]
    return pairs, round(float(sum(cost[r, c] for r, c in zip(rows, cols, strict=True))), 1)


def greedy(bundle: FleetBundle, needs_by_aircraft: dict[str, list[Need]],
           donors: list[Donor]) -> tuple[list[str], list[tuple[Need, Donor]]]:
    """Unblock the cheapest aircraft first; prefer donors already robbed (concentrate the
    damage on one hangar queen), then the cheapest swap."""
    restored: list[str] = []
    swaps: list[tuple[Need, Donor]] = []
    used: set[str] = set()
    robbed: defaultdict[str, int] = defaultdict(int)

    def cheapest(need: Need, blocked: set[str]) -> Donor | None:
        options = [d for d in donors if d.type_code == need.type_code and d.component_id not in used
                   and d.aircraft not in blocked and d.aircraft != need.aircraft]
        if not options:
            return None
        return min(options, key=lambda d: (-robbed[d.aircraft], _swap_hours(bundle, need, d),
                                           -d.hi, d.component_id))

    def estimate(aircraft: str) -> float:
        hours = []
        for need in needs_by_aircraft[aircraft]:
            donor = cheapest(need, set(restored) | {aircraft})
            hours.append(_swap_hours(bundle, need, donor) if donor else _INFEASIBLE)
        return sum(hours)

    pending = sorted(needs_by_aircraft, key=lambda a: (len(needs_by_aircraft[a]), estimate(a), a))
    for aircraft in pending:
        blocked = set(restored) | {aircraft}
        # A donor already giving a part keeps its place; an aircraft that donated cannot be
        # unblocked later in the same plan.
        if robbed[aircraft]:
            continue
        chosen: list[tuple[Need, Donor]] = []
        taken: set[str] = set()
        for need in needs_by_aircraft[aircraft]:
            options = [d for d in donors if d.type_code == need.type_code
                       and d.component_id not in used | taken
                       and d.aircraft not in blocked and d.aircraft != need.aircraft]
            if not options:
                chosen = []
                break
            donor = min(options, key=lambda d: (-robbed[d.aircraft], _swap_hours(bundle, need, d),
                                                -d.hi, d.component_id))
            chosen.append((need, donor))
            taken.add(donor.component_id)
        if not chosen:
            continue
        restored.append(aircraft)
        for need, donor in chosen:
            used.add(donor.component_id)
            robbed[donor.aircraft] += 1
            swaps.append((need, donor))
    return restored, swaps


def exact(bundle: FleetBundle, needs_by_aircraft: dict[str, list[Need]],
          donors: list[Donor]) -> tuple[int, float, list[tuple[Need, Donor]]] | None:
    """Most aircraft unblocked, then least labour, by trying every recipient subset."""
    recipients = sorted(needs_by_aircraft)
    if len(recipients) > EXACT_LIMIT:
        return None
    for size in range(len(recipients), -1, -1):
        best: tuple[list[tuple[Need, Donor]], float] | None = None
        for subset in combinations(recipients, size):
            chosen = set(subset)
            result = _assign(
                bundle, [n for a in subset for n in needs_by_aircraft[a]],
                [d for d in donors if d.aircraft not in chosen])
            if result is not None and (best is None or result[1] < best[1]):
                best = result
        if best is not None:
            return size, best[1], best[0]
    return 0, 0.0, []


def strategy(bundle: FleetBundle, offset: int, overlay: Overlay) -> dict[str, Any]:
    found = gather(bundle, offset, overlay)
    needs: list[Need] = found["needs"]
    donors: list[Donor] = found["donors"]
    printable = {t["code"] for i, t in enumerate(bundle.types) if bundle.printable[i]}
    forge = [n for n in needs if n.type_code in printable]
    arriving = [n for n in needs if n.type_code not in printable and n.wait_days < MIN_WAIT_DAYS]
    by_aircraft: dict[str, list[Need]] = defaultdict(list)
    for need in needs:
        if need.type_code not in printable and need.wait_days >= MIN_WAIT_DAYS:
            by_aircraft[need.aircraft].append(need)
    restored, swaps = greedy(bundle, by_aircraft, donors)
    labour = round(sum(_swap_hours(bundle, n, d) for n, d in swaps), 1)
    greedy_result = (len(restored), labour)
    optimum = exact(bundle, by_aircraft, donors)
    greedy_optimal = optimum is not None and optimum[0] == len(restored) and \
        abs(optimum[1] - labour) < 0.05
    plan_source = "greedy"
    if optimum is not None and not greedy_optimal:
        # Greedy is a heuristic; when the exact search finds a better plan, return that one.
        swaps = optimum[2]
        restored = sorted({n.aircraft for n, _ in swaps})
        labour = round(optimum[1], 1)
        plan_source = "exact"

    names = {t["code"]: t["name"] for t in bundle.types}
    sequence: list[dict[str, Any]] = []
    swap_rows: list[dict[str, Any]] = []
    for index, (need, donor) in enumerate(swaps, start=1):
        type_row = bundle.types[bundle.part_index[need.part_number]]
        hours = _hours(type_row)
        transfer = _swap_hours(bundle, need, donor) - 2 * hours
        name = names[need.type_code]
        swap_rows.append({
            "swap": index, "part_number": need.part_number, "component_type": need.type_code,
            "component_name": name, "donor": donor.aircraft, "donor_component": donor.component_id,
            "donor_health_index": donor.hi, "recipient": need.aircraft,
            "recipient_component": need.component_id, "work_order": need.work_order,
            "labor_hours": round(2 * hours + transfer, 1), "cross_base": transfer > 0,
            "supply_wait_avoided_days": round(need.wait_days, 1),
            "donor_new_wait_days": float(type_row["lead_time_days"]),
            "text": f"Remove {name} from {donor.aircraft}, install on {need.aircraft}",
        })
        sequence.append({"step": len(sequence) + 1, "action": "remove", "aircraft": donor.aircraft,
                         "component_id": donor.component_id, "part_number": need.part_number,
                         "component_name": name, "labor_hours": hours, "swap": index})
        if transfer:
            sequence.append({"step": len(sequence) + 1, "action": "transfer",
                             "aircraft": need.aircraft, "component_id": donor.component_id,
                             "part_number": need.part_number, "component_name": name,
                             "labor_hours": transfer, "swap": index})
        sequence.append({"step": len(sequence) + 1, "action": "install", "aircraft": need.aircraft,
                         "component_id": need.component_id, "part_number": need.part_number,
                         "component_name": name, "labor_hours": hours, "swap": index})

    robbed: defaultdict[str, list[str]] = defaultdict(list)
    for _, donor in swaps:
        robbed[donor.aircraft].append(donor.component_id)
    unmet = [
        {"aircraft": need.aircraft, "part_number": need.part_number,
         "component_name": names[need.type_code], "work_order": need.work_order,
         "supply_wait_days": round(need.wait_days, 1),
         "reason": "No healthy unit of this type on another grounded aircraft"
         if not any(d.type_code == need.type_code and d.aircraft != need.aircraft for d in donors)
         else "Units exist but are needed for aircraft the plan unblocks"}
        for aircraft, items in sorted(by_aircraft.items()) if aircraft not in restored
        for need in items
    ] + [
        {"aircraft": need.aircraft, "part_number": need.part_number,
         "component_name": names[need.type_code], "work_order": need.work_order,
         "supply_wait_days": round(need.wait_days, 1),
         "reason": f"Part arrives through supply within {MIN_WAIT_DAYS:g} days; a swap would "
         "not return the aircraft sooner"}
        for need in arriving
    ]
    states = found["states"]
    grounded_rows = []
    for aircraft in sorted(found["grounded"]):
        index = bundle.aircraft_index[aircraft]
        waits = [n.part_number for n in needs if n.aircraft == aircraft]
        grounded_rows.append({
            "aircraft": aircraft, "state": AVAILABILITY_STATES[int(states[index])],
            "base": bundle.aircraft[index]["base"], "waiting_for": waits,
            "role": "recipient" if aircraft in restored else
            "donor" if aircraft in robbed else "blocked" if aircraft in by_aircraft else "other",
        })

    used = [d.component_id for _, d in swaps]
    available = int((states == 0).sum())
    verification = {
        "no_unit_used_twice": len(used) == len(set(used)),
        "types_match": all(n.type_code == d.type_code for n, d in swaps),
        "donors_grounded": all(d.aircraft in found["grounded"] for _, d in swaps),
        "donors_not_unblocked": not (set(robbed) & set(restored)),
        "recipients_fully_covered": all(
            sum(1 for n, _ in swaps if n.aircraft == a) == len(by_aircraft[a]) for a in restored),
        "greedy_unblocked": greedy_result[0],
        "greedy_labor_hours": greedy_result[1],
        "optimal_unblocked": optimum[0] if optimum else None,
        "optimal_labor_hours": round(optimum[1], 1) if optimum else None,
        "greedy_is_optimal": greedy_optimal if optimum else None,
        "plan_source": plan_source,
        "exact_method": "every recipient subset, least-labour assignment by the Hungarian "
        "algorithm (scipy linear_sum_assignment)" if optimum else
        f"skipped: more than {EXACT_LIMIT} recipients",
    }
    return {
        "as_of": bundle.date_of(found["day"]).isoformat(),
        "fleet_size": len(bundle.aircraft),
        "available_now": available,
        "grounded": grounded_rows,
        "aircraft_unblocked": restored,
        "available_after_repairs": available + len(restored),
        "total_labor_hours": labour,
        "swaps": swap_rows,
        "sequence": sequence,
        "hangar_queens": [{"aircraft": a, "components_removed": c}
                          for a, c in sorted(robbed.items(), key=lambda kv: -len(kv[1]))],
        "forge": [{"aircraft": n.aircraft, "part_number": n.part_number,
                   "component_name": names[n.type_code], "work_order": n.work_order,
                   "print_days": PRINT_DAYS} for n in forge],
        "unmet": unmet,
        "verification": verification,
        "method": "Greedy: unblock aircraft needing the fewest parts first, concentrate removals "
        "on donors already robbed, then pick the cheapest swap. Checked against the exact "
        "optimum (most aircraft unblocked, then least labour); if the exact plan is better, "
        "it is returned instead.",
        "assumptions": [
            f"Removal and fitting each take {SWAP_SHARE:.0%} of the type's repair effort at "
            f"{MAN_HOURS_PER_REPAIR_DAY:g} man-hours per repair day.",
            f"Moving a unit between bases adds {CROSS_BASE_HOURS:g} man-hours of handling.",
            f"Donor units must be healthy with health index >= {DONOR_MIN_HI:g}; mission-capable "
            "aircraft are never robbed.",
            f"No swap is proposed when the part arrives through supply within {MIN_WAIT_DAYS:g} "
            "days.",
            "Unblocked aircraft still need their repair time in the bay before they fly.",
            "Each removed unit leaves the donor waiting for that part through normal supply.",
            "Synthetic data. A cannibalization needs engineering approval and records "
            "transfer in the aircraft documents.",
        ],
    }
