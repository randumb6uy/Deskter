"""Media playback control tools using Windows virtual key events."""

import ctypes
from jarvis.actions.registry import ToolResult, tool

# Windows Virtual Key Codes for Media
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def _send_media_key(vk_code: int) -> None:
    """Simulate hardware media keypress via Windows user32."""
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


@tool(
    name="media_play_pause",
    description="Toggle play/pause on background media (Spotify, YouTube, Media Player).",
    params={},
    risk="low",
)
def media_play_pause() -> ToolResult:
    """Toggle media play/pause."""
    try:
        _send_media_key(VK_MEDIA_PLAY_PAUSE)
        return ToolResult(ok=True, message="Toggled media playback.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to trigger play/pause: {e}")


@tool(
    name="media_next",
    description="Skip to the next track or video.",
    params={},
    risk="low",
)
def media_next() -> ToolResult:
    """Skip to next media track."""
    try:
        _send_media_key(VK_MEDIA_NEXT_TRACK)
        return ToolResult(ok=True, message="Playing next track.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to skip track: {e}")


@tool(
    name="media_prev",
    description="Go back to the previous track or video.",
    params={},
    risk="low",
)
def media_prev() -> ToolResult:
    """Go to previous media track."""
    try:
        _send_media_key(VK_MEDIA_PREV_TRACK)
        return ToolResult(ok=True, message="Playing previous track.")
    except Exception as e:
        return ToolResult(ok=False, message=f"Failed to go to previous track: {e}")
