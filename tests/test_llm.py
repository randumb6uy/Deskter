"""Unit tests for Ollama LLM client and auto-start daemon functionality."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.brain.llm import (
    LlmClient,
    ToolCall,
    ensure_ollama_running,
    find_ollama_executable,
    is_ollama_running,
    start_ollama_daemon,
)
from jarvis.config import LlmConfig


def test_find_ollama_executable() -> None:
    """Test locating Ollama executable."""
    with patch("shutil.which", return_value="C:\\fake\\ollama.exe"):
        exe = find_ollama_executable()
        assert exe == Path("C:\\fake\\ollama.exe")


def test_is_ollama_running_true() -> None:
    """Test is_ollama_running when server responds with 200."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        assert is_ollama_running("http://localhost:11434") is True


def test_is_ollama_running_false() -> None:
    """Test is_ollama_running when connection fails."""
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        assert is_ollama_running("http://localhost:11434") is False


def test_start_ollama_daemon_already_running() -> None:
    """Test start_ollama_daemon returns True immediately if already running."""
    with patch("jarvis.brain.llm.is_ollama_running", return_value=True):
        assert start_ollama_daemon("http://localhost:11434") is True


def test_start_ollama_daemon_spawns_process() -> None:
    """Test start_ollama_daemon successfully launches process and waits for ready."""
    states = [False, False, True]

    def mock_is_running(*args, **kwargs):
        return states.pop(0) if states else True

    with patch("jarvis.brain.llm.is_ollama_running", side_effect=mock_is_running), \
         patch("jarvis.brain.llm.find_ollama_executable", return_value=Path("C:\\fake\\ollama.exe")), \
         patch("subprocess.Popen") as mock_popen, \
         patch("time.sleep"):
        success = start_ollama_daemon("http://localhost:11434", timeout_s=5.0)
        assert success is True
        mock_popen.assert_called_once()


def test_ensure_ollama_running_disabled() -> None:
    """Test ensure_ollama_running when auto_start is False."""
    cfg = LlmConfig(auto_start=False)
    with patch("jarvis.brain.llm.is_ollama_running", return_value=True) as mock_is_running:
        assert ensure_ollama_running(cfg) is True
        mock_is_running.assert_called_once_with("http://localhost:11434")


def test_ensure_ollama_running_enabled() -> None:
    """Test ensure_ollama_running triggers start when enabled and not running."""
    cfg = LlmConfig(auto_start=True)
    with patch("jarvis.brain.llm.is_ollama_running", return_value=False), \
         patch("jarvis.brain.llm.start_ollama_daemon", return_value=True) as mock_start:
        assert ensure_ollama_running(cfg) is True
        mock_start.assert_called_once_with("http://localhost:11434", timeout_s=10.0)


def test_llm_json_fallback_extraction() -> None:
    """Test JSON tool call fallback extraction when model outputs JSON text."""
    client = LlmClient(LlmConfig(auto_start=False))

    # Single JSON object
    text1 = '```json\n{"name": "get_volume", "arguments": {}}\n```'
    extracted1 = client._extract_json_tool_calls(text1)
    assert len(extracted1) == 1
    assert extracted1[0].name == "get_volume"

    # Raw JSON dict
    text2 = '{"tool": "set_volume", "parameters": {"level": 60}}'
    extracted2 = client._extract_json_tool_calls(text2)
    assert len(extracted2) == 1
    assert extracted2[0].name == "set_volume"
    assert extracted2[0].arguments == {"level": 60}
