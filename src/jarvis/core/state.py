"""State definitions for the Jarvis assistant state machine."""

from enum import Enum


class AssistantState(str, Enum):
    """The lifecycle states of the offline desktop voice assistant."""
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"

    def __str__(self) -> str:
        return self.value
