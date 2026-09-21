"""Tool registry, @tool decorator, and Ollama schema generator."""

import asyncio
import inspect
import re
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union
from pydantic import BaseModel, Field


def normalize_tool_name(name: str) -> str:
    """Normalize tool name by stripping punctuation, whitespace, and lowercasing."""
    return re.sub(r"[^a-zA-Z0-9]", "", name).lower()


PARAM_ALIASES: Dict[str, List[str]] = {
    "app_name": ["app_name", "appname", "app", "application", "name", "process", "program"],
    "folder_name": ["folder_name", "foldername", "folder", "path", "dir", "directory"],
    "path": ["path", "folder_name", "folder", "dir", "directory", "file", "target"],
    "query": ["query", "q", "search_query", "search", "term", "text", "keywords"],
    "text": ["text", "note", "content", "message", "body", "input"],
    "url": ["url", "site", "website", "link", "target"],
    "site_name": ["site_name", "sitename", "site", "website", "name", "url", "target"],
    "level": ["level", "volume", "brightness", "val", "value", "percent", "percentage"],
    "mode": ["mode", "target_mode", "new_mode", "state"],
    "command": ["command", "cmd", "slash_command", "name"],
    "seconds": ["seconds", "duration", "time", "secs", "s"],
    "minutes": ["minutes", "mins", "m"],
}


def normalize_tool_params(tool: "ToolDefinition", raw_params: Dict[str, Any]) -> Dict[str, Any]:
    """Map raw LLM arguments to exact tool parameter signatures and types."""
    if not raw_params:
        return {}

    normalized: Dict[str, Any] = {}
    sig = inspect.signature(tool.func)
    expected_params = list(sig.parameters.keys())

    # Map raw_params keys
    for exp_param in expected_params:
        # 1. Exact match
        if exp_param in raw_params:
            normalized[exp_param] = raw_params[exp_param]
            continue

        # 2. Normalized key match (e.g. appname -> app_name)
        exp_clean = normalize_tool_name(exp_param)
        found = False
        for raw_k, raw_v in raw_params.items():
            if normalize_tool_name(raw_k) == exp_clean:
                normalized[exp_param] = raw_v
                found = True
                break
        if found:
            continue

        # 3. Alias match
        aliases = PARAM_ALIASES.get(exp_param, [])
        for alias in aliases:
            for raw_k, raw_v in raw_params.items():
                if normalize_tool_name(raw_k) == normalize_tool_name(alias):
                    normalized[exp_param] = raw_v
                    found = True
                    break
            if found:
                break

    # If no parameters were mapped but tool accepts 1 param and raw_params has 1 value
    if not normalized and len(expected_params) == 1 and len(raw_params) == 1:
        normalized[expected_params[0]] = list(raw_params.values())[0]

    # Type casting
    for exp_param, val in list(normalized.items()):
        param_obj = sig.parameters.get(exp_param)
        if not param_obj:
            continue
        annotation = param_obj.annotation

        # Int casting
        if annotation is int or (tool.params.get(exp_param, {}).get("type") in ["integer", "int"]):
            if isinstance(val, str):
                digits = re.findall(r"\d+", val)
                if digits:
                    normalized[exp_param] = int(digits[0])
            elif isinstance(val, float):
                normalized[exp_param] = int(val)

        # Float casting
        elif annotation is float or (tool.params.get(exp_param, {}).get("type") in ["number", "float"]):
            if isinstance(val, str):
                digits = re.findall(r"[\d.]+", val)
                if digits:
                    normalized[exp_param] = float(digits[0])
            elif isinstance(val, int):
                normalized[exp_param] = float(val)

    return normalized


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
        self._normalized_index: Dict[str, ToolDefinition] = {}

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
            tool_def = ToolDefinition(
                name=name,
                description=description,
                params=params,
                risk=risk,
                func=func,
            )
            self._tools[name] = tool_def
            self._normalized_index[normalize_tool_name(name)] = tool_def
            return func

        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve a tool definition by exact or normalized name."""
        if name in self._tools:
            return self._tools[name]
        return self._normalized_index.get(normalize_tool_name(name))

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

        clean_params = normalize_tool_params(tool, params)

        try:
            if inspect.iscoroutinefunction(tool.func):
                result = await tool.func(**clean_params)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool.func(**clean_params))

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

