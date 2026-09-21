"""Ollama LLM client with structured tool calling and JSON fallback."""

import json
import logging
import os
import re
import shutil
import subprocess
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import ollama

from jarvis.config import LlmConfig

logger = logging.getLogger("jarvis.brain.llm")


def find_ollama_executable() -> Optional[Path]:
    """Find the path to the Ollama executable across standard installation locations."""
    # 1. PATH lookup
    exe = shutil.which("ollama") or shutil.which("ollama.exe")
    if exe:
        return Path(exe)

    # 2. Windows standard installation locations
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        candidate = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
        if candidate.is_file():
            return candidate

    program_files = os.environ.get("ProgramFiles", "")
    if program_files:
        candidate = Path(program_files) / "Ollama" / "ollama.exe"
        if candidate.is_file():
            return candidate

    home = Path.home()
    candidate = home / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"
    if candidate.is_file():
        return candidate

    # 3. Unix standard installation locations
    for p in ["/usr/local/bin/ollama", "/usr/bin/ollama", "/opt/ollama/bin/ollama"]:
        cand = Path(p)
        if cand.is_file():
            return cand

    return None


def is_ollama_running(host: str = "http://localhost:11434", timeout_s: float = 1.5) -> bool:
    """Check if the Ollama HTTP API server is responsive."""
    url = f"{host.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Deskter/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            return response.status == 200
    except Exception:
        return False


def start_ollama_daemon(host: str = "http://localhost:11434", timeout_s: float = 10.0) -> bool:
    """Start Ollama server daemon in the background without creating a visible console window."""
    if is_ollama_running(host, timeout_s=1.0):
        logger.info(f"Ollama daemon is already running at {host}")
        return True

    exe = find_ollama_executable()
    if not exe:
        logger.warning(
            "Ollama executable not found in PATH or standard installation locations. "
            "Please ensure Ollama is installed (https://ollama.com) or start it manually."
        )
        return False

    logger.info(f"Launching Ollama daemon from {exe}...")
    try:
        creation_flags = 0
        if os.name == "nt":
            # Detach and hide console window on Windows
            CREATE_NO_WINDOW = 0x08000000
            DETACHED_PROCESS = 0x00000008
            creation_flags = CREATE_NO_WINDOW | DETACHED_PROCESS

        subprocess.Popen(
            [str(exe), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=creation_flags,
            close_fds=True if os.name != "nt" else False,
        )

        # Wait for server to become responsive
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout_s:
            if is_ollama_running(host, timeout_s=0.5):
                logger.info(f"Ollama daemon successfully started and responding at {host}")
                return True
            time.sleep(0.5)

        logger.warning(f"Ollama daemon spawned, but did not respond within {timeout_s}s.")
        return False
    except Exception as e:
        logger.error(f"Failed to launch Ollama daemon: {e}")
        return False


def ensure_ollama_running(config: LlmConfig, timeout_s: float = 10.0) -> bool:
    """Ensure Ollama server is running if auto_start is enabled in config."""
    if not config.auto_start:
        return is_ollama_running(config.host)

    if is_ollama_running(config.host):
        return True

    return start_ollama_daemon(config.host, timeout_s=timeout_s)


@dataclass
class ToolCall:
    """Structured representation of an LLM tool call request."""
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None


@dataclass
class LlmResponse:
    """Structured response from LLM inference."""
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LlmClient:
    """Asynchronous client for local Ollama LLM execution."""

    def __init__(self, config: LlmConfig) -> None:
        self.config = config
        self.client = ollama.AsyncClient(host=config.host)
        if config.auto_start:
            ensure_ollama_running(config)

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LlmResponse:
        """Send chat messages and optional tool schemas to Ollama."""
        options = {
            "temperature": self.config.temperature,
        }

        try:
            kwargs: Dict[str, Any] = {
                "model": self.config.model,
                "messages": messages,
                "options": options,
                "keep_alive": self.config.keep_alive,
            }
            if tools:
                kwargs["tools"] = tools

            logger.debug(f"Sending prompt to Ollama ({self.config.model}): {len(messages)} messages, {len(tools or [])} tools")
            resp = await self.client.chat(**kwargs)

            message = getattr(resp, "message", None)
            if not message and isinstance(resp, dict):
                message = resp.get("message", {})

            content = getattr(message, "content", "") or ""
            raw_tool_calls = getattr(message, "tool_calls", None)

            if raw_tool_calls is None and isinstance(message, dict):
                raw_tool_calls = message.get("tool_calls")

            parsed_tool_calls: List[ToolCall] = []

            # 1. Native Ollama Tool Calls
            if raw_tool_calls:
                for tc in raw_tool_calls:
                    fn = getattr(tc, "function", None)
                    if fn is None and isinstance(tc, dict):
                        fn = tc.get("function", {})
                    
                    name = getattr(fn, "name", None) or (fn.get("name") if isinstance(fn, dict) else "")
                    args = getattr(fn, "arguments", None) or (fn.get("arguments") if isinstance(fn, dict) else {})
                    
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            args = {}

                    if name:
                        parsed_tool_calls.append(ToolCall(name=name, arguments=args or {}))

            # 2. JSON Fallback Parsing (if model returned JSON text instead of native tool call)
            if not parsed_tool_calls and content:
                extracted = self._extract_json_tool_calls(content)
                if extracted:
                    parsed_tool_calls.extend(extracted)
                    # Clean up content if it was purely a JSON tool payload
                    if content.strip().startswith("{") or content.strip().startswith("["):
                        content = ""

            return LlmResponse(
                content=content.strip(),
                tool_calls=parsed_tool_calls,
                raw=resp if isinstance(resp, dict) else getattr(resp, "__dict__", None),
            )

        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return LlmResponse(
                content="I can't reach my language model.",
                tool_calls=[],
                error=str(e),
            )

    def _extract_json_tool_calls(self, text: str) -> List[ToolCall]:
        """Attempt to extract tool invocations from formatted JSON text."""
        tool_calls: List[ToolCall] = []
        text = text.strip()

        # Try parsing whole string as JSON
        json_objs = []
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                parsed = json.loads(text)
                json_objs = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                pass

        # Try markdown code blocks: ```json ... ```
        if not json_objs:
            matches = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
            for m in matches:
                try:
                    parsed = json.loads(m.strip())
                    if isinstance(parsed, list):
                        json_objs.extend(parsed)
                    elif isinstance(parsed, dict):
                        json_objs.append(parsed)
                except Exception:
                    continue

        # Try pseudo-execution text pattern: "I would execute <tool> with {<args>}" or "Dry Run I would execute <tool> with <args>"
        if not tool_calls:
            matches = re.findall(
                r"(?:\[?Dry Run\]?\s+)?(?:I would execute|execute)\s+([a-zA-Z0-9_-]+)(?:\s+with\s+(\{.*?\}))?",
                text,
                re.IGNORECASE,
            )
            for tool_name, raw_args in matches:
                parsed_args = {}
                if raw_args:
                    try:
                        # Handle python-style dict or json
                        raw_args_clean = raw_args.replace("'", '"')
                        parsed_args = json.loads(raw_args_clean)
                    except Exception:
                        pass
                tool_calls.append(ToolCall(name=tool_name, arguments=parsed_args))

        for obj in json_objs:
            if not isinstance(obj, dict):
                continue
            name = obj.get("tool") or obj.get("name") or obj.get("function")
            args = obj.get("args") or obj.get("arguments") or obj.get("parameters") or {}
            if name and isinstance(name, str):
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                tool_calls.append(ToolCall(name=name, arguments=args))

        return tool_calls

