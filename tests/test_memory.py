"""Unit tests for ConversationMemory."""

import time
import pytest
from jarvis.brain.memory import ConversationMemory


def test_conversation_memory_add_and_retrieve() -> None:
    memory = ConversationMemory(max_turns=3, inactivity_timeout_s=10.0)
    memory.add_user_message("Hello Deskter")
    memory.add_assistant_message("Hello! How can I help you today?")

    messages = memory.get_messages(system_prompt="System instructions")
    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"


def test_conversation_memory_trimming() -> None:
    memory = ConversationMemory(max_turns=2, inactivity_timeout_s=60.0)

    for i in range(5):
        memory.add_user_message(f"User message {i}")
        memory.add_assistant_message(f"Assistant reply {i}")

    messages = memory.get_messages()
    # 2 turns * 3 = 6 max items retained
    assert len(messages) <= 6
    assert "User message 4" in messages[-2]["content"]
    assert "Assistant reply 4" in messages[-1]["content"]


def test_conversation_memory_inactivity_expiration() -> None:
    memory = ConversationMemory(max_turns=3, inactivity_timeout_s=0.05)
    memory.add_user_message("Remember this")
    assert memory.message_count == 1

    time.sleep(0.08)

    # Accessing after timeout should expire messages
    assert memory.message_count == 0
    assert len(memory.get_messages()) == 0


def test_conversation_memory_clear() -> None:
    memory = ConversationMemory()
    memory.add_user_message("Test message")
    assert memory.message_count == 1

    memory.clear()
    assert memory.message_count == 0
