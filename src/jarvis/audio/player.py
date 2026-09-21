"""Audio player with sentence streaming and instant barge-in cancellation."""

import asyncio
import logging
import queue
import re
import threading
import time
from typing import List, Optional

from jarvis.audio.tts import BaseTTSEngine, get_tts_engine
from jarvis.config import Config
from jarvis.core.events import EventBus, SpeechFinishedEvent, SpeechStartedEvent

logger = logging.getLogger("jarvis.audio.player")


def split_sentences(text: str) -> List[str]:
    """Split text into sentence chunks for streaming audio playback."""
    # Clean text from markdown formatting or excess whitespace
    cleaned = re.sub(r"[\*\_#`]", "", text).strip()
    if not cleaned:
        return []

    # Split by standard sentence delimiters (. ! ? \n)
    parts = re.split(r"(?<=[.!?\n])\s+", cleaned)
    sentences = [p.strip() for p in parts if p.strip()]
    return sentences if sentences else [cleaned]


class AudioPlayer:
    """Non-blocking streaming TTS player with barge-in interruption."""

    def __init__(
        self,
        config: Config,
        bus: Optional[EventBus] = None,
        engine: Optional[BaseTTSEngine] = None,
    ) -> None:
        self.config = config
        self.bus = bus
        self.engine = engine or get_tts_engine(config)
        self._queue: queue.Queue[Optional[str]] = queue.Queue()
        self._stop_event = threading.Event()
        self._is_speaking = False
        self._worker_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self._worker_thread.start()

    @property
    def is_speaking(self) -> bool:
        """True if speech audio is currently being played."""
        return self._is_speaking

    def _playback_loop(self) -> None:
        """Background worker consuming and speaking sentence chunks."""
        while True:
            try:
                item = self._queue.get()
                if item is None:
                    continue

                if self._stop_event.is_set():
                    self._queue.task_done()
                    continue

                self._is_speaking = True
                if self.bus:
                    self.bus.publish_threadsafe(SpeechStartedEvent(text=item))

                # Synthesize and speak directly
                try:
                    self.engine.speak_direct(item)
                except Exception as e:
                    logger.error(f"Playback error on '{item}': {e}")

                self._is_speaking = False
                if self.bus and self._queue.empty():
                    self.bus.publish_threadsafe(SpeechFinishedEvent())

                self._queue.task_done()

            except Exception as e:
                logger.error(f"Error in audio playback loop: {e}")
                self._is_speaking = False

    def speak(self, text: str, blocking: bool = False) -> None:
        """Enqueue text for streaming spoken playback."""
        if not text or not text.strip():
            return

        # Reset stop event for new speech
        self._stop_event.clear()
        sentences = split_sentences(text)

        for sentence in sentences:
            if self._stop_event.is_set():
                break
            self._queue.put(sentence)

        if blocking:
            self._queue.join()

    def stop(self) -> None:
        """Instantly interrupt and cancel active speech playback."""
        self._stop_event.set()
        # Drain any queued sentences
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

        self._is_speaking = False
        if self.bus:
            self.bus.publish_threadsafe(SpeechFinishedEvent())
        logger.info("Speech playback stopped immediately (barge-in).")
