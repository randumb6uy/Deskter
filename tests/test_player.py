"""Unit tests for AudioPlayer and Barge-in cancellation."""

import time
import pytest

from jarvis.audio.player import AudioPlayer
from jarvis.config import Config
from jarvis.core.events import EventBus, SpeechFinishedEvent, SpeechStartedEvent
from tests.fakes import FakeTTS


def test_audio_player_queuing_and_barge_in() -> None:
    config = Config()
    bus = EventBus()
    fake_engine = FakeTTS()

    player = AudioPlayer(config=config, bus=bus, engine=fake_engine)

    # Queue multiple sentences
    player.speak("First sentence. Second sentence. Third sentence.")
    time.sleep(0.05)

    # Test immediate interruption
    player.stop()
    assert player.is_speaking is False


def test_audio_player_events() -> None:
    config = Config()
    bus = EventBus()
    fake_engine = FakeTTS()

    started_events = []
    finished_events = []

    bus.subscribe(SpeechStartedEvent, lambda e: started_events.append(e))
    bus.subscribe(SpeechFinishedEvent, lambda e: finished_events.append(e))

    player = AudioPlayer(config=config, bus=bus, engine=fake_engine)
    player.speak("Testing event publishing.")

    time.sleep(0.05)
    player.stop()
