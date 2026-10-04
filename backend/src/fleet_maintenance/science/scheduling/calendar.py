"""Convert timezone-aware windows inward onto a conservative fixed planning grid."""

import math
from datetime import datetime


def calendar_slots(
    epoch: datetime,
    windows: tuple[tuple[datetime, datetime], ...],
    *,
    horizon: int = 14,
    slot_hours: int = 8,
) -> tuple[tuple[int, int], ...]:
    if epoch.utcoffset() is None or horizon <= 0 or slot_hours <= 0:
        raise ValueError("A timezone-aware epoch and positive grid are required")
    intervals = []
    for start, end in windows:
        if start.utcoffset() is None or end.utcoffset() is None or end <= start:
            raise ValueError("Calendar windows require increasing timezone-aware timestamps")
        left = max(0, math.ceil((start.timestamp() - epoch.timestamp()) / (slot_hours * 3600)))
        right = min(
            horizon, math.floor((end.timestamp() - epoch.timestamp()) / (slot_hours * 3600))
        )
        if left < right:
            intervals.append((left, right))
    merged: list[tuple[int, int]] = []
    for left, right in sorted(intervals):
        if merged and left <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], right))
        else:
            merged.append((left, right))
    return tuple(merged)
