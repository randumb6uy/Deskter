"""Fake/Mock components for unit testing without hardware or network."""

import asyncio
from typing import Any, Dict, List, Optional

from jarvis.actions.registry import ToolResult
from jarvis.brain.llm import LlmResponse, ToolCall


class FakeMic:
    """Simulates audio stream from microphone."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate
        self.is_running = False

    def start(self) -> None:
        self.is_running = True

    def stop(self) -> None:
        self.is_running = False


class FakeSTT:
    """Mock speech-to-text transcriber."""

    def __init__(self, preset_response: str = "open notepad") -> None:
        self.preset_response = preset_response

    async def transcribe(self, audio_data: Any) -> str:
        return self.preset_response


class FakeTTS:
    """Mock text-to-speech engine."""

    def __init__(self) -> None:
        self.spoken_phrases: List[str] = []
        self.is_speaking = False

    async def speak(self, text: str) -> None:
        self.spoken_phrases.append(text)
        self.is_speaking = True
        await asyncio.sleep(0.01)
        self.is_speaking = False

    def stop(self) -> None:
        self.is_speaking = False


class FakeLLM:
    """Mock local LLM client for testing Router and Brain components."""

    def __init__(
        self,
        tool_calls: Optional[List[ToolCall]] = None,
        text_reply: str = "I am ready.",
        error: Optional[str] = None,
    ) -> None:
        self.tool_calls = tool_calls or []
        self.text_reply = text_reply
        self.error = error
        self.received_messages: List[List[Dict[str, Any]]] = []

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LlmResponse:
        self.received_messages.append(messages)
        if self.error:
            return LlmResponse(content="I can't reach my language model.", error=self.error)
        return LlmResponse(
            content=self.text_reply if not self.tool_calls else "",
            tool_calls=self.tool_calls,
        )
