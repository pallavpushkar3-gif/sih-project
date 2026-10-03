import pytest

from fleet_maintenance.workers.task_lifecycle import transition


def test_valid_job_lifecycle():
    assert transition("queued", "running") == "running"


def test_terminal_result_is_immutable():
    with pytest.raises(ValueError):
        transition("succeeded", "running")
