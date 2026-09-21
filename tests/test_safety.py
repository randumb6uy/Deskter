"""Unit tests for SafetyGate path restrictions and dry-run."""

import pytest
from pathlib import Path
from jarvis.actions.registry import ToolDefinition, ToolResult
from jarvis.config import Config
from jarvis.safety.gate import SafetyGate


@pytest.mark.asyncio
async def test_safety_gate_dry_run():
    config = Config()
    config.assistant.dry_run = True
    gate = SafetyGate(config)

    dummy_tool = ToolDefinition(
        name="format_disk",
        description="Dangerous tool",
        params={},
        risk="high",
        func=lambda: ToolResult(ok=True, message="Formatted"),
    )

    res = await gate.evaluate_and_execute(dummy_tool, {})
    assert res.ok is True
    assert "[Dry Run]" in res.message
    assert res.data["dry_run"] is True


@pytest.mark.asyncio
async def test_safety_gate_high_risk_confirmation():
    config = Config()
    config.safety.confirm_high_risk = True
    gate = SafetyGate(config)

    executed = False

    def dangerous_action():
        nonlocal executed
        executed = True
        return ToolResult(ok=True, message="Executed dangerous action")

    tool_def = ToolDefinition(
        name="shutdown_pc",
        description="Shutdown",
        params={},
        risk="high",
        func=dangerous_action,
    )

    # 1. Denied confirmation callback
    async def deny_cb(prompt: str) -> bool:
        return False

    res_denied = await gate.evaluate_and_execute(tool_def, {}, confirm_callback=deny_cb)
    assert res_denied.ok is False
    assert executed is False
    assert "cancelled" in res_denied.message

    # 2. Approved confirmation callback
    async def approve_cb(prompt: str) -> bool:
        return True

    res_approved = await gate.evaluate_and_execute(tool_def, {}, confirm_callback=approve_cb)
    assert res_approved.ok is True
    assert executed is True
