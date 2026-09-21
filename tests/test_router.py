"""Unit tests for Brain Router."""

import pytest
import jarvis.actions  # Ensure tools are registered
from jarvis.brain.llm import ToolCall
from jarvis.brain.memory import ConversationMemory
from jarvis.brain.router import Router
from jarvis.config import Config
from jarvis.core.events import EventBus
from jarvis.safety.gate import SafetyGate
from tests.fakes import FakeLLM


@pytest.fixture
def config() -> Config:
    cfg = Config()
    cfg.assistant.dry_run = True
    return cfg


@pytest.fixture
def gate(config: Config) -> SafetyGate:
    return SafetyGate(config)


@pytest.mark.asyncio
async def test_router_fast_path(config: Config, gate: SafetyGate) -> None:
    fake_llm = FakeLLM(text_reply="LLM should not be called")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    # Fast path command
    resp = await router.route_and_execute("what time is it")
    assert resp.fast_path is True
    assert len(fake_llm.received_messages) == 0  # LLM was not touched
    assert len(resp.tool_results) == 1
    assert "Dry Run" in resp.reply or "It is" in resp.reply


@pytest.mark.asyncio
async def test_router_slow_path_tool_call(config: Config, gate: SafetyGate) -> None:
    # Query not in fast path regexes
    fake_llm = FakeLLM(
        tool_calls=[ToolCall(name="get_battery", arguments={})]
    )
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("Hey could you please check how much juice my laptop has left?")
    assert resp.fast_path is False
    assert len(fake_llm.received_messages) == 1
    assert len(resp.tool_results) == 1
    assert resp.tool_results[0].ok is True


@pytest.mark.asyncio
async def test_router_slow_path_pure_chat(config: Config, gate: SafetyGate) -> None:
    fake_llm = FakeLLM(text_reply="The capital of France is Paris.")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("What is the capital of France?")
    assert resp.fast_path is False
    assert resp.reply == "The capital of France is Paris."
    assert len(resp.tool_results) == 0


@pytest.mark.asyncio
async def test_router_llm_error_handling(config: Config, gate: SafetyGate) -> None:
    fake_llm = FakeLLM(error="Connection refused to Ollama")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("Explain general relativity")
    assert resp.fast_path is False
    assert "can't reach my language model" in resp.reply
    assert resp.error is not None
