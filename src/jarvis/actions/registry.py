"""Tool registry, @tool decorator, and Ollama schema generator."""

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union
from pydantic import BaseModel, Field


@dataclass
class ToolResult:
    """Standardized tool return type."""
    ok: bool
    message: str
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "data": self.data,
        }


@dataclass
class ToolDefinition:
    """Metadata and execution target for a registered tool."""
    name: str
    description: str
    params: Dict[str, Any]
    risk: str
    func: Callable[..., Union[ToolResult, Coroutine[Any, Any, ToolResult]]]

    def to_ollama_tool(self) -> Dict[str, Any]:
        """Generate Ollama-compatible JSON schema definition."""
        properties: Dict[str, Any] = {}
        required: List[str] = []

        for param_name, param_meta in self.params.items():
            prop: Dict[str, Any] = {
                "type": param_meta.get("type", "string"),
                "description": param_meta.get("description", ""),
            }
            if "enum" in param_meta:
                prop["enum"] = param_meta["enum"]
            properties[param_name] = prop

            if param_meta.get("required", True):
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class ToolRegistry:
    """Central registry for all executable tools in Jarvis."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        params: Optional[Dict[str, Any]] = None,
        risk: str = "low",
    ) -> Callable[[Callable], Callable]:
        """Decorator to register a function as an assistant tool."""
        if params is None:
            params = {}

        def decorator(func: Callable) -> Callable:
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                params=params,
                risk=risk,
                func=func,
            )
            return func

        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_ollama_tools_schema(self) -> List[Dict[str, Any]]:
        """Generate full list of Ollama tools schema."""
        return [tool.to_ollama_tool() for tool in self._tools.values()]

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        """Alias for get_ollama_tools_schema."""
        return self.get_ollama_tools_schema()

    async def execute(self, name: str, **params) -> ToolResult:
        """Execute a tool by name with provided keyword parameters."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                ok=False,
                message=f"I don't have a tool named '{name}'.",
                data={"error": "Tool not found"},
            )

        try:
            if inspect.iscoroutinefunction(tool.func):
                result = await tool.func(**params)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool.func(**params))

            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, str):
                return ToolResult(ok=True, message=result)
            elif isinstance(result, tuple) and len(result) == 2:
                return ToolResult(ok=bool(result[0]), message=str(result[1]))
            else:
                return ToolResult(ok=True, message="Action completed.", data={"raw": result})

        except TypeError as te:
            return ToolResult(
                ok=False,
                message=f"Invalid arguments for {name}.",
                data={"error": str(te)},
            )
        except Exception as e:
            return ToolResult(
                ok=False,
                message=f"Error executing {name}: {str(e)}",
                data={"error": str(e)},
            )


# Global singleton tool registry
registry = ToolRegistry()
tool = registry.register
