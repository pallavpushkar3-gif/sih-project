import pytest

from fleet_maintenance.domain.units import require_unit


def test_supported_unit_is_retained():
    assert require_unit("cycles") == "cycles"


def test_unknown_unit_is_rejected():
    with pytest.raises(ValueError):
        require_unit("minutes")
