"""Router coordinating cognitive LLM intent reasoning, tool calling, and execution."""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.actions.registry import ToolResult, registry
from jarvis.brain.llm import LlmClient, ToolCall
from jarvis.brain.memory import ConversationMemory
from jarvis.brain.prompts import build_system_prompt
from jarvis.brain.rules import RuleMatcher
from jarvis.config import Config
from jarvis.core.events import EventBus, ToolCallEvent, ToolResultEvent
from jarvis.safety.gate import SafetyGate

logger = logging.getLogger("jarvis.brain.router")

EMERGENCY_STOP_KEYWORDS = {"stop", "cancel", "abort", "quiet", "silence", "shut up"}


@dataclass
class RouterResponse:
    """Consolidated outcome of intent resolution and action execution."""
    reply: str
    fast_path: bool = False
    tool_results: List[ToolResult] = field(default_factory=list)
    error: Optional[str] = None


class Router:
    """Orchestrates cognitive LLM intent reasoning, tool selection, and execution."""

    def __init__(
        self,
        config: Config,
        gate: SafetyGate,
        bus: Optional[EventBus] = None,
        llm_client: Optional[LlmClient] = None,
        memory: Optional[ConversationMemory] = None,
    ) -> None:
        self.config = config
        self.gate = gate
        self.bus = bus or EventBus()
        self.rules = RuleMatcher()
        self.llm = llm_client or LlmClient(config.llm)
        self.memory = memory or ConversationMemory()
        self.system_prompt = build_system_prompt(assistant_name=config.assistant.name)
        self.routing_mode = getattr(config.llm, "routing_mode", "llm_first").lower()

    async def route_and_execute(self, user_text: str) -> RouterResponse:
        """Route user input through cognitive LLM reasoning or rules and execute actions."""
        text = user_text.strip()
        if not text:
            return RouterResponse(reply="", fast_path=True)

        logger.info(f"Processing input: '{text}' (mode: {self.routing_mode})")

        # 1. Emergency interrupt check (always fast-path if user says "stop" or "cancel")
        clean_text = re.sub(r"[^\w\s]", "", text.lower()).strip()
        if clean_text in EMERGENCY_STOP_KEYWORDS:
            logger.info(f"Emergency stop requested: '{clean_text}'")
            self.memory.add_user_message(text)
            reply = "Stopping current action."
            self.memory.add_assistant_message(content=reply)
            return RouterResponse(reply=reply, fast_path=True)

        # 2. If routing_mode is "rules_first", evaluate hardcoded fast-path rules first
        if self.routing_mode == "rules_first":
            match = self.rules.match(text)
            if match.matched:
                logger.info(f"Fast path rule match: tool={match.tool_name}, direct_reply={match.direct_reply}")
                if match.direct_reply:
                    self.memory.add_user_message(text)
                    self.memory.add_assistant_message(content=match.direct_reply)
                    return RouterResponse(reply=match.direct_reply, fast_path=True)

                if match.tool_name:
                    tool_def = registry.get_tool(match.tool_name)
                    if tool_def:
                        self.memory.add_user_message(text)
                        await self.bus.publish(ToolCallEvent(tool_name=match.tool_name, params=match.params))
                        result = await self.gate.evaluate_and_execute(tool_def, match.params)
                        await self.bus.publish(ToolResultEvent(tool_name=match.tool_name, ok=result.ok, message=result.message))
                        self.memory.add_assistant_message(
                            content=result.message,
                            tool_calls=[{"function": {"name": match.tool_name, "arguments": match.params}}],
                        )
                        return RouterResponse(
                            reply=result.message,
                            fast_path=True,
                            tool_results=[result],
                        )

        # 3. Cognitive Agent Path (Default 'llm_first' or 'llm_only'):
        # Ollama LLM analyzes natural language, extracts intent, selects tools or answers directly.
        logger.info("Routing to Cognitive Ollama LLM...")
        self.memory.add_user_message(text)
        messages = self.memory.get_messages(system_prompt=self.system_prompt)
        tools = registry.get_ollama_tools()

        llm_resp = await self.llm.chat(messages=messages, tools=tools)

        if llm_resp.error:
            # If LLM is unreachable and we are in llm_first, fallback to rules matcher
            if self.routing_mode == "llm_first":
                logger.warning("Ollama LLM unreachable, attempting rule matcher fallback...")
                match = self.rules.match(text)
                if match.matched and match.tool_name:
                    tool_def = registry.get_tool(match.tool_name)
                    if tool_def:
                        await self.bus.publish(ToolCallEvent(tool_name=match.tool_name, params=match.params))
                        result = await self.gate.evaluate_and_execute(tool_def, match.params)
                        await self.bus.publish(ToolResultEvent(tool_name=match.tool_name, ok=result.ok, message=result.message))
                        self.memory.add_assistant_message(
                            content=result.message,
                            tool_calls=[{"function": {"name": match.tool_name, "arguments": match.params}}],
                        )
                        return RouterResponse(
                            reply=result.message,
                            fast_path=True,
                            tool_results=[result],
                        )

            reply = llm_resp.content or "I am having trouble reaching my language model right now."
            return RouterResponse(reply=reply, fast_path=False, error=llm_resp.error)

        # Case A: LLM identified one or more tools to call
        if llm_resp.tool_calls:
            results: List[ToolResult] = []
            executed_calls: List[Dict[str, Any]] = []

            for tc in llm_resp.tool_calls:
                tool_def = registry.get_tool(tc.name)
                if not tool_def:
                    logger.warning(f"LLM requested unknown tool: {tc.name}")
                    continue

                logger.info(f"Executing LLM tool: {tc.name} with params {tc.arguments}")
                await self.bus.publish(ToolCallEvent(tool_name=tc.name, params=tc.arguments))
                res = await self.gate.evaluate_and_execute(tool_def, tc.arguments)
                await self.bus.publish(ToolResultEvent(tool_name=tc.name, ok=res.ok, message=res.message))

                results.append(res)
                executed_calls.append({"function": {"name": tc.name, "arguments": tc.arguments}})
                self.memory.add_tool_result(tool_name=tc.name, result_content=res.message)

            # Synthesize reply from executed tool messages
            messages_combined = " ".join(r.message for r in results if r.message).strip()
            if not messages_combined:
                messages_combined = "Action completed."

            # Clean memory of dry-run meta prefixes to preserve natural dialogue context
            clean_memory_content = re.sub(r"^\[Dry Run\]\s+I would execute \w+ with \{.*?\}[.\s]*", "Action executed. ", messages_combined).strip()
            if not clean_memory_content:
                clean_memory_content = messages_combined

            self.memory.add_assistant_message(
                content=clean_memory_content,
            )
            return RouterResponse(
                reply=messages_combined,
                fast_path=False,
                tool_results=results,
            )

        # Case B: Pure Chat / General Question / Direct Answer
        reply = llm_resp.content.strip()
        if not reply:
            reply = "I didn't catch what you would like me to do."

        # Clean speech of any stray markdown symbols for smooth audio synthesis
        clean_spoken_reply = re.sub(r"[*_#`~\[\]]", "", reply).strip()
        self.memory.add_assistant_message(content=clean_spoken_reply)
        return RouterResponse(reply=clean_spoken_reply, fast_path=False)

