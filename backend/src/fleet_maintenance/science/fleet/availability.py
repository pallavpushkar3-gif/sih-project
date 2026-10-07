"""Fleet availability Monte Carlo and scenario engine (docs/plan.md section 7).

A day-step discrete-event simulation over a 7-60 day horizon. Component failures are sampled
from each slot's predicted remaining-life quantiles (or, without a degradation signal, from the
calibrated 30-day risk and a type background rate). Failed or planned work then waits for a
spare and an agency bay before its repair time. Baseline and scenario runs share random numbers
so their difference reflects the intervention rather than sampling noise.

These are decision-support projections on synthetic data, not operational planning outputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from fleet_maintenance.science.fleet.catalog import PRINT_DAYS

CAUSES = ("scheduled", "unscheduled", "awaiting_spares", "awaiting_agency")


@dataclass(frozen=True)
class OpenWork:
    aircraft: int
    remaining_days: int
    cause: str
    agency: int
    in_bay: bool


@dataclass(frozen=True)
class Snapshot:
    """Immutable simulation inputs captured from one as-of state."""

    aircraft_ids: tuple[str, ...]
    slot_aircraft: np.ndarray
    slot_part: np.ndarray
    slot_agency: np.ndarray
    repair_days: np.ndarray  # expected unscheduled repair days per slot
    rul: np.ndarray  # (slots, 3) p10/p50/p90 in days, capped at 60
    risk30: np.ndarray
    background_hazard: np.ndarray  # per-day failure hazard without a degradation signal
    stock: np.ndarray  # on hand per part
    reorder_level: np.ndarray
    lead_time: np.ndarray  # days per part
    receipts: tuple[tuple[int, int, int], ...]  # (part, quantity, day offset)
    bays: np.ndarray  # per agency
    open_work: tuple[OpenWork, ...]
    inspection_due_day: np.ndarray  # per aircraft, day offset when the next inspection starts
    inspection_days: int
    inspection_agency: int
    printable: np.ndarray | None = None  # Project Forge: printed in PRINT_DAYS instead of ordered


@dataclass(frozen=True)
class Intervention:
    kind: str  # replace | spare_unavailable | extra_capacity | early_replacement
    slots: tuple[int, ...] = ()
    day: int = 0
    part: int | None = None
    lead_time_days: int | None = None
    agency: int | None = None
    extra_bays: int = 0


@dataclass
class RunSummary:
    availability: np.ndarray  # (runs, horizon) fraction available
    lost: np.ndarray  # (runs, len(CAUSES)) aircraft-days
    stockouts: np.ndarray  # (runs, parts) bool
    failures: np.ndarray  # (runs,)
    by_aircraft_lost: np.ndarray  # (runs, aircraft)

    def describe(self) -> dict[str, object]:
        p10, p50, p90 = np.percentile(self.availability, [10, 50, 90], axis=0)
        mean_curve = self.availability.mean(axis=0)
        horizon_mean = self.availability.mean(axis=1)
        lost_total = self.lost.sum(axis=1)
        return {
            "curve": {
                "p10": p10.round(4).tolist(),
                "p50": p50.round(4).tolist(),
                "p90": p90.round(4).tolist(),
                "mean": mean_curve.round(4).tolist(),
            },
            "availability_mean": float(horizon_mean.mean()),
            "availability_p10": float(np.percentile(horizon_mean, 10)),
            "availability_p50": float(np.percentile(horizon_mean, 50)),
            "availability_p90": float(np.percentile(horizon_mean, 90)),
            "aircraft_days_lost": float(lost_total.mean()),
            "aircraft_days_lost_p10": float(np.percentile(lost_total, 10)),
            "aircraft_days_lost_p90": float(np.percentile(lost_total, 90)),
            "by_cause": {
                cause: float(self.lost[:, index].mean()) for index, cause in enumerate(CAUSES)
            },
            "expected_failures": float(self.failures.mean()),
            "stockout_probability": self.stockouts.mean(axis=0).round(4).tolist(),
            "aircraft_days_lost_by_aircraft": self.by_aircraft_lost.mean(axis=0).round(3).tolist(),
        }


@dataclass
class _Order:
    aircraft: int
    slot: int | None
    part: int | None
    agency: int
    repair: int
    cause: str  # scheduled | unscheduled
    start: int
    allocated: bool = False
    in_bay: bool = False
    waited_spare: bool = False


@dataclass
class _RandomStream:
    failure_u: np.ndarray  # (runs, slots)
    background_u: np.ndarray  # (runs, slots)
    repair_noise: np.ndarray  # (runs, slots, 3) lognormal multipliers for successive repairs
    replacement_u: np.ndarray  # (runs, slots) failure draw for replaced parts
    lead_noise: np.ndarray  # (runs, parts, 4)


def _random_stream(snapshot: Snapshot, runs: int, seed: int) -> _RandomStream:
    rng = np.random.default_rng(seed)
    slots = snapshot.slot_part.size
    parts = snapshot.stock.size
    return _RandomStream(
        failure_u=rng.random((runs, slots)),
        background_u=rng.random((runs, slots)),
        repair_noise=rng.lognormal(0.0, 0.3, (runs, slots, 3)),
        replacement_u=rng.random((runs, slots)),
        lead_noise=rng.uniform(0.8, 1.4, (runs, parts, 4)),
    )


def _sample_failure_day(rul: np.ndarray, u: float, background_u: float, hazard: float,
                        risk30: float) -> float:
    p10, p50, p90 = (float(value) for value in rul)
    if p50 < 50.0:
        low = max(0.0, p10 - (p50 - p10))
        high = p90 + (p90 - p50) if p90 < 60.0 else math.inf
        knots = np.array([0.0, 0.1, 0.5, 0.9, 1.0])
        values = np.array([low, p10, p50, p90, high if math.isfinite(high) else 1e6])
        return float(np.interp(u, knots, values))
    rate = max(hazard, -math.log(max(1e-9, 1.0 - min(risk30, 0.999))) / 30.0)
    return -math.log(max(background_u, 1e-12)) / rate


def simulate_fleet(snapshot: Snapshot, horizon: int, runs: int, seed: int,
                   interventions: tuple[Intervention, ...] = ()) -> RunSummary:  # noqa: C901
    if not 7 <= horizon <= 60:
        raise ValueError("Horizon must be between 7 and 60 days")
    if not 20 <= runs <= 1000:
        raise ValueError("Runs must be between 20 and 1000")
    stream = _random_stream(snapshot, runs, seed)
    aircraft = len(snapshot.aircraft_ids)
    slots = snapshot.slot_part.size
    parts = snapshot.stock.size
    availability = np.zeros((runs, horizon))
    lost = np.zeros((runs, len(CAUSES)))
    stockouts = np.zeros((runs, parts), dtype=bool)
    failures = np.zeros(runs)
    by_aircraft = np.zeros((runs, aircraft))

    bays = snapshot.bays.copy()
    lead_time = snapshot.lead_time.astype(float).copy()
    blocked_parts: set[int] = set()
    planned: dict[int, int] = {}
    early: set[int] = set()
    for intervention in interventions:
        if intervention.kind == "extra_capacity" and intervention.agency is not None:
            bays[intervention.agency] += intervention.extra_bays
        elif intervention.kind == "spare_unavailable" and intervention.part is not None:
            blocked_parts.add(intervention.part)
            if intervention.lead_time_days is not None:
                lead_time[intervention.part] = intervention.lead_time_days
        elif intervention.kind == "replace":
            for slot in intervention.slots:
                planned[slot] = intervention.day
        elif intervention.kind == "early_replacement":
            early.update(intervention.slots)
    if snapshot.printable is not None:
        # Project Forge bypasses the supplier: a printable part arrives after the print time,
        # even when a scenario makes the supplier unavailable.
        lead_time = np.where(snapshot.printable, float(PRINT_DAYS), lead_time)
    # Supplier lead times vary; a print job does not.
    forge = snapshot.printable if snapshot.printable is not None else np.zeros(parts, dtype=bool)

    for run in range(runs):
        stock = snapshot.stock.copy()
        receipts = [list(r) for r in snapshot.receipts]
        for part in blocked_parts:
            stock[part] = 0
            receipts = [r for r in receipts if r[0] != part]
        failure_day = np.array([
            _sample_failure_day(snapshot.rul[s], stream.failure_u[run, s],
                                stream.background_u[run, s], snapshot.background_hazard[s],
                                float(snapshot.risk30[s]))
            for s in range(slots)
        ])
        repairs_done = np.zeros(slots, dtype=int)
        orders: list[_Order] = []
        down_until = np.zeros(aircraft, dtype=int)  # existing work: aircraft down until day
        down_cause = ["" for _ in range(aircraft)]
        for work in snapshot.open_work:
            if work.remaining_days > down_until[work.aircraft]:
                down_until[work.aircraft] = work.remaining_days
                down_cause[work.aircraft] = work.cause
        inspection_due = snapshot.inspection_due_day.copy()
        busy = np.zeros(bays.size, dtype=int)
        for work in snapshot.open_work:
            if work.in_bay:
                busy[work.agency] += 1

        def place(aircraft_index: int, slot: int | None, cause: str, day: int,
                  planned_work: bool = False, run: int = run,
                  repairs_done: np.ndarray = repairs_done,
                  orders: list[_Order] = orders) -> None:
            if slot is None:
                repair = snapshot.inspection_days
                part = None
                agency = snapshot.inspection_agency
            else:
                noise = stream.repair_noise[run, slot, min(repairs_done[slot], 2)]
                factor = 0.7 if planned_work else 1.0
                repair = max(1, math.ceil(float(snapshot.repair_days[slot]) * factor * noise))
                part = int(snapshot.slot_part[slot])
                agency = int(snapshot.slot_agency[slot])
                repairs_done[slot] += 1
            orders.append(_Order(aircraft_index, slot, part, agency, repair, cause, day))

        for slot in early:
            # Early replacement: planned at the first day a spare is on hand (bounded by horizon).
            planned.setdefault(slot, 1)

        for day in range(horizon):
            # Existing work releases its bay when it finishes.
            for work in snapshot.open_work:
                if work.in_bay and work.remaining_days == day:
                    busy[work.agency] -= 1
            # Receipts.
            for receipt in [r for r in receipts if r[2] == day]:
                stock[receipt[0]] += receipt[1]
                receipts.remove(receipt)
            # Planned replacements and inspections start.
            for slot, start in planned.items():
                if start == day and math.isfinite(failure_day[slot]):
                    place(int(snapshot.slot_aircraft[slot]), slot, "scheduled", day, True)
                    failure_day[slot] = math.inf  # replaced before failing
            for index in np.flatnonzero(inspection_due == day).tolist():
                place(int(index), None, "scheduled", day, True)
            # Failures while the aircraft is flying.
            active_aircraft = {order.aircraft for order in orders}
            for slot in np.flatnonzero(failure_day <= day).tolist():
                owner = int(snapshot.slot_aircraft[slot])
                if owner in active_aircraft or down_until[owner] > day:
                    failure_day[slot] = day + 1.0  # cannot fail while grounded; resume later
                    continue
                failures[run] += 1
                place(owner, int(slot), "unscheduled", day)
                failure_day[slot] = math.inf
            # Advance work orders: spares, bays, repair.
            day_cause = ["" for _ in range(aircraft)]
            for order in list(orders):
                if order.start > day:
                    continue
                if order.part is not None and not order.allocated:
                    if stock[order.part] > 0:
                        stock[order.part] -= 1
                        order.allocated = True
                    else:
                        stockouts[run, order.part] = True
                        if not any(r[0] == order.part for r in receipts):
                            delay = lead_time[order.part] * (
                                1.0 if forge[order.part] else stream.lead_noise[run, order.part, 0])
                            receipts.append([order.part, 1, day + max(1, round(delay))])
                        day_cause[order.aircraft] = "awaiting_spares"
                        continue
                if not order.in_bay:
                    if busy[order.agency] < bays[order.agency]:
                        busy[order.agency] += 1
                        order.in_bay = True
                    else:
                        if day_cause[order.aircraft] != "awaiting_spares":
                            day_cause[order.aircraft] = "awaiting_agency"
                        continue
                order.repair -= 1
                if day_cause[order.aircraft] == "":
                    day_cause[order.aircraft] = order.cause
                if order.repair <= 0:
                    busy[order.agency] -= 1
                    orders.remove(order)
                    if order.slot is not None:
                        # Replacement part: sample a fresh background failure time.
                        rate = max(float(snapshot.background_hazard[order.slot]), 1e-6)
                        u = max(float(stream.replacement_u[run, order.slot]), 1e-12)
                        failure_day[order.slot] = day + 1 - math.log(u) / rate
            # Reorder.
            for part in range(parts):
                position = stock[part] + sum(r[1] for r in receipts if r[0] == part)
                if position < snapshot.reorder_level[part] and part not in blocked_parts:
                    delay = lead_time[part] * (
                        1.0 if forge[part] else stream.lead_noise[run, part, 1])
                    receipts.append([part, 1, day + max(1, round(delay))])
            # Record the aircraft-day states.
            for index in range(aircraft):
                cause = day_cause[index]
                if not cause and down_until[index] > day:
                    cause = down_cause[index]
                if cause:
                    lost[run, CAUSES.index(cause)] += 1
                    by_aircraft[run, index] += 1
            availability[run, day] = 1.0 - sum(
                1 for index in range(aircraft)
                if day_cause[index] or down_until[index] > day
            ) / aircraft
    return RunSummary(availability, lost, stockouts, failures, by_aircraft)


def compare(snapshot: Snapshot, horizon: int, runs: int, seed: int,
            interventions: tuple[Intervention, ...]) -> dict[str, object]:
    baseline = simulate_fleet(snapshot, horizon, runs, seed).describe()
    scenario = simulate_fleet(snapshot, horizon, runs, seed, interventions).describe()
    return {
        "baseline": baseline,
        "scenario": scenario,
        "delta": {
            "availability_pct_points": round(
                100 * (float(scenario["availability_mean"])  # type: ignore[arg-type]
                       - float(baseline["availability_mean"])), 2  # type: ignore[arg-type]
            ),
            "aircraft_days_lost": round(
                float(scenario["aircraft_days_lost"])  # type: ignore[arg-type]
                - float(baseline["aircraft_days_lost"]), 2  # type: ignore[arg-type]
            ),
        },
    }

