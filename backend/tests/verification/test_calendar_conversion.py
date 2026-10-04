from datetime import datetime

import pytest

from fleet_maintenance.science.scheduling.calendar import calendar_slots


def test_timezone_conversion_rounds_inward_and_preserves_a_closure():
    parse = datetime.fromisoformat
    epoch = parse("2026-10-05T00:00:00+00:00")
    windows = (
        (parse("2026-10-05T06:30:00+05:30"), parse("2026-10-06T05:30:00+05:30")),
        (parse("2026-10-06T13:30:00+05:30"), parse("2026-10-07T05:30:00+05:30")),
    )
    assert calendar_slots(epoch, windows) == ((1, 3), (4, 6))
    with pytest.raises(ValueError, match="timezone-aware"):
        calendar_slots(datetime(2026, 10, 5), windows)
