from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class QualityFinding:
    code: str
    severity: str
    message: str


def validate_history(rows: list[dict[str, object]]) -> list[QualityFinding]:
    findings: list[QualityFinding] = []
    if not rows:
        return [QualityFinding("empty_history", "error", "No observations are available.")]
    raw_cycles = [row["cycle"] for row in rows if "cycle" in row]
    cycles: list[int] = []
    for value in raw_cycles:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            findings.append(QualityFinding("invalid_cycle", "error", "A cycle index is invalid."))
            continue
        cycles.append(int(value))
    if len(raw_cycles) != len(rows):
        findings.append(QualityFinding("missing_cycle", "error", "A cycle index is missing."))
    if cycles != sorted(cycles):
        findings.append(QualityFinding("out_of_order", "error", "Cycles are out of order."))
    if len(cycles) != len(set(cycles)):
        findings.append(QualityFinding("duplicate_cycle", "error", "Duplicate cycles were found."))
    for row in rows:
        for key, value in row.items():
            if key.startswith("sensor_") and (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(float(value))
            ):
                findings.append(
                    QualityFinding("invalid_sensor", "error", f"{key} is missing or invalid.")
                )
    return findings


def assessment_state(findings: list[QualityFinding]) -> str:
    return "withheld" if any(item.severity == "error" for item in findings) else "eligible"
