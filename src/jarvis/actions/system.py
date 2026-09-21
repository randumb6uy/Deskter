"""System hardware control tools: volume, brightness, battery, screenshot, lock, power."""

import ctypes
import datetime
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, Union
import psutil
from PIL import ImageGrab

from jarvis.actions.com_utils import COMContext
from jarvis.actions.registry import ToolResult, tool

logger = logging.getLogger("jarvis.actions.system")


@tool(
    name="set_volume",
    description="Adjust the system audio volume (e.g. '50', 'up', 'down', 'mute', 'max').",
    params={"level": {"type": "string", "description": "Volume level: 0-100 integer, 'up', 'down', 'mute', 'unmute', or 'max'"}},
    risk="low",
)
def set_volume(level: Union[int, str]) -> ToolResult:
    """Adjust system master volume."""
    with COMContext():
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL

            devices = AudioUtilities.GetSpeakers()
            if hasattr(devices, "EndpointVolume"):
                volume = devices.EndpointVolume
            else:
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))

            current = volume.GetMasterVolumeLevelScalar()
            current_pct = int(round(current * 100))

            level_str = str(level).lower().strip()

            if level_str == "up":
                new_pct = min(100, current_pct + 10)
            elif level_str == "down":
                new_pct = max(0, current_pct - 10)
            elif level_str in ["mute", "silence"]:
                volume.SetMute(1, None)
                return ToolResult(ok=True, message="Muted audio.")
            elif level_str == "unmute":
                volume.SetMute(0, None)
                return ToolResult(ok=True, message="Unmuted audio.")
            elif level_str in ["max", "maximum", "full"]:
                new_pct = 100
            else:
                # Try parsing integer percentage
                digits = "".join(c for c in level_str if c.isdigit())
                if digits:
                    new_pct = max(0, min(100, int(digits)))
                else:
                    return ToolResult(ok=False, message=f"Could not understand volume level '{level}'.")

            volume.SetMute(0, None)
            volume.SetMasterVolumeLevelScalar(new_pct / 100.0, None)
            return ToolResult(
                ok=True,
                message=f"Volume set to {new_pct} percent.",
                data={"volume": new_pct},
            )
        except Exception as e:
            logger.exception(f"Volume control failed: {e}")
            return ToolResult(ok=False, message=f"Failed to adjust volume: {e}")


@tool(
    name="mute",
    description="Mute or toggle mute on system audio.",
    params={"state": {"type": "string", "description": "'on', 'off', or 'toggle'", "required": False}},
    risk="low",
)
def mute(state: str = "toggle") -> ToolResult:
    """Mute system audio."""
    with COMContext():
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL

            devices = AudioUtilities.GetSpeakers()
            if hasattr(devices, "EndpointVolume"):
                volume = devices.EndpointVolume
            else:
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = ctypes.cast(interface, ctypes.POINTER(IAudioEndpointVolume))

            current_mute = volume.GetMute()
            if state == "on":
                new_mute = 1
            elif state == "off":
                new_mute = 0
            else:
                new_mute = 0 if current_mute else 1

            volume.SetMute(new_mute, None)
            status_text = "Muted." if new_mute else "Unmuted."
            return ToolResult(ok=True, message=status_text, data={"muted": bool(new_mute)})
        except Exception as e:
            return ToolResult(ok=False, message=f"Failed to toggle mute: {e}")


@tool(
    name="set_brightness",
    description="Set display brightness level (0 to 100).",
    params={"level": {"type": "integer", "description": "Brightness percentage from 0 to 100"}},
    risk="low",
)
def set_brightness(level: int) -> ToolResult:
    """Set screen brightness."""
    try:
        import screen_brightness_control as sbc
        target = max(0, min(100, int(level)))
        sbc.set_brightness(target)
        return ToolResult(
            ok=True,
            message=f"Brightness set to {target} percent.",
            data={"brightness": target},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Could not change brightness: {e}")


@tool(
    name="lock_screen",
    description="Lock the Windows workstation.",
    params={},
    risk="low",
)
def lock_screen() -> ToolResult:
    """Lock Windows screen."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return ToolResult(ok=True, message="Locking the screen.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to lock workstation: {e}")


@tool(
    name="screenshot",
    description="Take a screenshot of the desktop and save it to the Pictures folder.",
    params={},
    risk="low",
)
def screenshot() -> ToolResult:
    """Capture full desktop screenshot."""
    try:
        pictures_dir = Path.home() / "Pictures" / "Screenshots"
        pictures_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = pictures_dir / f"Screenshot_{timestamp}.png"

        img = ImageGrab.grab()
        img.save(str(file_path))

        return ToolResult(
            ok=True,
            message=f"Screenshot saved to your Screenshots folder.",
            data={"path": str(file_path)},
        )
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to take screenshot: {e}")


@tool(
    name="get_battery",
    description="Check current battery charge percentage and power connection status.",
    params={},
    risk="low",
)
def get_battery() -> ToolResult:
    """Get battery status."""
    battery = psutil.sensors_battery()
    if battery is None:
        return ToolResult(ok=True, message="No battery detected. This PC is running on AC power.")

    percent = int(battery.percent)
    plugged = battery.power_plugged
    charging_text = "plugged in" if plugged else "on battery"
    return ToolResult(
        ok=True,
        message=f"Battery is at {percent} percent and {charging_text}.",
        data={"percent": percent, "plugged": plugged},
    )


@tool(
    name="get_time",
    description="Get the current local time.",
    params={},
    risk="low",
)
def get_time() -> ToolResult:
    """Get current time."""
    now = datetime.datetime.now()
    formatted = now.strftime("%I:%M %p").lstrip("0")
    return ToolResult(
        ok=True,
        message=f"It is {formatted}.",
        data={"time": formatted},
    )


@tool(
    name="get_date",
    description="Get the current date and day of the week.",
    params={},
    risk="low",
)
def get_date() -> ToolResult:
    """Get current date."""
    now = datetime.datetime.now()
    formatted = now.strftime("%A, %B %d, %Y")
    return ToolResult(
        ok=True,
        message=f"Today is {formatted}.",
        data={"date": formatted},
    )


@tool(
    name="sleep",
    description="Put the computer into sleep mode.",
    params={},
    risk="high",
)
def power_sleep() -> ToolResult:
    """Put PC to sleep."""
    try:
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
        return ToolResult(ok=True, message="Putting the PC to sleep.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to sleep: {e}")


@tool(
    name="shutdown",
    description="Shut down the computer.",
    params={},
    risk="high",
)
def power_shutdown() -> ToolResult:
    """Shut down PC."""
    try:
        subprocess.run(["shutdown", "/s", "/t", "10"], check=True)
        return ToolResult(ok=True, message="Shutting down the computer.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to initiate shutdown: {e}")


@tool(
    name="restart",
    description="Restart the computer.",
    params={},
    risk="high",
)
def power_restart() -> ToolResult:
    """Restart PC."""
    try:
        subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
        return ToolResult(ok=True, message="Restarting the computer.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to initiate restart: {e}")
