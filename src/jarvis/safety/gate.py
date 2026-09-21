"""Safety Gate: risk assessment, confirmations, path verification, and dry-run enforcement."""

import logging
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, Optional
from jarvis.actions.registry import ToolDefinition, ToolResult, normalize_tool_params
from jarvis.config import Config

logger = logging.getLogger("jarvis.safety")


class SafetyGate:
    """Evaluates tool execution risk and enforces security constraints."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.dry_run = config.assistant.dry_run
        self.allowed_roots = config.files.get_resolved_roots()

    def is_path_allowed(self, target_path: str | Path) -> bool:
        """Check if target path is within configured allowed directories."""
        try:
            resolved = Path(target_path).resolve()
            for allowed in self.allowed_roots:
                try:
                    resolved.relative_to(allowed)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    async def evaluate_and_execute(
        self,
        tool_def: ToolDefinition,
        params: Dict[str, Any],
        confirm_callback: Optional[Callable[[str], Coroutine[Any, Any, bool]]] = None,
    ) -> ToolResult:
        """Evaluate tool safety, handle confirmations, and execute safely."""
        risk = tool_def.risk.lower()
        tool_name = tool_def.name
        clean_params = normalize_tool_params(tool_def, params)

        # 1. Check dry_run mode
        if self.dry_run:
            logger.info(f"[DRY RUN] Would execute tool '{tool_name}' with params: {clean_params}")
            return ToolResult(
                ok=True,
                message=f"[Dry Run] I would execute {tool_name} with {clean_params}.",
                data={"dry_run": True, "tool": tool_name, "params": clean_params},
            )

        # 2. File path restriction verification
        if tool_name in ["open_folder", "find_file"]:
            path_arg = params.get("path") or params.get("directory")
            if path_arg and not self.is_path_allowed(path_arg):
                logger.warning(f"Blocked access to unapproved path: {path_arg}")
                return ToolResult(
                    ok=False,
                    message=f"Access to '{path_arg}' is not permitted by security rules.",
                    data={"blocked": True, "path": str(path_arg)},
                )

        # 3. High risk confirmation check
        if risk == "high" and self.config.safety.confirm_high_risk:
            prompt = f"Are you sure you want to execute {tool_name.replace('_', ' ')}?"
            logger.info(f"High risk tool {tool_name} requires confirmation. Prompt: {prompt}")

            confirmed = False
            if confirm_callback:
                confirmed = await confirm_callback(prompt)
            else:
                # If no confirmation callback provided, block high risk by default
                logger.warning(f"No confirmation handler available for high risk {tool_name}. Denying.")
                return ToolResult(
                    ok=False,
                    message=f"Action '{tool_name}' cancelled because confirmation was not received.",
                    data={"cancelled": True},
                )

            if not confirmed:
                logger.info(f"Execution of {tool_name} was denied by user.")
                return ToolResult(
                    ok=False,
                    message=f"Action '{tool_name}' cancelled.",
                    data={"cancelled": True},
                )

        # 4. Medium risk announcement
        if risk == "medium":
            logger.info(f"[Medium Risk] Executing {tool_name} with params {params}")

        # 5. Execute via tool definition (use normalized params, not raw)
        try:
            import inspect
            if inspect.iscoroutinefunction(tool_def.func):
                result = await tool_def.func(**clean_params)
            else:
                import asyncio
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: tool_def.func(**clean_params))

            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, str):
                return ToolResult(ok=True, message=result)
            elif isinstance(result, tuple) and len(result) == 2:
                return ToolResult(ok=bool(result[0]), message=str(result[1]))
            else:
                return ToolResult(ok=True, message="Action completed.", data={"raw": result})

        except Exception as e:
            logger.exception(f"Exception during tool {tool_name} execution: {e}")
            return ToolResult(
                ok=False,
                message=f"Failed to execute {tool_name}: {str(e)}",
                data={"error": str(e)},
            )
