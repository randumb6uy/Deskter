"""Unit tests for Cognitive Brain Router and ReAct Execution Loop."""

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
    cfg.llm.routing_mode = "llm_first"
    return cfg


@pytest.fixture
def gate(config: Config) -> SafetyGate:
    return SafetyGate(config)


@pytest.mark.asyncio
async def test_router_llm_first_tool_call(config: Config, gate: SafetyGate) -> None:
    """In llm_first mode, the LLM processes the query and selects tools."""
    fake_llm = FakeLLM(
        tool_calls=[ToolCall(name="get_battery", arguments={})]
    )
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("how much battery juice is left?")
    assert resp.fast_path is False
    assert len(fake_llm.received_messages) == 1
    assert len(resp.tool_results) == 1
    assert resp.tool_results[0].ok is True


@pytest.mark.asyncio
async def test_router_rules_first_mode(config: Config, gate: SafetyGate) -> None:
    """In rules_first mode, rule regex matches execute without hitting the LLM."""
    config.llm.routing_mode = "rules_first"
    fake_llm = FakeLLM(text_reply="LLM should not be called")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("what time is it")
    assert resp.fast_path is True
    assert len(fake_llm.received_messages) == 0  # LLM was not touched
    assert len(resp.tool_results) == 1


@pytest.mark.asyncio
async def test_router_emergency_stop(config: Config, gate: SafetyGate) -> None:
    """Emergency stop keywords return immediate fast path response."""
    fake_llm = FakeLLM(text_reply="Should not reach here")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("stop")
    assert resp.fast_path is True
    assert "Stopping" in resp.reply
    assert len(fake_llm.received_messages) == 0


@pytest.mark.asyncio
async def test_router_multi_tool_chaining(config: Config, gate: SafetyGate) -> None:
    """Test LLM returning multiple sequential tool calls in a single turn."""
    fake_llm = FakeLLM(
        tool_calls=[
            ToolCall(name="set_volume", arguments={"level": 20}),
            ToolCall(name="get_time", arguments={}),
        ]
    )
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("set volume to 20 and tell me the time")
    assert resp.fast_path is False
    assert len(resp.tool_results) == 2
    assert resp.tool_results[0].ok is True
    assert resp.tool_results[1].ok is True


@pytest.mark.asyncio
async def test_router_pure_chat(config: Config, gate: SafetyGate) -> None:
    """Test general question answering without tool invocations."""
    fake_llm = FakeLLM(text_reply="The speed of light in vacuum is approximately 300,000 km per second.")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("What is the speed of light?")
    assert resp.fast_path is False
    assert "speed of light" in resp.reply
    assert len(resp.tool_results) == 0


@pytest.mark.asyncio
async def test_router_llm_error_fallback(config: Config, gate: SafetyGate) -> None:
    """Test fallback when LLM fails."""
    fake_llm = FakeLLM(error="Connection refused to Ollama")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    # Command matching a known rule falls back to rule execution
    resp = await router.route_and_execute("what time is it")
    assert len(resp.tool_results) == 1 or "time" in resp.reply
