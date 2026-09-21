"""Unit tests for configuration loader and defaults."""

from pathlib import Path
from jarvis.config import Config, load_config


def test_default_config_instantiation():
    config = Config()
    assert config.assistant.name == "Deskter"
    assert config.assistant.dry_run is False
    assert config.audio.sample_rate == 16000
    assert config.llm.provider == "ollama"
    assert config.tts.engine == "piper"
    assert len(config.files.allowed_roots) >= 3


def test_config_load_from_file():
    config = load_config(Path("config.yaml"))
    assert config.assistant.name == "Deskter"
    assert config.browser.bridge_port == 8765
    assert len(config.browser.blocked_domains) > 0


def test_files_allowed_roots_resolution():
    config = Config()
    resolved = config.files.get_resolved_roots()
    assert all(isinstance(p, Path) for p in resolved)
    assert all(p.is_absolute() for p in resolved)
