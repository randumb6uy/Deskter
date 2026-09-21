"""Unit tests for utility tools (notes, timers, help)."""

import pytest
from pathlib import Path
from jarvis.actions.utility import take_note, get_notes, set_timer, get_help, NOTES_FILE


def test_take_and_get_notes(tmp_path, monkeypatch):
    test_notes_file = tmp_path / "test_notes.txt"
    monkeypatch.setattr("jarvis.actions.utility.NOTES_FILE", test_notes_file)

    # Empty initially
    res_empty = get_notes()
    assert res_empty.ok is True

    # Take note
    res_take = take_note("Remember to buy milk")
    assert res_take.ok is True
    assert "milk" in test_notes_file.read_text(encoding="utf-8")

    # Read note
    res_read = get_notes()
    assert res_read.ok is True
    assert "milk" in res_read.message


@pytest.mark.asyncio
async def test_set_timer():
    res = await set_timer(seconds=10, label="Test Timer")
    assert res.ok is True
    assert res.data["duration_seconds"] == 10


def test_get_help():
    res = get_help()
    assert res.ok is True
    assert "Jarvis" in res.message or "applications" in res.message
