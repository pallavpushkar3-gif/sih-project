"""Example FD001 CSV adapter, not an aircraft-system connection."""

import csv
import io
import math

from fleet_maintenance.domain.contracts.health import HistoryImport
from fleet_maintenance.science.data.loaders import FEATURE_NAMES


class AdapterValidationError(ValueError):
    def __init__(self, errors: list[dict[str, object]]):
        super().__init__("CSV batch rejected; no rows imported")
        self.errors = errors


def adapt_csv(
    text: str,
    source_version: str,
    engine_identity: str,
    previous_id: str | None = None,
) -> HistoryImport:
    if len(text.encode()) > 1_500_000:
        raise AdapterValidationError([{"row": 0, "error": "CSV exceeds 1.5 MB limit"}])
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != ["cycle", *FEATURE_NAMES]:
        raise AdapterValidationError(
            [{"row": 1, "error": "Expected cycle and the 24 ordered FD001 columns"}]
        )
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for number, row in enumerate(reader, start=2):
        if number > 10001:
            errors.append({"row": number, "error": "Maximum 10,000 observations"})
            break
        try:
            if None in row or any(row[name] is None for name in reader.fieldnames):
                raise ValueError("Missing or extra columns")
            cycle = int(row["cycle"])
            values = [None if not row[name].strip() else float(row[name]) for name in FEATURE_NAMES]
            if any(value is not None and not math.isfinite(value) for value in values):
                raise ValueError("Sensor/settings values must be finite or blank")
            if cycle != len(rows) + 1:
                raise ValueError("Cycles must be consecutive from one, without duplicates")
            rows.append({"cycle": cycle, "values": values})
        except (ValueError, TypeError, KeyError) as exc:
            errors.append({"row": number, "error": str(exc)})
            if len(errors) >= 20:
                break
    if errors:
        raise AdapterValidationError(errors)
    return HistoryImport.model_validate(
        {
            "source_version": source_version,
            "engine_identity": engine_identity,
            "previous_id": previous_id,
            "rows": rows,
        }
    )
