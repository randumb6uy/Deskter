"""Unit tests for ToolRegistry and @tool decorator."""

import pytest
from jarvis.actions.registry import ToolRegistry, ToolResult


@pytest.mark.asyncio
async def test_tool_registration_and_execution():
    test_reg = ToolRegistry()

    @test_reg.register(
        name="test_tool",
        description="A test calculation tool",
        params={"x": {"type": "integer", "description": "Number to multiply"}},
        risk="low",
    )
    def multiply_by_two(x: int) -> ToolResult:
        return ToolResult(ok=True, message=f"Result is {x * 2}", data={"val": x * 2})

    tool_def = test_reg.get_tool("test_tool")
    assert tool_def is not None
    assert tool_def.name == "test_tool"
    assert tool_def.risk == "low"

    # Execute
    res = await test_reg.execute("test_tool", x=5)
    assert res.ok is True
    assert res.message == "Result is 10"
    assert res.data == {"val": 10}


@pytest.mark.asyncio
async def test_async_tool_execution():
    test_reg = ToolRegistry()

    @test_reg.register(name="async_echo", description="Async echo tool", risk="low")
    async def async_echo(text: str) -> ToolResult:
        return ToolResult(ok=True, message=f"Echo: {text}")

    res = await test_reg.execute("async_echo", text="hello")
    assert res.ok is True
    assert res.message == "Echo: hello"


def test_ollama_schema_generation():
    test_reg = ToolRegistry()

    @test_reg.register(
        name="weather_check",
        description="Check weather for a city",
        params={"city": {"type": "string", "description": "City name"}},
        risk="low",
    )
    def check_weather(city: str) -> ToolResult:
        return ToolResult(ok=True, message=f"Weather in {city}")

    schemas = test_reg.get_ollama_tools_schema()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "weather_check"
    assert "city" in schemas[0]["function"]["parameters"]["properties"]
    assert "city" in schemas[0]["function"]["parameters"]["required"]
