"""Actions package: tool registry and built-in modules."""

from jarvis.actions.registry import registry, tool, ToolResult, ToolDefinition

# Import all tool modules to trigger registration
import jarvis.actions.apps
import jarvis.actions.browser
import jarvis.actions.system
import jarvis.actions.media
import jarvis.actions.files
import jarvis.actions.utility
import jarvis.actions.antigravity_bridge

__all__ = ["registry", "tool", "ToolResult", "ToolDefinition"]
