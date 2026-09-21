"""Rolling conversation memory with inactivity expiration."""

import time
from typing import Any, Dict, List, Optional


class ConversationMemory:
    """Manages short-term rolling conversation history."""

    def __init__(self, max_turns: int = 6, inactivity_timeout_s: float = 300.0) -> None:
        """Initialize memory.
        
        Args:
            max_turns: Maximum number of dialogue turns (user + assistant pairs) to keep.
            inactivity_timeout_s: Inactivity timeout in seconds before clearing history.
        """
        self.max_turns = max_turns
        self.inactivity_timeout_s = inactivity_timeout_s
        self._messages: List[Dict[str, Any]] = []
        self._last_interaction_time: float = time.time()

    def _check_and_expire(self) -> None:
        """Clear messages if inactivity timeout has elapsed."""
        now = time.time()
        if self._messages and (now - self._last_interaction_time > self.inactivity_timeout_s):
            self._messages.clear()
        self._last_interaction_time = now

    def add_user_message(self, content: str) -> None:
        """Append a user message to history."""
        self._check_and_expire()
        self._messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Append an assistant response or tool call to history."""
        self._check_and_expire()
        msg: Dict[str, Any] = {"role": "assistant", "content": content or ""}
        if tool_calls:
            formatted_calls: List[Dict[str, Any]] = []
            for tc in tool_calls:
                if "function" in tc:
                    formatted_calls.append(tc)
                elif "name" in tc:
                    formatted_calls.append({
                        "function": {
                            "name": tc["name"],
                            "arguments": tc.get("args") or tc.get("arguments") or {},
                        }
                    })
                else:
                    formatted_calls.append(tc)
            msg["tool_calls"] = formatted_calls
        self._messages.append(msg)
        self._trim()

    def add_tool_result(
        self,
        tool_name: str,
        result_content: str,
        tool_call_id: Optional[str] = None,
    ) -> None:
        """Append tool execution output to history."""
        self._check_and_expire()
        msg: Dict[str, Any] = {
            "role": "tool",
            "name": tool_name,
            "content": str(result_content),
        }
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        self._messages.append(msg)
        self._trim()

    def _trim(self) -> None:
        """Keep only the latest turns."""
        max_messages = self.max_turns * 3  # Allow for user + assistant + tool triplets
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]

    def get_messages(self, system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return formatted message list ready for Ollama / chat LLMs."""
        self._check_and_expire()
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(list(self._messages))
        return messages

    def clear(self) -> None:
        """Reset conversation memory."""
        self._messages.clear()
        self._last_interaction_time = time.time()

    @property
    def message_count(self) -> int:
        """Return number of currently active messages in memory."""
        self._check_and_expire()
        return len(self._messages)
