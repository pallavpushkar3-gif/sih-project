SUPPORTED_UNITS = {"cycles", "hours", "unknown_dataset_unit"}


def require_unit(unit: str, allowed: set[str] | None = None) -> str:
    permitted = allowed or SUPPORTED_UNITS
    if unit not in permitted:
        raise ValueError(f"Unsupported unit: {unit}")
    return unit
