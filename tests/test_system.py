"""Unit tests for system time, date, battery tools."""

from jarvis.actions.system import get_time, get_date, get_battery


def test_get_time():
    res = get_time()
    assert res.ok is True
    assert "time" in res.data
    assert ":" in res.data["time"]


def test_get_date():
    res = get_date()
    assert res.ok is True
    assert "date" in res.data
    assert len(res.data["date"]) > 5


def test_get_battery():
    res = get_battery()
    assert res.ok is True
    assert isinstance(res.message, str)
