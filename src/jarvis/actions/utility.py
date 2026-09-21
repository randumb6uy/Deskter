"""Utility tools: timers, reminders, voice notes, and help metadata."""

import asyncio
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from jarvis.actions.registry import ToolResult, tool

logger = logging.getLogger("jarvis.actions.utility")

NOTES_FILE = Path("data/notes.txt")


@tool(
    name="set_timer",
    description="Set a countdown timer for a specified number of seconds or minutes.",
    params={
        "seconds": {"type": "integer", "description": "Timer duration in seconds (e.g. 60 for 1 minute, 300 for 5 minutes)"},
        "label": {"type": "string", "description": "Optional label for the timer", "required": False},
    },
    risk="low",
)
async def set_timer(seconds: int, label: str = "Timer") -> ToolResult:
    """Schedule a countdown timer."""
    seconds = int(seconds)
    if seconds <= 0:
        return ToolResult(ok=False, message="Timer duration must be greater than zero seconds.")

    mins = seconds // 60
    secs = seconds % 60
    time_str = f"{mins} minutes" if mins > 0 and secs == 0 else f"{seconds} seconds"

    async def _timer_worker(delay: int, name: str) -> None:
        await asyncio.sleep(delay)
        logger.info(f"Timer '{name}' expired after {delay} seconds.")

    # Launch background timer task
    asyncio.create_task(_timer_worker(seconds, label))

    return ToolResult(
        ok=True,
        message=f"Timer set for {time_str}.",
        data={"duration_seconds": seconds, "label": label},
    )


@tool(
    name="take_note",
    description="Save a quick text note to your notes file.",
    params={"text": {"type": "string", "description": "The note content to save"}},
    risk="low",
)
def take_note(text: str) -> ToolResult:
    """Append a note to data/notes.txt."""
    try:
        NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"[{timestamp}] {text.strip()}\n"

        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(entry)

        return ToolResult(
            ok=True,
            message="Note saved.",
            data={"text": text, "timestamp": timestamp},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to save note: {e}")


@tool(
    name="get_notes",
    description="Read back the most recent notes you have taken.",
    params={"limit": {"type": "integer", "description": "Maximum number of recent notes to read (default 3)", "required": False}},
    risk="low",
)
def get_notes(limit: int = 3) -> ToolResult:
    """Retrieve recent notes from notes file."""
    if not NOTES_FILE.exists():
        return ToolResult(ok=True, message="You don't have any saved notes yet.")

    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        if not lines:
            return ToolResult(ok=True, message="You don't have any saved notes yet.")

        recent = lines[-limit:]
        summary = " Next note: ".join(recent)
        return ToolResult(
            ok=True,
            message=f"Here are your latest notes: {summary}",
            data={"notes": recent},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Could not read notes: {e}")


@tool(
    name="help",
    description="Explain what Deskter can do and list available command categories.",
    params={},
    risk="low",
)
def get_help() -> ToolResult:
    """Provide overview of assistant capabilities."""
    help_text = (
        "I am Deskter. I can launch applications, search the web, control volume and brightness, "
        "manage browser tabs, take notes, set timers, and answer questions offline."
    )
    return ToolResult(ok=True, message=help_text)
