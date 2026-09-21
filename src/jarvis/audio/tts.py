"""Text-to-speech engine abstraction with SAPI5 and Piper neural TTS support."""

import abc
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from jarvis.actions.com_utils import COMContext
from jarvis.config import Config, TtsConfig

logger = logging.getLogger("jarvis.audio.tts")


class BaseTTSEngine(abc.ABC):
    """Abstract interface for offline text-to-speech synthesis."""

    @abc.abstractmethod
    def synthesize_to_file(self, text: str, output_wav_path: str) -> bool:
        """Synthesize text directly into a target WAV audio file."""
        pass

    @abc.abstractmethod
    def speak_direct(self, text: str) -> bool:
        """Speak text directly to default audio output device."""
        pass


class SapiTTSEngine(BaseTTSEngine):
    """Windows Native SAPI5 engine (via pyttsx3) for zero extra RAM and instant speech."""

    def __init__(self, voice: Optional[str] = None, rate_wpm: int = 180) -> None:
        self.voice = voice
        self.rate_wpm = rate_wpm

    def _get_configured_engine(self) -> Any:
        """Instantiate pyttsx3 within COM context."""
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate_wpm)
        if self.voice:
            voices = engine.getProperty("voices")
            for v in voices:
                if self.voice.lower() in v.name.lower() or self.voice.lower() in getattr(v, "id", "").lower():
                    engine.setProperty("voice", v.id)
                    break
        return engine

    def synthesize_to_file(self, text: str, output_wav_path: str) -> bool:
        """Save SAPI speech to WAV file."""
        with COMContext():
            try:
                engine = self._get_configured_engine()
                engine.save_to_file(text, output_wav_path)
                engine.runAndWait()
                return Path(output_wav_path).exists()
            except Exception as e:
                logger.error(f"SAPI save_to_file failed: {e}")
                return False

    def speak_direct(self, text: str) -> bool:
        """Speak text directly using Windows SAPI."""
        with COMContext():
            try:
                engine = self._get_configured_engine()
                engine.say(text)
                engine.runAndWait()
                return True
            except Exception as e:
                logger.error(f"SAPI direct speak failed: {e}")
                return False


class PiperTTSEngine(BaseTTSEngine):
    """High-fidelity local neural TTS using Piper (ONNX int8 quantized)."""

    def __init__(
        self,
        voice_model: str = "en_US-lessac-medium",
        models_dir: str = "models/piper",
        fallback_engine: Optional[BaseTTSEngine] = None,
    ) -> None:
        self.voice_model = voice_model
        self.models_dir = Path(models_dir)
        self.fallback = fallback_engine or SapiTTSEngine()
        self._piper_binary = shutil.which("piper") or shutil.which("piper.exe")

    def _get_model_paths(self) -> tuple[Optional[Path], Optional[Path]]:
        """Return (onnx_path, json_config_path) if downloaded."""
        onnx_file = self.models_dir / f"{self.voice_model}.onnx"
        json_file = self.models_dir / f"{self.voice_model}.onnx.json"
        if onnx_file.exists() and json_file.exists():
            return onnx_file, json_file
        return None, None

    def synthesize_to_file(self, text: str, output_wav_path: str) -> bool:
        """Synthesize neural speech to WAV via Piper with fallback."""
        onnx_path, json_path = self._get_model_paths()

        if self._piper_binary and onnx_path:
            try:
                cmd = [
                    self._piper_binary,
                    "--model", str(onnx_path),
                    "--config", str(json_path),
                    "--output_file", str(output_wav_path),
                ]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                proc.communicate(input=text.encode("utf-8"), timeout=10)
                if proc.returncode == 0 and Path(output_wav_path).exists():
                    return True
            except Exception as e:
                logger.warning(f"Piper binary execution failed: {e}. Falling back to SAPI.")

        # Fallback to SAPI5 if Piper model or binary is not present
        return self.fallback.synthesize_to_file(text, output_wav_path)

    def speak_direct(self, text: str) -> bool:
        """Direct speak via fallback or synthesis."""
        return self.fallback.speak_direct(text)


def get_tts_engine(config: Config) -> BaseTTSEngine:
    """Factory creating the configured TTS engine with automatic fallback."""
    cfg = config.tts
    sapi_fallback = SapiTTSEngine(voice=cfg.voice, rate_wpm=int(180 * cfg.speed))

    if cfg.engine.lower() == "piper":
        return PiperTTSEngine(
            voice_model=cfg.voice,
            fallback_engine=sapi_fallback,
        )

    return sapi_fallback
