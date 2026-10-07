"""Data integration layer (docs/plan.md module 1).

The simulator produces one consistent world. To exercise integration honestly, this module
derives four *source extracts* from it, each with the identifier conventions, timestamp formats,
duplicates and gaps of a separate system, then normalises them into the unified
aircraft -> system -> component -> part model and reports what it had to repair or reject.
The extract defects are injected deliberately and labelled as such.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import timedelta

import numpy as np

from fleet_maintenance.science.fleet.catalog import BASES, COMPONENT_TYPES, SYSTEMS
from fleet_maintenance.science.fleet.features import FLAG_SPIKE, FLAG_STUCK
from fleet_maintenance.science.fleet.simulator import FLAG_MISSING, FLAG_NO_FLIGHT, FLAG_OK, World

TAIL_PATTERN = re.compile(r"^\s*(?:SYN[\s-]*)?AC[\s_-]*0*(\d{1,3})\s*$", re.IGNORECASE)
PART_PATTERN = re.compile(r"^\s*([A-Z]{3})[\s-]?(\d{3})(?:[-/][A-Z0-9]+)?\s*$", re.IGNORECASE)
WINDOW_DAYS = 90


def normalise_tail(raw: str) -> str | None:
    match = TAIL_PATTERN.match(raw)
    return f"AC-{int(match.group(1)):03d}" if match else None


def normalise_part(raw: str) -> str | None:
    match = PART_PATTERN.match(raw)
    return f"{match.group(1).upper()}-{match.group(2)}" if match else None


def _tail_variant(rng: np.random.Generator, tail: str) -> str:
    number = int(tail[3:])
    choice = rng.random()
    if choice < 0.55:
        return tail
    if choice < 0.75:
        return f"AC{number:03d}"
    if choice < 0.9:
        return f"SYN AC {number}"
    if choice < 0.995:
        return f"ac_{number:02d}"
    return f"TAIL-{number}"  # unmappable legacy identifier


def _part_variant(rng: np.random.Generator, part: str) -> str:
    choice = rng.random()
    if choice < 0.7:
        return part
    if choice < 0.85:
        return part.replace("-", "") + "-A"
    if choice < 0.995:
        return part.lower()
    return f"NSN-{part}"  # unmappable stock number


def integrate(world: World, flags: np.ndarray) -> dict[str, object]:
    """Build the four source extracts, normalise them and return a data-quality report."""
    rng = np.random.default_rng(world.config.seed + 101)
    first_day = world.days - WINDOW_DAYS
    known_tails = set(world.aircraft_ids)
    known_parts = {t.part_number for t in COMPONENT_TYPES}
    sources = []

    # 1. Health monitoring downloads: one row per component, flight-day and parameter.
    window = flags[:, first_day:, :]
    flown = window != FLAG_NO_FLIGHT
    raw_rows = int(flown.sum())
    duplicates = int(rng.binomial(raw_rows, 0.004))
    variants = [_tail_variant(rng, tail) for tail in world.aircraft_ids]
    unmapped_tails = [v for v in variants if normalise_tail(v) is None]
    unmapped_rows = int(
        sum(flown[world.slot_aircraft == index].sum() for index, v in enumerate(variants)
            if normalise_tail(v) is None)
    )
    remapped_rows = int(
        sum(flown[world.slot_aircraft == index].sum() for index, v in enumerate(variants)
            if normalise_tail(v) not in (None, v))
    )
    missing = int((window == FLAG_MISSING).sum())
    stuck = int((window == FLAG_STUCK).sum())
    spikes = int((window == FLAG_SPIKE).sum())
    usable = int(
        sum((window[world.slot_aircraft == index] == FLAG_OK).sum()
            for index, v in enumerate(variants) if normalise_tail(v) is not None)
    )
    sources.append({
        "id": "health_monitoring",
        "name": "Aircraft health monitoring downloads",
        "owner": "Flight-data download station",
        "format": "post-flight parameter summaries (mean per flight-day)",
        "identifier_example": variants[16],
        "timestamp_format": "local base time, converted to UTC date",
        "raw_records": raw_rows + duplicates,
        "duplicates_removed": duplicates,
        "identifiers_remapped": remapped_rows,
        "rejected_unmappable": unmapped_rows,
        "missing_values": missing,
        "stuck_values_flagged": stuck,
        "spikes_clipped": spikes,
        "accepted_records": usable,
        "unmapped_identifiers": unmapped_tails,
    })

    # 2. Technical records: defect reports and maintenance actions from the logbook.
    faults = [event for event in world.faults if event.day >= first_day]
    orders = [wo for wo in world.work_orders if wo.opened >= first_day]
    logbook = [(world.aircraft_ids[e.aircraft], e.day) for e in faults] + [
        (world.aircraft_ids[wo.aircraft], wo.opened) for wo in orders
    ]
    duplicated = int(rng.binomial(len(logbook), 0.01))
    tails = [_tail_variant(rng, tail) for tail, _ in logbook]
    mapped = [normalise_tail(tail) for tail in tails]
    date_formats = Counter(rng.choice(["ISO 8601", "dd/mm/yyyy", "dd-MMM-yy"], len(logbook),
                                      p=[0.5, 0.35, 0.15]).tolist())
    sources.append({
        "id": "technical_records",
        "name": "Technical records and logbooks",
        "owner": "Maintenance control",
        "format": "defect reports, rectification actions, component changes",
        "identifier_example": tails[0] if tails else "",
        "timestamp_format": ", ".join(f"{k} ({v})" for k, v in date_formats.items()),
        "raw_records": len(logbook) + duplicated,
        "duplicates_removed": duplicated,
        "identifiers_remapped": sum(1 for raw, m in zip(tails, mapped, strict=True)
                                    if m is not None and m != raw),
        "rejected_unmappable": sum(1 for m in mapped if m is None),
        "missing_values": int(rng.binomial(len(logbook), 0.02)),
        "accepted_records": sum(1 for m in mapped if m in known_tails),
        "linked_to_work_orders": sum(1 for e in faults if e.severity >= 4),
    })

    # 3. Stores: issue, receipt and repair-return transactions.
    transactions = [t for t in world.transactions if t.day >= first_day]
    parts = [_part_variant(rng, COMPONENT_TYPES[t.part].part_number) for t in transactions]
    mapped_parts = [normalise_part(p) for p in parts]
    issued = [t for t in transactions if t.kind == "issue"]
    sources.append({
        "id": "spares_inventory",
        "name": "Stores and spares system",
        "owner": "Logistics",
        "format": "stock transactions with part numbers and locations",
        "identifier_example": parts[0] if parts else "",
        "timestamp_format": "transaction date (UTC)",
        "raw_records": len(transactions),
        "duplicates_removed": 0,
        "identifiers_remapped": sum(1 for raw, m in zip(parts, mapped_parts, strict=True)
                                    if m is not None and m != raw),
        "rejected_unmappable": sum(1 for m in mapped_parts if m not in known_parts),
        "missing_values": 0,
        "accepted_records": sum(1 for m in mapped_parts if m in known_parts),
        "issues_linked_to_work_orders": sum(1 for t in issued if t.work_order),
    })

    # 4. Agency reports: work orders with promised and actual completion dates.
    agency_rows = [wo for wo in world.work_orders if (wo.done or world.days) >= first_day]
    late = sum(1 for wo in agency_rows if wo.done is not None and
               wo.done - wo.opened > wo.repair_days + 2)
    sources.append({
        "id": "agency_reports",
        "name": "Maintenance agency reports",
        "owner": "Line, base and depot agencies",
        "format": "work-order status with promised and actual dates",
        "identifier_example": f"{'LINE'}/{agency_rows[0].id}" if agency_rows else "",
        "timestamp_format": "agency local date, converted to UTC date",
        "raw_records": len(agency_rows),
        "duplicates_removed": 0,
        "identifiers_remapped": len(agency_rows),
        "rejected_unmappable": 0,
        "missing_values": sum(1 for wo in agency_rows if wo.done is None),
        "accepted_records": len(agency_rows),
        "late_against_promise": late,
    })

    for source in sources:
        raw = max(int(source["raw_records"]), 1)  # type: ignore[call-overload]
        accepted = int(source["accepted_records"])  # type: ignore[call-overload]
        missing_rate = int(source["missing_values"]) / raw  # type: ignore[call-overload]
        source["quality_score"] = round(100 * min(1.0, accepted / raw) * (1 - missing_rate), 1)

    return {
        "window": {
            "from": world.day_date(first_day).isoformat(),
            "to": world.day_date(world.days - 1).isoformat(),
            "days": WINDOW_DAYS,
        },
        "defects_injected": "identifier variants, mixed date formats, duplicate downloads, "
        "dropouts, stuck values, spikes and unmappable legacy identifiers are injected "
        "deliberately into synthetic extracts",
        "unified_model": {
            "aircraft": len(world.aircraft_ids),
            "systems": len(SYSTEMS),
            "component_types": len(COMPONENT_TYPES),
            "component_positions": world.slots,
            "part_numbers": len(known_parts),
            "bases": len(BASES),
            "part_instances_tracked": len(world.instances),
        },
        "sources": sources,
        "coverage_end": (world.start + timedelta(days=world.days - 1)).isoformat(),
    }
