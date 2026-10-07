"""Latent-health fleet simulator (docs/plan.md section 3).

Each component slot holds a part instance that wears in two phases: an incubation phase with no
observable signature, then a degradation phase whose progress ``x`` drives the sensor signature
``x ** p``. Failure happens when ``x`` reaches one, or through a random shock that gives little
warning. Sensors are ``baseline(operating conditions) + signature(health) + noise``.

Work orders model spare waits, agency queues and repair time, so downtime has the causes that
section 1.1 of the plan describes. The hidden health and failure dates are returned separately
in ``SimulationTruth`` and must never be used as model features.

Hero aircraft follow scripted degradation in the final weeks so the demonstration has reliable
storylines. The script is disclosed in ``World.scripted``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np

from fleet_maintenance.science.fleet.catalog import (
    AGENCIES,
    AGENCY_INDEX,
    BASES,
    COMPONENT_TYPES,
    MAX_PARAMETERS,
    WorldConfig,
    tail_code,
)

STATE_AVAILABLE = 0
STATE_SCHEDULED = 1
STATE_UNSCHEDULED = 2
STATE_SPARES = 3
STATE_AGENCY = 4
STATE_NAMES = (
    "available",
    "scheduled_maintenance",
    "unscheduled_repair",
    "awaiting_spares",
    "awaiting_agency",
)
FLAG_OK = 0
FLAG_MISSING = 1
FLAG_NO_FLIGHT = 9


@dataclass
class WorkOrder:
    id: str
    aircraft: int
    slot: int | None
    kind: str  # unscheduled | scheduled | inspection
    agency: int
    opened: int
    repair_days: int
    part: int | None
    priority: str
    finding: str
    allocated_day: int | None = None
    bay_start: int | None = None
    done: int | None = None
    remaining: int = 0
    spare_wait_days: int = 0
    queue_wait_days: int = 0
    serial_out: str | None = None
    serial_in: str | None = None

    @property
    def is_open(self) -> bool:
        return self.done is None

    def delay_reason(self) -> str | None:
        if self.spare_wait_days >= max(1, self.queue_wait_days):
            return "awaiting_spares" if self.spare_wait_days else None
        return "agency_queue" if self.queue_wait_days else None


@dataclass
class FaultEvent:
    day: int
    aircraft: int
    slot: int
    code: str
    severity: int  # 1 advisory BIT message .. 4 functional failure
    description: str
    sudden: bool = False


@dataclass
class Transaction:
    day: int
    part: int
    quantity: int
    kind: str  # issue | receipt | repair-return
    work_order: str | None = None


@dataclass
class PendingReceipt:
    part: int
    quantity: int
    arrival: int
    kind: str


@dataclass
class Instance:
    slot: int
    serial: str
    installed: int
    removed: int | None = None
    removal_reason: str | None = None


@dataclass
class SimulationTruth:
    """Hidden ground truth. Evaluation and storytelling only, never a model feature."""

    health: np.ndarray  # (slots, days) float32, 1 = new, 0 = failed
    failure_days: list[tuple[int, int, bool]]  # (slot, day, sudden)
    future_failures: dict[int, int]  # scripted slots: slot -> failure day beyond as-of


@dataclass
class World:
    config: WorldConfig
    start: date
    days: int
    aircraft_ids: list[str]
    aircraft_base: np.ndarray
    aircraft_commissioned: list[date]
    utilisation: np.ndarray
    slot_aircraft: np.ndarray
    slot_type: np.ndarray
    readings: np.ndarray  # (slots, days, MAX_PARAMETERS) float32
    flags: np.ndarray  # (slots, days, MAX_PARAMETERS) uint8
    instance_index: np.ndarray  # (slots, days) int16 local instance counter
    hours_since_install: np.ndarray  # (slots, days) float32 at end of day
    flight_hours: np.ndarray  # (aircraft, days) float32
    cycles: np.ndarray  # (aircraft, days) int16
    ambient: np.ndarray  # (aircraft, days) float32
    load_factor: np.ndarray  # (aircraft, days) float32
    aircraft_state: np.ndarray  # (aircraft, days) int8
    stock: np.ndarray  # (parts, days) int16 on hand at end of day
    instances: list[Instance]
    work_orders: list[WorkOrder]
    faults: list[FaultEvent]
    transactions: list[Transaction]
    pending_receipts: list[PendingReceipt]
    inspection_hours_since: np.ndarray  # (aircraft,) flight hours since the last inspection
    truth: SimulationTruth
    scripted: list[dict[str, object]] = field(default_factory=list)

    def day_date(self, day: int) -> date:
        return self.start + timedelta(days=int(day))

    @property
    def as_of_day(self) -> int:
        return self.days - 1

    @property
    def slots(self) -> int:
        return int(self.slot_aircraft.shape[0])


@dataclass(frozen=True)
class HeroScript:
    tail: str
    component: str
    fail_offset_days: int  # failure day relative to as-of (positive means after as-of)
    window_days: int  # onset-to-failure window
    power: float = 1.7


HERO_SCRIPTS: tuple[HeroScript, ...] = (
    HeroScript("AC-017", "HYD-PMP", 15, 50),
    HeroScript("AC-023", "HYD-PMP", 34, 60),
    HeroScript("AC-008", "ELE-GEN", 5, 30),
    HeroScript("AC-031", "ENG-OIL", 40, 70),
)
QUIET_DAYS = 45  # hero aircraft have no random events in the final weeks (disclosed)


def _parameter_table() -> dict[str, np.ndarray]:
    types = len(COMPONENT_TYPES)
    table = {
        key: np.full((types, MAX_PARAMETERS), np.nan, dtype=np.float64)
        for key in ("baseline", "ambient", "load", "signature", "noise", "minimum")
    }
    for index, component_type in enumerate(COMPONENT_TYPES):
        for k, parameter in enumerate(component_type.parameters):
            table["baseline"][index, k] = parameter.baseline
            table["ambient"][index, k] = parameter.ambient_coeff
            table["load"][index, k] = parameter.load_coeff
            table["signature"][index, k] = parameter.signature
            table["noise"][index, k] = parameter.noise
            table["minimum"][index, k] = (
                parameter.minimum if parameter.minimum is not None else -np.inf
            )
    return table


def part_numbers() -> list[str]:
    return [component_type.part_number for component_type in COMPONENT_TYPES]


def simulate(config: WorldConfig | None = None) -> World:  # noqa: C901 - one explicit day loop
    config = config or WorldConfig()
    rng = np.random.default_rng(config.seed)
    days = config.history_days
    start = config.as_of - timedelta(days=days - 1)
    aircraft_count = config.aircraft
    type_count = len(COMPONENT_TYPES)
    slots = aircraft_count * type_count
    slot_aircraft = np.repeat(np.arange(aircraft_count), type_count)
    slot_type = np.tile(np.arange(type_count), aircraft_count)
    aircraft_ids = [tail_code(index) for index in range(aircraft_count)]
    tail_index = {tail: index for index, tail in enumerate(aircraft_ids)}

    aircraft_base = rng.integers(0, len(BASES), aircraft_count)
    utilisation = rng.uniform(0.8, 1.5, aircraft_count)
    aircraft_commissioned = [
        date(int(year), int(month), 1)
        for year, month in zip(
            rng.integers(2008, 2020, aircraft_count), rng.integers(1, 13, aircraft_count),
            strict=True,
        )
    ]
    mean_life = np.array([t.mean_life_fh for t in COMPONENT_TYPES])[slot_type] * config.life_scale
    hard_time = np.array(
        [t.hard_time_fh if t.hard_time_fh else np.inf for t in COMPONENT_TYPES]
    )[slot_type]
    sudden_share = np.array([t.sudden_share for t in COMPONENT_TYPES])[slot_type]
    table = _parameter_table()
    parameter_count = np.array([len(t.parameters) for t in COMPONENT_TYPES])[slot_type]

    # Per-instance "personality": onset life, degradation window and signature curvature.
    def draw_personality(count: int, types: np.ndarray) -> tuple[np.ndarray, ...]:
        onset = mean_life_by_type[types] * rng.lognormal(0.0, 0.35, count)
        window = 110.0 * rng.lognormal(0.0, 0.45, count)
        power = rng.uniform(1.4, 2.2, count)
        return onset, window, power

    mean_life_by_type = np.array([t.mean_life_fh for t in COMPONENT_TYPES]) * config.life_scale
    onset, window, power = draw_personality(slots, slot_type)
    # Start mid-life: some slots are already in degradation, which seeds early failures.
    effective = onset * rng.uniform(0.0, 0.97, slots)
    hours = effective.copy()
    progress = np.zeros(slots)

    serial_counter = [0] * type_count

    def new_serial(type_index: int) -> str:
        serial_counter[type_index] += 1
        return f"{COMPONENT_TYPES[type_index].part_number}-{serial_counter[type_index]:05d}"

    instances: list[Instance] = []
    current_instance: list[int] = []
    for slot in range(slots):
        instances.append(Instance(slot, new_serial(int(slot_type[slot])), 0))
        current_instance.append(len(instances) - 1)
    local_counter = np.zeros(slots, dtype=np.int16)

    # Sensor fault injection plans (stuck-at windows and slow drift on non-failing sensors).
    stuck_start = np.full((slots, MAX_PARAMETERS), -1)
    stuck_length = np.zeros((slots, MAX_PARAMETERS), dtype=int)
    drift_start = np.full((slots, MAX_PARAMETERS), -1)
    drift_length = np.ones((slots, MAX_PARAMETERS), dtype=int)
    drift_magnitude = np.zeros((slots, MAX_PARAMETERS))
    valid_parameter = np.arange(MAX_PARAMETERS)[None, :] < parameter_count[:, None]
    stuck_mask = valid_parameter & (rng.random((slots, MAX_PARAMETERS)) < config.stuck_sensor_share)
    stuck_start[stuck_mask] = rng.integers(30, days - 30, int(stuck_mask.sum()))
    stuck_length[stuck_mask] = rng.integers(5, 16, int(stuck_mask.sum()))
    drift_mask = valid_parameter & (rng.random((slots, MAX_PARAMETERS)) < config.drift_sensor_share)
    drift_start[drift_mask] = rng.integers(30, days - 90, int(drift_mask.sum()))
    drift_length[drift_mask] = rng.integers(30, 90, int(drift_mask.sum()))
    noise_by_slot = table["noise"][slot_type]
    signature_by_slot = table["signature"][slot_type]
    drift_magnitude[drift_mask] = (
        rng.uniform(2.0, 4.0, int(drift_mask.sum()))
        * noise_by_slot[drift_mask]
        * np.sign(signature_by_slot[drift_mask])
    )
    stuck_value = np.full((slots, MAX_PARAMETERS), np.nan)
    last_value = np.full((slots, MAX_PARAMETERS), np.nan)

    # Hero scripts: deterministic degradation ending at a known failure day after as-of.
    scripted: list[dict[str, object]] = []
    hero_slot: dict[int, tuple[int, float, float]] = {}  # slot -> (onset day, window, power)
    future_failures: dict[int, int] = {}
    hero_aircraft: set[int] = set()
    for script in HERO_SCRIPTS:
        if script.tail not in tail_index:
            continue
        aircraft = tail_index[script.tail]
        type_index = next(
            i for i, component_type in enumerate(COMPONENT_TYPES)
            if component_type.code == script.component
        )
        slot = aircraft * type_count + type_index
        failure_day = days - 1 + script.fail_offset_days
        onset_day = failure_day - script.window_days
        hero_slot[slot] = (onset_day, float(script.window_days), script.power)
        future_failures[slot] = failure_day
        hero_aircraft.add(aircraft)
        scripted.append(
            {
                "aircraft": script.tail,
                "component": script.component,
                "script": "deterministic degradation; random events suppressed on this "
                f"aircraft for the final {QUIET_DAYS} days",
                "hidden_failure_offset_days": script.fail_offset_days,
            }
        )
    for slot, (onset_day, _, _) in hero_slot.items():
        # The scripted instance is installed well before its onset and never reaches onset early.
        onset[slot] = 1e9
        effective[slot] = 0.0
        hours[slot] = max(0.0, (onset_day - (days - 200)) * 2.0)

    parts = part_numbers()
    on_hand = np.array([t.reorder_level for t in COMPONENT_TYPES], dtype=int)
    pending: list[PendingReceipt] = []
    transactions: list[Transaction] = []
    work_orders: list[WorkOrder] = []
    open_orders: list[WorkOrder] = []
    faults: list[FaultEvent] = []
    failure_days: list[tuple[int, int, bool]] = []

    readings = np.full((slots, days, MAX_PARAMETERS), np.nan, dtype=np.float32)
    flags = np.full((slots, days, MAX_PARAMETERS), FLAG_NO_FLIGHT, dtype=np.uint8)
    instance_index = np.zeros((slots, days), dtype=np.int16)
    hours_record = np.zeros((slots, days), dtype=np.float32)
    flight_hours = np.zeros((aircraft_count, days), dtype=np.float32)
    cycles = np.zeros((aircraft_count, days), dtype=np.int16)
    ambient_record = np.zeros((aircraft_count, days), dtype=np.float32)
    load_record = np.zeros((aircraft_count, days), dtype=np.float32)
    aircraft_state = np.zeros((aircraft_count, days), dtype=np.int8)
    stock = np.zeros((len(parts), days), dtype=np.int16)
    health = np.zeros((slots, days), dtype=np.float32)
    slot_busy = np.zeros(slots, dtype=bool)  # a work order already covers this slot
    inspection_since = rng.uniform(0, config.inspection_interval_fh, aircraft_count)
    base_mean = np.array([base.mean_temp_c for base in BASES])[aircraft_base]
    base_amplitude = np.array([base.seasonal_amplitude_c for base in BASES])[aircraft_base]
    agency_busy = np.zeros(len(AGENCIES), dtype=int)

    def reorder(day: int) -> None:
        for part_index, component_type in enumerate(COMPONENT_TYPES):
            on_order = sum(r.quantity for r in pending if r.part == part_index)
            waiting = sum(
                1 for wo in open_orders
                if wo.part == part_index and wo.allocated_day is None
            )
            position = on_hand[part_index] + on_order - waiting
            if position <= component_type.reorder_level:
                quantity = component_type.reorder_level + 1 - position
                lead = max(1, round(component_type.lead_time_days * rng.uniform(0.8, 1.4)))
                pending.append(PendingReceipt(part_index, int(quantity), day + lead, "receipt"))

    def open_work_order(
        day: int, aircraft: int, slot: int | None, kind: str, finding: str, priority: str
    ) -> None:
        if slot is not None:
            component_type = COMPONENT_TYPES[int(slot_type[slot])]
            agency = AGENCY_INDEX[component_type.agency]
            base_days = component_type.repair_days * config.repair_scale * (
                0.7 if kind == "scheduled" else 1.0
            )
            if kind == "inspection":
                base_days += config.inspection_days
                agency = AGENCY_INDEX["AG-LINE"]
            repair_days = max(1, math.ceil(base_days * rng.lognormal(0.0, 0.3)))
            part: int | None = int(slot_type[slot])
            slot_busy[slot] = True
        else:
            agency = AGENCY_INDEX["AG-LINE"]
            repair_days = config.inspection_days
            part = None
        order = (
            WorkOrder(
                id=f"WO-{len(work_orders) + 1:05d}",
                aircraft=aircraft,
                slot=slot,
                kind=kind,
                agency=agency,
                opened=day,
                repair_days=repair_days,
                remaining=repair_days,
                part=part,
                priority=priority,
                finding=finding,
                serial_out=instances[current_instance[slot]].serial if slot is not None else None,
            )
        )
        work_orders.append(order)
        open_orders.append(order)

    def replace_instance(day: int, slot: int, reason: str) -> str:
        instance = instances[current_instance[slot]]
        instance.removed = day
        instance.removal_reason = reason
        type_index = int(slot_type[slot])
        serial = new_serial(type_index)
        instances.append(Instance(slot, serial, day + 1))
        current_instance[slot] = len(instances) - 1
        local_counter[slot] += 1
        new_onset, new_window, new_power = draw_personality(1, np.array([type_index]))
        onset[slot], window[slot], power[slot] = new_onset[0], new_window[0], new_power[0]
        effective[slot] = 0.0
        hours[slot] = 0.0
        progress[slot] = 0.0
        slot_busy[slot] = False
        return serial

    for day in range(days):
        # 1. Receipts arriving today.
        for receipt in [r for r in pending if r.arrival == day]:
            on_hand[receipt.part] += receipt.quantity
            transactions.append(Transaction(day, receipt.part, receipt.quantity, receipt.kind))
            pending.remove(receipt)

        # 2. Advance open work orders: spare allocation, agency queue, repair.
        aircraft_phase = np.zeros(aircraft_count, dtype=np.int8)
        for wo in list(open_orders):
            if wo.opened >= day:
                continue
            if wo.part is not None and wo.allocated_day is None:
                if on_hand[wo.part] > 0:
                    on_hand[wo.part] -= 1
                    wo.allocated_day = day
                    transactions.append(Transaction(day, wo.part, -1, "issue", wo.id))
                else:
                    wo.spare_wait_days += 1
                    aircraft_phase[wo.aircraft] = max(aircraft_phase[wo.aircraft], STATE_SPARES)
                    continue
            if wo.bay_start is None:
                if agency_busy[wo.agency] < AGENCIES[wo.agency].bays:
                    agency_busy[wo.agency] += 1
                    wo.bay_start = day
                else:
                    wo.queue_wait_days += 1
                    aircraft_phase[wo.aircraft] = max(aircraft_phase[wo.aircraft], STATE_AGENCY)
                    continue
            wo.remaining -= 1
            in_repair = STATE_UNSCHEDULED if wo.kind == "unscheduled" else STATE_SCHEDULED
            if aircraft_phase[wo.aircraft] < STATE_SPARES:
                aircraft_phase[wo.aircraft] = max(aircraft_phase[wo.aircraft], in_repair)
            if wo.remaining <= 0:
                wo.done = day
                open_orders.remove(wo)
                agency_busy[wo.agency] -= 1
                if wo.slot is not None and wo.part is not None:
                    wo.serial_in = replace_instance(day, wo.slot, wo.kind)
                    if COMPONENT_TYPES[wo.part].repairable and rng.random() < 0.5:
                        pending.append(
                            PendingReceipt(wo.part, 1, day + int(rng.integers(20, 46)),
                                           "repair-return")
                        )
                if wo.kind == "inspection":
                    inspection_since[wo.aircraft] = 0.0
        aircraft_state[:, day] = aircraft_phase
        reorder(day)
        stock[:, day] = on_hand

        # 3. Flights for aircraft not held by a work order.
        down = aircraft_phase > 0
        day_of_year = (start + timedelta(days=day)).timetuple().tm_yday
        seasonal = np.sin(2 * np.pi * (day_of_year - 110) / 365)
        temperature = base_mean + base_amplitude * seasonal + rng.normal(0, 3.0, aircraft_count)
        load = rng.uniform(0.5, 0.95, aircraft_count)
        flights = np.minimum(rng.poisson(utilisation), 4) * (~down)
        hours_per_flight = rng.uniform(1.0, 2.5, (aircraft_count, 4))
        fh = (hours_per_flight * (np.arange(4)[None, :] < flights[:, None])).sum(axis=1)
        flight_hours[:, day] = fh
        cycles[:, day] = flights
        ambient_record[:, day] = temperature
        load_record[:, day] = load
        inspection_since += fh

        flying = flights[slot_aircraft] > 0
        slot_fh = fh[slot_aircraft]
        slot_temp = temperature[slot_aircraft]
        slot_load = load[slot_aircraft]
        stress = 1.0 + 0.015 * np.maximum(slot_temp - 15.0, 0.0) + 0.5 * (slot_load - 0.7)
        wear = slot_fh * stress
        hours += slot_fh
        effective += wear
        in_degradation = effective >= onset
        increments = np.where(
            in_degradation & flying,
            rng.gamma(4.0, np.maximum(wear / np.maximum(window, 1e-6), 1e-9) / 4.0),
            0.0,
        )
        progress = np.minimum(progress + increments, 1.0)
        for slot, (onset_day, script_window, script_power) in hero_slot.items():
            progress[slot] = min(max(0.0, (day - onset_day) / script_window), 0.999)
            power[slot] = script_power
        signature_level = np.where(progress > 0, progress ** power, 0.0)
        health[:, day] = np.where(
            progress > 0,
            0.7 * (1.0 - progress),
            1.0 - 0.3 * np.minimum(effective / np.maximum(onset, 1.0), 1.0),
        )

        # 4. Post-flight sensor summaries with injected data-quality problems.
        flight_count = np.maximum(flights[slot_aircraft], 1)[:, None]
        values = (
            table["baseline"][slot_type]
            + table["ambient"][slot_type] * (slot_temp - 15.0)[:, None]
            + table["load"][slot_type] * (slot_load - 0.7)[:, None]
            + signature_by_slot * signature_level[:, None]
            + noise_by_slot * rng.standard_normal((slots, MAX_PARAMETERS)) / np.sqrt(flight_count)
        )
        drift_progress = np.clip((day - drift_start) / drift_length, 0.0, 1.0)
        drift_active = (drift_start >= 0) & (day >= drift_start) & (
            day < drift_start + drift_length + 30
        )
        values = values + np.where(drift_active, drift_magnitude * drift_progress, 0.0)
        stuck_active = (stuck_start >= 0) & (day >= stuck_start) & (
            day < stuck_start + stuck_length
        )
        starting = stuck_active & np.isnan(stuck_value)
        stuck_value[starting] = last_value[starting]
        values = np.where(stuck_active & ~np.isnan(stuck_value), stuck_value, values)
        stuck_value[~stuck_active] = np.nan
        spikes = rng.random((slots, MAX_PARAMETERS)) < config.spike_rate
        values = values + spikes * 8.0 * noise_by_slot * rng.choice([-1.0, 1.0], (slots, 1))
        values = np.maximum(values, table["minimum"][slot_type])
        record = flying[:, None] & valid_parameter
        last_value = np.where(record, values, last_value)
        dropout = rng.random((slots, MAX_PARAMETERS)) < config.dropout_rate
        download_lost = rng.random(aircraft_count) < config.missing_download_rate
        missing_download = download_lost[slot_aircraft]
        missing = record & (dropout | missing_download[:, None])
        stored = record & ~missing
        readings[:, day, :] = np.where(stored, values, np.nan)
        flags[:, day, :] = np.where(
            missing, FLAG_MISSING, np.where(stored, FLAG_OK, FLAG_NO_FLIGHT)
        )
        instance_index[:, day] = local_counter
        hours_record[:, day] = hours

        # 5. Events: precursor messages, failures, hard-time replacements, inspections.
        quiet = np.zeros(slots, dtype=bool)
        if day >= days - QUIET_DAYS:
            quiet = np.isin(slot_aircraft, list(hero_aircraft))
        scripted_slot = np.zeros(slots, dtype=bool)
        scripted_slot[list(hero_slot)] = True
        candidates = flying & ~slot_busy & ~quiet
        precursor = candidates & (rng.random(slots) < 0.06 * signature_level)
        for slot in np.flatnonzero(precursor).tolist():
            faults.append(
                FaultEvent(day, int(slot_aircraft[slot]), int(slot), f"BIT-{slot_type[slot]:02d}1",
                           1, "Intermittent built-in-test advisory message")
            )
        hazard = (
            config.sudden_scale * sudden_share / (1.0 - sudden_share) * wear
            / np.maximum(mean_life, 1.0)
        )
        sudden = candidates & ~scripted_slot & (rng.random(slots) < hazard)
        worn = candidates & ~scripted_slot & (progress >= 1.0)
        for slot in np.flatnonzero(sudden | worn).tolist():
            aircraft = int(slot_aircraft[slot])
            is_sudden = bool(sudden[slot] and not worn[slot])
            failure_days.append((int(slot), day, is_sudden))
            faults.append(
                FaultEvent(day, aircraft, int(slot), f"FLT-{slot_type[slot]:02d}4", 4,
                           "Functional failure reported after flight", is_sudden)
            )
            open_work_order(day, aircraft, int(slot), "unscheduled",
                            "sudden failure" if is_sudden else "failure", "P1")
        hard = candidates & ~scripted_slot & (hours >= hard_time) & ~(sudden | worn)
        for slot in np.flatnonzero(hard).tolist():
            open_work_order(day, int(slot_aircraft[slot]), int(slot), "scheduled",
                            "hard-time replacement", "P3")
        due = (inspection_since >= config.inspection_interval_fh) & ~down
        for aircraft in np.flatnonzero(due).tolist():
            if day >= days - 60 and aircraft_ids[aircraft] == "AC-031":
                continue  # AC-031's inspection is scripted to be overdue at as-of.
            if any(wo.aircraft == aircraft and wo.kind == "inspection" for wo in open_orders):
                continue
            if quiet[aircraft * type_count]:
                continue
            open_work_order(day, int(aircraft), None, "inspection", "periodic inspection", "P3")
            on_aircraft = (slot_aircraft == aircraft) & ~slot_busy & ~scripted_slot
            found = on_aircraft & (progress > 0.3) & (rng.random(slots) < 0.6)
            for slot in np.flatnonzero(found).tolist():
                open_work_order(day, int(aircraft), int(slot), "scheduled",
                                "degradation found on inspection", "P2")

    # Scripted spare position for the demonstration storyline (disclosed in World.scripted).
    hydraulic_pump = next(i for i, t in enumerate(COMPONENT_TYPES) if t.code == "HYD-PMP")
    pending = [r for r in pending if r.part != hydraulic_pump]
    on_hand[hydraulic_pump] = 1
    stock[hydraulic_pump, days - 1] = 1
    scripted.append(
        {
            "part": "HYD-114",
            "script": "stock set to 1 on hand and 0 on order at as-of to create the "
            "fleet-level spares storyline",
        }
    )

    return World(
        config=config,
        start=start,
        days=days,
        aircraft_ids=aircraft_ids,
        aircraft_base=aircraft_base,
        aircraft_commissioned=aircraft_commissioned,
        utilisation=utilisation,
        slot_aircraft=slot_aircraft,
        slot_type=slot_type,
        readings=readings,
        flags=flags,
        instance_index=instance_index,
        hours_since_install=hours_record,
        flight_hours=flight_hours,
        cycles=cycles,
        ambient=ambient_record,
        load_factor=load_record,
        aircraft_state=aircraft_state,
        stock=stock,
        instances=instances,
        work_orders=work_orders,
        faults=faults,
        transactions=transactions,
        pending_receipts=pending,
        inspection_hours_since=inspection_since,
        truth=SimulationTruth(health, failure_days, future_failures),
        scripted=scripted,
    )
