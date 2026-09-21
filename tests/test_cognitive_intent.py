"""Unit tests for Cognitive Intent Resolution and Lenient Parameter Normalization."""

import pytest
from jarvis.actions.registry import (
    ToolDefinition,
    ToolResult,
    normalize_tool_name,
    normalize_tool_params,
    registry,
)
from jarvis.brain.llm import ToolCall
from jarvis.brain.router import Router
from jarvis.config import Config
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


def test_normalize_tool_name() -> None:
    """Test string normalization of tool names."""
    assert normalize_tool_name("open_app") == "openapp"
    assert normalize_tool_name("open-app") == "openapp"
    assert normalize_tool_name("OpenApp") == "openapp"
    assert normalize_tool_name("antigravity_token_usage") == "antigravitytokenusage"


def test_normalize_tool_params_aliasing() -> None:
    """Test mapping and type casting of raw LLM arguments to tool signatures."""
    tool_def = registry.get_tool("open_app")
    assert tool_def is not None

    # LLM passes 'appname' instead of 'app_name'
    raw1 = {"appname": "visual studio code"}
    norm1 = normalize_tool_params(tool_def, raw1)
    assert norm1 == {"app_name": "visual studio code"}

    # LLM passes 'name'
    raw2 = {"name": "notepad"}
    norm2 = normalize_tool_params(tool_def, raw2)
    assert norm2 == {"app_name": "notepad"}


def test_normalize_tool_params_type_casting() -> None:
    """Test integer conversion from strings with percentages or words."""
    tool_def = registry.get_tool("set_brightness")
    assert tool_def is not None

    raw = {"level": "50%"}
    norm = normalize_tool_params(tool_def, raw)
    assert norm == {"level": 50}


@pytest.mark.asyncio
async def test_cognitive_intent_implicit_volume(config: Config, gate: SafetyGate) -> None:
    """Test implicit volume request mapped to set_volume tool."""
    fake_llm = FakeLLM(
        tool_calls=[ToolCall(name="set_volume", arguments={"level": "down"})]
    )
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("it's way too loud in here, turn it down")
    assert len(resp.tool_results) == 1
    assert "set_volume" in resp.reply or "down" in resp.reply


@pytest.mark.asyncio
async def test_cognitive_intent_pure_chat_no_tools(config: Config, gate: SafetyGate) -> None:
    """Test direct conversational question produces plain text with zero tools called."""
    fake_llm = FakeLLM(text_reply="The capital of Japan is Tokyo.")
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("What is the capital of Japan?")
    assert len(resp.tool_results) == 0
    assert resp.reply == "The capital of Japan is Tokyo."


@pytest.mark.asyncio
async def test_cognitive_multi_action_chaining(config: Config, gate: SafetyGate) -> None:
    """Test compound request triggering multiple tool calls."""
    fake_llm = FakeLLM(
        tool_calls=[
            ToolCall(name="set_brightness", arguments={"level": 30}),
            ToolCall(name="open_app", arguments={"app_name": "notepad"}),
        ]
    )
    router = Router(config=config, gate=gate, llm_client=fake_llm)

    resp = await router.route_and_execute("dim the screen to 30 and open notepad")
    assert len(resp.tool_results) == 2
