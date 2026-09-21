"""Unit tests for Google Antigravity Voice Bridge tools and rule patterns."""

import pytest
import jarvis.actions  # Ensure tools are registered
from jarvis.actions.antigravity_bridge import (
    antigravity_clear_history,
    antigravity_compact_context,
    antigravity_list_subagents,
    antigravity_prompt,
    antigravity_set_mode,
    antigravity_slash_command,
    antigravity_status,
    antigravity_token_usage,
)
from jarvis.actions.registry import registry
from jarvis.brain.rules import RuleMatcher


def test_antigravity_tools_registered() -> None:
    expected_tools = [
        "antigravity_prompt",
        "antigravity_token_usage",
        "antigravity_set_mode",
        "antigravity_status",
        "antigravity_slash_command",
        "antigravity_list_subagents",
        "antigravity_compact_context",
        "antigravity_clear_history",
    ]
    for name in expected_tools:
        tool = registry.get_tool(name)
        assert tool is not None, f"Tool {name} not found in registry."


def test_antigravity_token_usage_execution() -> None:
    res = antigravity_token_usage()
    assert res.ok is True
    assert "tokens" in res.message
    assert "turns" in res.message


def test_antigravity_prompt_execution() -> None:
    res = antigravity_prompt("Create a FastAPI health check route")
    assert res.ok is True
    assert "FastAPI" in res.message


def test_antigravity_set_mode_execution() -> None:
    res = antigravity_set_mode("accept edits")
    assert res.ok is True
    assert "Accept Edits" in res.message


def test_antigravity_status_execution() -> None:
    res = antigravity_status()
    assert res.ok is True
    assert "Antigravity is active" in res.message


def test_antigravity_slash_command_execution() -> None:
    res = antigravity_slash_command("/goal")
    assert res.ok is True
    assert "goal" in res.message.lower()


def test_antigravity_rule_matching() -> None:
    matcher = RuleMatcher()

    # Token usage
    m = matcher.match("check the usage of tokens")
    assert m.matched is True
    assert m.tool_name == "antigravity_token_usage"

    # Set mode
    m = matcher.match("change mode to accept edits")
    assert m.matched is True
    assert m.tool_name == "antigravity_set_mode"
    assert m.params["mode"] == "accept edits"

    # Prompt
    m = matcher.match("ask Antigravity to write unit tests for the auth module")
    assert m.matched is True
    assert m.tool_name == "antigravity_prompt"
    assert "write unit tests" in m.params["prompt"]

    # Status
    m = matcher.match("antigravity status")
    assert m.matched is True
    assert m.tool_name == "antigravity_status"

    # Slash command
    m = matcher.match("/goal")
    assert m.matched is True
    assert m.tool_name == "antigravity_slash_command"
    assert m.params["command"] == "goal"

    # Quota check
    m = matcher.match("how much quota do i have")
    assert m.matched is True
    assert m.tool_name == "antigravity_quota"

    # Model info
    m = matcher.match("what model is running")
    assert m.matched is True
    assert m.tool_name == "antigravity_model_info"


def test_antigravity_quota_execution() -> None:
    from jarvis.actions.antigravity_bridge import antigravity_quota, antigravity_model_info, antigravity_cost_estimate
    res_quota = antigravity_quota()
    assert res_quota.ok is True
    assert "context window" in res_quota.message

    res_model = antigravity_model_info()
    assert res_model.ok is True
    assert "Gemini" in res_model.message

    res_cost = antigravity_cost_estimate()
    assert res_cost.ok is True
    assert "tokens" in res_cost.message
