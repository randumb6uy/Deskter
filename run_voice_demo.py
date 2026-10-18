"""Run Deskter with real-time TTS voice output across multiple cognitive and system queries."""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src/ to path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import jarvis.actions  # registers all 39 tools
from jarvis.audio.player import AudioPlayer
from jarvis.brain.llm import ensure_ollama_running
from jarvis.brain.router import Router
from jarvis.config import load_config
from jarvis.core.events import EventBus
from jarvis.safety.gate import SafetyGate

VOICE_QUERIES = [
    {
        "intent": "Time Query",
        "input": "what time is it right now",
    },
    {
        "intent": "Hardware Diagnostics",
        "input": "check battery percentage",
    },
    {
        "intent": "Google Antigravity Telemetry",
        "input": "how much token usage in antigravity",
    },
    {
        "intent": "AI Cognitive Reasoning",
        "input": "give me a one-sentence motivational tip for a software developer",
    },
]


async def main() -> None:
    config = load_config()
    print("=" * 65)
    print(f"DESKTER VOICE MODE DEMONSTRATION")
    print(f"Assistant : {config.assistant.name}")
    print(f"Local LLM : {config.llm.model} (GPU Accelerated)")
    print(f"Audio TTS : {config.tts.fallback} (Windows SAPI5 Native Speech)")
    print("=" * 65)

    # 1. Ensure Ollama daemon is ready
    print("\n[Voice Demo] Ensuring Ollama LLM server is active...")
    if not ensure_ollama_running(config.llm):
        print("[Voice Demo] Warning: Could not connect to Ollama.")

    # 2. Initialize Core Subsystems
    gate = SafetyGate(config)
    bus = EventBus()
    router = Router(config=config, gate=gate, bus=bus)
    player = AudioPlayer(config=config, bus=bus)

    # Startup Voice Announcement
    welcome_text = "Deskter voice mode is online. Initializing demonstration queries."
    print(f"\n[Deskter Speaking] {welcome_text}")
    player.speak(welcome_text, blocking=True)
    await asyncio.sleep(0.4)

    # 3. Execute Voice Pipeline
    for i, item in enumerate(VOICE_QUERIES, 1):
        print(f"\n-----------------------------------------------------------------")
        print(f"Turn #{i}: [{item['intent']}]")
        print(f"You Said > \"{item['input']}\"")

        t0 = time.time()
        resp = await router.route_and_execute(item["input"])
        latency_ms = (time.time() - t0) * 1000

        route = "Fast-Path Rules" if resp.fast_path else f"Cognitive LLM ({config.llm.model})"
        print(f"Routing  > {route} ({latency_ms:.1f}ms)")
        print(f"Deskter  > \"{resp.reply}\"")
        print(f"Speaking > Outputting audio through system speakers...")

        if resp.reply:
            player.speak(resp.reply, blocking=True)

        await asyncio.sleep(0.5)

    conclusion = "All demonstration turns completed successfully. Deskter is standing by."
    print(f"\n[Deskter Speaking] {conclusion}")
    player.speak(conclusion, blocking=True)

    print("\n" + "=" * 65)
    print("Voice mode demonstration complete.")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
