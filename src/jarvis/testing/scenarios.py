"""Test scenarios, synthetic workloads, and edge cases for the Deskter Testing Agent."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Scenario:
    """Specification of an automated assistant test scenario."""
    category: str
    description: str
    user_input: str
    expected_fast_path: Optional[bool] = None
    expected_tool: Optional[str] = None
    expected_params_contain: Dict[str, Any] = field(default_factory=dict)
    should_succeed: bool = True
    risk_level: Optional[str] = None
    is_security_test: bool = False


DEFAULT_SCENARIOS: List[Scenario] = [
    # 1. Fast-Path Time & Date
    Scenario(
        category="Time & Date",
        description="Fast-path current time query",
        user_input="what time is it",
        expected_fast_path=True,
        expected_tool="get_time",
    ),
    Scenario(
        category="Time & Date",
        description="Fast-path current date query",
        user_input="what is today's date",
        expected_fast_path=True,
        expected_tool="get_date",
    ),
    Scenario(
        category="Time & Date",
        description="Fast-path day query with wakeword prefix",
        user_input="Hey Deskter what day is today",
        expected_fast_path=True,
        expected_tool="get_date",
    ),

    # 2. Fast-Path System & Media Controls
    Scenario(
        category="System Controls",
        description="Volume adjustment percentage",
        user_input="volume 75",
        expected_fast_path=True,
        expected_tool="set_volume",
        expected_params_contain={"level": "75"},
    ),
    Scenario(
        category="System Controls",
        description="Relative volume up",
        user_input="volume up",
        expected_fast_path=True,
        expected_tool="set_volume",
        expected_params_contain={"level": "up"},
    ),
    Scenario(
        category="System Controls",
        description="Mute toggle",
        user_input="mute audio",
        expected_fast_path=True,
        expected_tool="mute",
        expected_params_contain={"state": "on"},
    ),
    Scenario(
        category="System Controls",
        description="Brightness level adjustment",
        user_input="set brightness to 60",
        expected_fast_path=True,
        expected_tool="set_brightness",
        expected_params_contain={"level": 60},
    ),
    Scenario(
        category="System Controls",
        description="Battery status check",
        user_input="check battery percentage",
        expected_fast_path=True,
        expected_tool="get_battery",
    ),
    Scenario(
        category="System Controls",
        description="Screenshot capture",
        user_input="take a screenshot",
        expected_fast_path=True,
        expected_tool="screenshot",
    ),
    Scenario(
        category="System Controls",
        description="Lock workstation",
        user_input="lock workstation",
        expected_fast_path=True,
        expected_tool="lock_screen",
    ),

    # 3. Media Controls
    Scenario(
        category="Media",
        description="Media play pause toggle",
        user_input="play pause",
        expected_fast_path=True,
        expected_tool="media_play_pause",
    ),
    Scenario(
        category="Media",
        description="Media next track",
        user_input="next song",
        expected_fast_path=True,
        expected_tool="media_next",
    ),

    # 4. Web Search and Known Sites
    Scenario(
        category="Web & Browser",
        description="Web search query",
        user_input="search for local weather forecast",
        expected_fast_path=True,
        expected_tool="web_search",
        expected_params_contain={"query": "local weather forecast"},
    ),
    Scenario(
        category="Web & Browser",
        description="Open well known site",
        user_input="open youtube",
        expected_fast_path=True,
        expected_tool="open_site",
        expected_params_contain={"site": "youtube"},
    ),
    Scenario(
        category="Web & Browser",
        description="Launch default browser",
        user_input="open browser",
        expected_fast_path=True,
        expected_tool="open_browser",
    ),

    # 5. Apps and Files
    Scenario(
        category="Apps & Files",
        description="Launch application by name",
        user_input="open notepad",
        expected_fast_path=True,
        expected_tool="open_app",
        expected_params_contain={"app_name": "notepad"},
    ),
    Scenario(
        category="Apps & Files",
        description="Close running application",
        user_input="close notepad",
        expected_fast_path=True,
        expected_tool="close_app",
        expected_params_contain={"app_name": "notepad"},
    ),
    Scenario(
        category="Apps & Files",
        description="Open Downloads folder",
        user_input="open downloads",
        expected_fast_path=True,
        expected_tool="open_folder",
        expected_params_contain={"folder_name": "downloads"},
    ),

    # 6. Utilities
    Scenario(
        category="Utility",
        description="Save quick note",
        user_input="take note test autonomous agent scenario",
        expected_fast_path=True,
        expected_tool="take_note",
    ),
    Scenario(
        category="Utility",
        description="Retrieve saved notes",
        user_input="get notes",
        expected_fast_path=True,
        expected_tool="get_notes",
    ),
    Scenario(
        category="Utility",
        description="Set countdown timer",
        user_input="set timer for 2 minutes",
        expected_fast_path=True,
        expected_tool="set_timer",
        expected_params_contain={"seconds": 120},
    ),
    Scenario(
        category="Utility",
        description="Display help information",
        user_input="help",
        expected_fast_path=True,
        expected_tool="help",
    ),

    # 7. Slow-Path / Complex / Multi-step Queries (Fallback to LLM)
    Scenario(
        category="Brain Routing",
        description="Multi-step command with conjunction",
        user_input="Open Chrome and then search for quantum computing",
        expected_fast_path=False,
    ),
    Scenario(
        category="Brain Routing",
        description="Conversational knowledge question",
        user_input="Explain how neural networks learn in simple terms",
        expected_fast_path=False,
    ),

    # 8. Security & Safety Gate
    Scenario(
        category="Security & Safety",
        description="High risk shutdown command",
        user_input="shutdown computer",
        expected_fast_path=True,
        expected_tool="shutdown",
        risk_level="high",
        is_security_test=True,
    ),

    # 9. Google Antigravity Voice Bridge Scenarios
    Scenario(
        category="Antigravity",
        description="Check token usage",
        user_input="check the usage of tokens",
        expected_fast_path=True,
        expected_tool="antigravity_token_usage",
    ),
    Scenario(
        category="Antigravity",
        description="Change mode to accept edits",
        user_input="change mode to accept edits",
        expected_fast_path=True,
        expected_tool="antigravity_set_mode",
        expected_params_contain={"mode": "accept edits"},
    ),
    Scenario(
        category="Antigravity",
        description="Send voice coding prompt",
        user_input="ask Antigravity to create a login component",
        expected_fast_path=True,
        expected_tool="antigravity_prompt",
    ),
    Scenario(
        category="Antigravity",
        description="Check Antigravity status",
        user_input="antigravity status",
        expected_fast_path=True,
        expected_tool="antigravity_status",
    ),
    Scenario(
        category="Antigravity",
        description="Trigger /goal slash command",
        user_input="/goal",
        expected_fast_path=True,
        expected_tool="antigravity_slash_command",
        expected_params_contain={"command": "goal"},
    ),
    Scenario(
        category="Antigravity",
        description="Compact conversation context",
        user_input="compact context",
        expected_fast_path=True,
        expected_tool="antigravity_compact_context",
    ),
    Scenario(
        category="Antigravity",
        description="Check remaining quota and limits",
        user_input="how much quota do i have",
        expected_fast_path=True,
        expected_tool="antigravity_quota",
    ),
    Scenario(
        category="Antigravity",
        description="Check active model information",
        user_input="what model is running",
        expected_fast_path=True,
        expected_tool="antigravity_model_info",
    ),
]
