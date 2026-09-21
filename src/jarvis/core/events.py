import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Type, Union
from pydantic import BaseModel, Field

from jarvis.core.state import AssistantState


class Event(BaseModel):
    """Base event payload."""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    name: str = "base_event"


class StateChangeEvent(Event):
    """Fired whenever the assistant state changes."""
    name: str = "state_change"
    old_state: AssistantState
    new_state: AssistantState


class WakeDetectedEvent(Event):
    """Fired when the wake word or push-to-talk hotkey triggers."""
    name: str = "wake_detected"
    source: str = "wakeword"  # 'wakeword' | 'hotkey' | 'text'


class TranscriptReadyEvent(Event):
    """Fired when STT has transcribed an utterance."""
    name: str = "transcript_ready"
    text: str


class ToolCallEvent(Event):
    """Fired when a tool is about to be executed."""
    name: str = "tool_called"
    tool_name: str
    params: Dict[str, Any]
    risk: str = "low"


class ToolResultEvent(Event):
    """Fired when a tool execution completes."""
    name: str = "tool_result"
    tool_name: str
    ok: bool
    message: str
    data: Any = None
    execution_time_ms: float = 0.0


class SpeechStartedEvent(Event):
    """Fired when TTS starts speaking audio."""
    name: str = "speech_started"
    text: str


class SpeechFinishedEvent(Event):
    """Fired when TTS finishes speaking."""
    name: str = "speech_finished"


class AudioLevelEvent(Event):
    """Fired periodically with input audio RMS level for visualizers."""
    name: str = "audio_level"
    level: float  # 0.0 to 1.0


class ErrorEvent(Event):
    """Fired when an error or exception occurs in the pipeline."""
    name: str = "error"
    message: str
    context: str = ""
    recoverable: bool = True


EventHandler = Union[
    Callable[[Event], Coroutine[Any, Any, None]],
    Callable[[Event], None]
]


class EventBus:
    """Asynchronous and thread-safe publish-subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[Type[Event], List[EventHandler]] = {}
        self._wildcard_subscribers: List[EventHandler] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Assign the active asyncio event loop."""
        self._loop = loop

    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Subscribe a callback to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a callback to all events published on the bus."""
        if handler not in self._wildcard_subscribers:
            self._wildcard_subscribers.append(handler)

    def unsubscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Unsubscribe a callback from a specific event type."""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all registered listeners asynchronously."""
        handlers: List[EventHandler] = []
        
        # Exact type subscribers
        if type(event) in self._subscribers:
            handlers.extend(self._subscribers[type(event)])

        # Wildcard subscribers
        handlers.extend(self._wildcard_subscribers)

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log or swallow error so one failing subscriber does not break others
                print(f"[EventBus] Error in event handler {handler}: {e}")

    def publish_threadsafe(self, event: Event) -> None:
        """Publish an event from a synchronous or worker thread into the asyncio loop."""
        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.publish(event), loop)
        else:
            # Synchronously trigger non-async handlers if loop is not active
            for handler in self._wildcard_subscribers:
                if not asyncio.iscoroutinefunction(handler):
                    try:
                        handler(event)
                    except Exception as e:
                        print(f"[EventBus] Error in sync handler {handler}: {e}")
