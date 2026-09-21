"""Configuration loader and Pydantic validation models for Jarvis."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class AssistantConfig(BaseModel):
    """General assistant behavior settings."""
    name: str = "Deskter"
    dry_run: bool = False


class DashboardConfig(BaseModel):
    """Deskter CustomTkinter UI dashboard settings."""
    enabled: bool = True
    title: str = "Deskter - AI Assistant Dashboard"
    theme: str = "dark-blue"
    host: str = "127.0.0.1"
    port: int = 8766


class AudioConfig(BaseModel):
    """Audio input/output hardware settings."""
    input_device: Optional[int] = None
    output_device: Optional[int] = None
    sample_rate: int = 16000


class WakeWordConfig(BaseModel):
    """Wake word and push-to-talk hotkey settings."""
    phrase: str = "hey_jarvis"
    threshold: float = 0.5
    hotkey: str = "<ctrl>+<alt>+<space>"


class VadConfig(BaseModel):
    """Voice Activity Detection parameters."""
    silence_ms: int = 800
    max_record_s: int = 15


class SttConfig(BaseModel):
    """Speech-to-text inference settings."""
    engine: str = "faster-whisper"
    model: str = "small.en"
    device: str = "cpu"
    compute_type: str = "int8"


class LlmConfig(BaseModel):
    """Local LLM runtime configuration."""
    provider: str = "ollama"
    host: str = "http://localhost:11434"
    model: str = "qwen2.5:3b"
    temperature: float = 0.3
    keep_alive: str = "30m"
    timeout_s: int = 30
    auto_start: bool = True
    routing_mode: str = "llm_first"  # Options: "llm_first", "rules_first", "llm_only"



class TtsConfig(BaseModel):
    """Text-to-speech engine and voice settings."""
    engine: str = "piper"
    voice: str = "en_US-lessac-medium"
    fallback: str = "pyttsx3"
    speed: float = 1.0


class AppsConfig(BaseModel):
    """Installed applications discovery and manual aliases."""
    aliases: Dict[str, str] = Field(default_factory=dict)


class FilesConfig(BaseModel):
    """Allowed roots for file search and folder opening."""
    allowed_roots: List[str] = Field(
        default_factory=lambda: ["~/Documents", "~/Downloads", "~/Desktop"]
    )

    def get_resolved_roots(self) -> List[Path]:
        """Return expanded absolute paths for allowed roots."""
        return [Path(os.path.expanduser(p)).resolve() for p in self.allowed_roots]


class BrowserConfig(BaseModel):
    """Browser launch and tab bridge parameters."""
    bridge_host: str = "127.0.0.1"
    bridge_port: int = 8765
    request_timeout_s: int = 5
    blocked_domains: List[str] = Field(
        default_factory=lambda: [
            "accounts.google.com",
            "*.bank*",
            "*bitwarden*",
            "*1password*",
            "*lastpass*",
        ]
    )


class SafetyConfig(BaseModel):
    """Action safety levels and confirmation timeouts."""
    confirm_high_risk: bool = True
    confirm_timeout_s: int = 8


class LoggingConfig(BaseModel):
    """Logging level and output file destination."""
    level: str = "INFO"
    file: str = "logs/deskter.log"


class Config(BaseModel):
    """Root configuration object for Jarvis."""
    assistant: AssistantConfig = Field(default_factory=AssistantConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    wakeword: WakeWordConfig = Field(default_factory=WakeWordConfig)
    vad: VadConfig = Field(default_factory=VadConfig)
    stt: SttConfig = Field(default_factory=SttConfig)
    llm: LlmConfig = Field(default_factory=LlmConfig)
    tts: TtsConfig = Field(default_factory=TtsConfig)
    apps: AppsConfig = Field(default_factory=AppsConfig)
    files: FilesConfig = Field(default_factory=FilesConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Optional[str | Path] = None) -> Config:
    """Load and validate config from YAML file or return defaults."""
    if config_path is None:
        # Default locations to search: current directory config.yaml or project root
        potential_paths = [
            Path("config.yaml"),
            Path(__file__).parent.parent.parent / "config.yaml",
        ]
        for p in potential_paths:
            if p.exists():
                config_path = p
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}
            return Config(**raw_data)

    return Config()
