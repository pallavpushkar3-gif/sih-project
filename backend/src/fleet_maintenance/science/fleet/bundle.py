"""Read-only access to a verified fleet engine bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np

from fleet_maintenance.artifacts.storage import verify_hashes
from fleet_maintenance.science.fleet.availability import OpenWork, Snapshot
from fleet_maintenance.science.fleet.catalog import ADDITIVE_PRINTABLE, PRINT_DAYS
from fleet_maintenance.science.fleet.engine import BACKGROUND_SHARE, BUNDLE_FILES


@dataclass
class FleetBundle:
    directory: Path
    manifest: dict[str, Any]
    records: dict[str, Any]
    arrays: dict[str, np.ndarray]
    attributions: dict[str, list[dict[str, Any]]]
    evaluation: dict[str, Any]
    forecast: dict[str, Any]
    integration: dict[str, Any]
    truth: dict[str, Any]

    @classmethod
    def load(cls, directory: Path) -> FleetBundle:
        manifest = json.loads((directory / "manifest.json").read_text())
        verify_hashes(directory, {name: manifest["hashes"][name] for name in BUNDLE_FILES
                                  if name != "models.joblib"})
        with np.load(directory / "arrays.npz") as data:
            arrays = {key: data[key] for key in data.files}

        def read(name: str) -> Any:
            return json.loads((directory / name).read_text())

        return cls(
            directory=directory,
            manifest=manifest,
            records=read("records.json"),
            arrays=arrays,
            attributions=read("attributions.json"),
            evaluation=read("evaluation.json"),
            forecast=read("forecast.json"),
            integration=read("integration.json"),
            truth=read("truth.json"),
        )

    # Calendar helpers -------------------------------------------------------------------------
    @cached_property
    def start(self) -> date:
        return date.fromisoformat(self.records["meta"]["start"])

    @cached_property
    def as_of(self) -> date:
        return date.fromisoformat(self.records["meta"]["as_of"])

    @property
    def days(self) -> int:
        return int(self.records["meta"]["days"])

    @property
    def replay_start_day(self) -> int:
        return int(self.records["meta"]["replay_start_day"])

    @property
    def recent_start_day(self) -> int:
        return int(self.records["meta"]["recent_start_day"])

    def day_of(self, value: date) -> int:
        return (value - self.start).days

    def date_of(self, day: int) -> date:
        return self.start + timedelta(days=int(day))

    def replay_offset(self, as_of: date | None) -> int:
        """Offset into the replay window; raises ValueError outside it."""
        if as_of is None:
            return int(self.records["meta"]["replay_days"]) - 1
        offset = self.day_of(as_of) - self.replay_start_day
        if not 0 <= offset < int(self.records["meta"]["replay_days"]):
            first = self.date_of(self.replay_start_day)
            raise ValueError(f"as_of must be between {first} and {self.as_of}")
        return offset

    # Catalogue --------------------------------------------------------------------------------
    @cached_property
    def types(self) -> list[dict[str, Any]]:
        return list(self.records["catalog"]["component_types"])

    @cached_property
    def type_by_code(self) -> dict[str, dict[str, Any]]:
        return {t["code"]: t for t in self.types}

    @cached_property
    def systems(self) -> dict[str, str]:
        return {s["code"]: s["name"] for s in self.records["catalog"]["systems"]}

    @cached_property
    def agencies(self) -> dict[str, dict[str, Any]]:
        return {a["id"]: a for a in self.records["catalog"]["agencies"]}

    @cached_property
    def printable(self) -> np.ndarray:
        """Project Forge flag per part (bundles made before the flag fall back to the catalog)."""
        return np.array([bool(t.get("additive_printable", t["code"] in ADDITIVE_PRINTABLE))
                         for t in self.types])

    def lead_time(self, part_index: int) -> int:
        """Days to obtain one more unit: print time for printable parts, else the order lead."""
        return PRINT_DAYS if self.printable[part_index] else int(
            self.types[part_index]["lead_time_days"])

    @cached_property
    def part_index(self) -> dict[str, int]:
        return {t["part_number"]: index for index, t in enumerate(self.types)}

    @cached_property
    def slots(self) -> list[dict[str, Any]]:
        return list(self.records["slots"])

    @cached_property
    def slot_index(self) -> dict[str, int]:
        return {slot["id"]: index for index, slot in enumerate(self.slots)}

    @cached_property
    def aircraft(self) -> list[dict[str, Any]]:
        return list(self.records["aircraft"])

    @cached_property
    def aircraft_index(self) -> dict[str, int]:
        return {a["id"]: index for index, a in enumerate(self.aircraft)}

    @cached_property
    def slot_type_index(self) -> np.ndarray:
        codes = {t["code"]: i for i, t in enumerate(self.types)}
        return np.array([codes[slot["type"]] for slot in self.slots])

    @cached_property
    def slot_aircraft_index(self) -> np.ndarray:
        return np.array([self.aircraft_index[slot["aircraft"]] for slot in self.slots])

    # Work orders ------------------------------------------------------------------------------
    def open_work_orders(self, day: int) -> list[dict[str, Any]]:
        return [
            wo for wo in self.records["work_orders"]
            if wo["opened_day"] < day and (wo["done_day"] is None or wo["done_day"] >= day)
        ]

    def work_order_phase(self, wo: dict[str, Any], day: int) -> str:
        if wo["part"] is not None and (wo["allocated_day"] is None or wo["allocated_day"] > day):
            return "awaiting_spares"
        if wo["bay_start_day"] is None or wo["bay_start_day"] > day:
            return "awaiting_agency"
        return "in_work"

    def agency_load(self, day: int) -> dict[str, int]:
        load = {agency: 0 for agency in self.agencies}
        for wo in self.open_work_orders(day):
            load[wo["agency"]] += 1
        return load

    # Inventory --------------------------------------------------------------------------------
    def stock_on(self, day: int) -> np.ndarray:
        return self.arrays["stock"][:, min(day, self.days - 1)].astype(int)

    def receipts_after(self, day: int) -> list[dict[str, Any]]:
        """Receipts expected after ``day``: pending ones at as-of, or recorded future ones."""
        if day >= self.days - 1:
            return list(self.records["pending_receipts"])
        recorded = [
            {"part": t["part"], "quantity": t["quantity"], "arrival_day": t["day"],
             "kind": t["kind"]}
            for t in self.records["transactions"]
            if t["kind"] != "issue" and t["day"] > day
        ]
        return recorded + list(self.records["pending_receipts"])

    @cached_property
    def background_hazard(self) -> np.ndarray:
        """Per-slot daily failure hazard for components without a degradation signal."""
        fh_per_day = max(float(self.arrays["flight_hours"][:, -30:].mean()), 0.5)
        life_days = np.array([t["mean_life_fh"] for t in self.types])[self.slot_type_index] / (
            fh_per_day
        )
        hazard: np.ndarray = BACKGROUND_SHARE / np.maximum(life_days, 1.0)
        return hazard

    # Simulation snapshot ----------------------------------------------------------------------
    def snapshot(self, offset: int | None = None,
                 closed: frozenset[str] = frozenset()) -> Snapshot:
        offset = self.replay_offset(None) if offset is None else offset
        day = self.replay_start_day + offset
        repair_days = np.array([t["repair_days"] for t in self.types])[self.slot_type_index]
        fh = self.arrays["flight_hours"]
        fh_per_day = max(float(fh[:, max(0, day - 29): day + 1].mean()), 0.5)
        life_days = np.array([t["mean_life_fh"] for t in self.types])[self.slot_type_index] / (
            fh_per_day
        )
        agency_ids = list(self.agencies)
        open_work = []
        for wo in self.open_work_orders(day + 1):
            if wo["id"] in closed:
                continue
            phase = self.work_order_phase(wo, day)
            if phase == "awaiting_spares":
                part = self.part_index[wo["part"]]
                arrivals = [r["arrival_day"] for r in self.receipts_after(day)
                            if r["part"] == wo["part"] and r["arrival_day"] > day]
                wait = min([a - day for a in arrivals] + [self.lead_time(part)])
                remaining, cause = wait + wo["repair_days"], "awaiting_spares"
            elif phase == "awaiting_agency":
                remaining, cause = wo["repair_days"] + 2, "awaiting_agency"
            else:
                done = wo["done_day"] if wo["done_day"] is not None else (
                    wo["bay_start_day"] + wo["repair_days"]
                )
                remaining = done - day
                cause = "unscheduled" if wo["kind"] == "unscheduled" else "scheduled"
            open_work.append(OpenWork(self.aircraft_index[wo["aircraft"]], max(1, int(remaining)),
                                      cause, agency_ids.index(wo["agency"]), phase == "in_work"))
        receipts = tuple(
            (self.part_index[r["part"]], int(r["quantity"]), int(r["arrival_day"]) - day)
            for r in self.receipts_after(day) if r["arrival_day"] > day
        )
        interval = float(self.records["meta"]["config"]["inspection_interval_fh"])
        since = np.array([a["inspection_hours_since"] for a in self.aircraft])
        utilisation = np.maximum(fh[:, -30:].mean(axis=1), 0.3)
        inspection_due = np.maximum(np.ceil((interval - since) / utilisation), 0).astype(int)
        return Snapshot(
            aircraft_ids=tuple(a["id"] for a in self.aircraft),
            slot_aircraft=self.slot_aircraft_index,
            slot_part=self.slot_type_index,
            slot_agency=np.array([agency_ids.index(t["agency"]) for t in self.types])[
                self.slot_type_index
            ],
            repair_days=repair_days,
            rul=self.arrays["rul"][:, offset, :].astype(np.float64),
            risk30=self.arrays["risk30"][:, offset].astype(np.float64),
            background_hazard=BACKGROUND_SHARE / np.maximum(life_days, 1.0),
            stock=self.stock_on(day),
            reorder_level=np.array([t["reorder_level"] for t in self.types]),
            lead_time=np.array([t["lead_time_days"] for t in self.types]),
            printable=self.printable,
            receipts=receipts,
            bays=np.array([self.agencies[a]["bays"] for a in agency_ids]),
            open_work=tuple(open_work),
            inspection_due_day=inspection_due,
            inspection_days=int(self.records["meta"]["config"]["inspection_days"]),
            inspection_agency=agency_ids.index("AG-LINE"),
        )
