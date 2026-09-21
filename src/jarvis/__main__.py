"""Main CLI entrypoint for Deskter."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from jarvis import __version__
from jarvis.actions.registry import registry
from jarvis.audio.player import AudioPlayer
from jarvis.brain.llm import ensure_ollama_running
from jarvis.brain.router import Router
from jarvis.config import Config, load_config
from jarvis.core.events import EventBus
from jarvis.safety.gate import SafetyGate


def setup_logging(config: Config) -> None:
    """Initialize structured logging."""
    log_file = Path(config.logging.file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, config.logging.level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_file), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


async def run_text_cli(config: Config, gate: SafetyGate, bus: EventBus, enable_voice: bool = True) -> None:
    """Run interactive text CLI powered by the Deskter Brain router and speech output."""
    router = Router(config=config, gate=gate, bus=bus)
    player = AudioPlayer(config=config, bus=bus) if enable_voice else None

    print("=" * 60)
    print(f"DESKTER Voice & Text Console v{__version__}")
    print(f"Voice Output: {'[ENABLED]' if enable_voice else '[DISABLED]'}")
    print(f"Type commands directly (e.g., 'open notepad', 'volume 50', 'time').")
    print(f"Type 'tools' to list actions, 'clear' to reset memory, 'exit' to quit.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n[You] > ").strip()
            if not user_input:
                continue

            # Immediate barge-in: stop any active speech as soon as user enters new input
            if player and player.is_speaking:
                player.stop()

            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                if player:
                    player.speak("Goodbye!", blocking=True)
                break

            if user_input.lower() == "tools":
                print("\nRegistered Tools:")
                for t in registry.list_tools():
                    print(f"  - {t.name:20} [{t.risk:6}] {t.description}")
                continue

            if user_input.lower() == "clear":
                router.memory.clear()
                print("[Deskter] Conversation memory cleared.")
                if player:
                    player.speak("Conversation memory cleared.")
                continue

            # Route through Deskter Brain (Fast path rules -> LLM with tools -> Safety Gate)
            resp = await router.route_and_execute(user_input)
            print(f"[{config.assistant.name}] {resp.reply}")

            # Stream spoken response
            if player and resp.reply:
                player.speak(resp.reply)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            if player:
                player.stop()
            break
        except Exception as e:
            print(f"[Error] {e}")


def main() -> None:
    """CLI parser and startup coordinator."""
    parser = argparse.ArgumentParser(
        description="DESKTER: Offline Desktop Voice Assistant & AI Dashboard"
    )
    parser.add_argument("--config", type=str, default=None, help="Path to custom config.yaml")
    parser.add_argument("--text", action="store_true", help="Run in interactive text console mode")
    parser.add_argument("--dry-run", action="store_true", help="Log actions without executing them")
    parser.add_argument("--no-voice", action="store_true", help="Disable TTS speech audio output")
    parser.add_argument("--list-tools", action="store_true", help="Print all registered tools and exit")
    parser.add_argument("--refresh-apps", action="store_true", help="Scan and rebuild the app index")
    parser.add_argument("--run-agent-tests", action="store_true", help="Run autonomous AI testing agent and generate report")
    parser.add_argument("--continuous-test", type=int, nargs="?", const=30, default=None, help="Run AI testing agent continuously every N seconds (default 30s)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    if args.dry_run:
        config.assistant.dry_run = True

    setup_logging(config)

    # Initialize Actions
    import jarvis.actions  # registers all tools

    if args.list_tools:
        print("Registered Tools:")
        for t in registry.list_tools():
            print(f"  - {t.name:20} [{t.risk:6}] {t.description}")
        return

    if args.refresh_apps:
        from jarvis.actions.apps import get_indexer
        indexer = get_indexer()
        indexer.rebuild_index()
        print(f"Successfully indexed {len(indexer.index)} applications.")
        return

    if args.run_agent_tests:
        from jarvis.testing.agent import TestingAgent
        agent = TestingAgent(config)
        print("Running Deskter Autonomous AI Testing Agent...")
        report = asyncio.run(agent.run_all_tests())
        print("\n" + report.to_markdown())
        return

    if args.continuous_test is not None:
        from jarvis.testing.agent import TestingAgent
        agent = TestingAgent(config)
        asyncio.run(agent.run_continuous(interval_seconds=args.continuous_test))
        return

    gate = SafetyGate(config)
    bus = EventBus()
    enable_voice = not args.no_voice

    # Ensure Ollama LLM server daemon is running
    if config.llm.auto_start:
        print("[Deskter] Verifying Ollama LLM server daemon...")
        if ensure_ollama_running(config.llm):
            print(f"[Deskter] Ollama LLM is online ({config.llm.model} at {config.llm.host}).")
        else:
            print(f"[Deskter Warning] Could not start Ollama server at {config.llm.host}.")

    if args.text or not sys.stdin.isatty():
        asyncio.run(run_text_cli(config, gate, bus, enable_voice=enable_voice))
    else:
        # Default: start text CLI in Brain Mode
        print(f"Starting {config.assistant.name} in interactive text console (Phase 3 Voice & Brain)...")
        asyncio.run(run_text_cli(config, gate, bus, enable_voice=enable_voice))


if __name__ == "__main__":
    main()
