"""Unit tests for TTS engines and sentence splitting."""

import tempfile
from pathlib import Path
import pytest

from jarvis.audio.player import split_sentences
from jarvis.audio.tts import PiperTTSEngine, SapiTTSEngine, get_tts_engine
from jarvis.config import Config


def test_sentence_splitting() -> None:
    text = "Hello there! This is Deskter. I am ready to help you with coding; let's get started."
    sentences = split_sentences(text)
    assert len(sentences) >= 3
    assert "Hello there!" in sentences[0]
    assert "This is Deskter." in sentences[1]


def test_sapi_tts_engine_synthesize_file() -> None:
    engine = SapiTTSEngine()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        wav_path = tf.name

    try:
        success = engine.synthesize_to_file("Testing SAPI speech synthesis.", wav_path)
        assert success is True
        assert Path(wav_path).exists()
        assert Path(wav_path).stat().st_size > 0
    finally:
        if Path(wav_path).exists():
            try:
                Path(wav_path).unlink()
            except Exception:
                pass


def test_tts_engine_factory_fallback() -> None:
    config = Config()
    config.tts.engine = "piper"
    engine = get_tts_engine(config)
    assert isinstance(engine, (PiperTTSEngine, SapiTTSEngine))
