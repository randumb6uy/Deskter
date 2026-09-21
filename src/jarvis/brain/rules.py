"""Fast-path rule matching engine for millisecond intent dispatch."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.actions.apps import get_indexer


@dataclass
class RuleMatch:
    """Represents the outcome of a rule pattern match."""
    matched: bool
    tool_name: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    direct_reply: Optional[str] = None


class RuleMatcher:
    """Matches common voice/text commands using regex and fuzzy string comparisons."""

    def __init__(self) -> None:
        self.indexer = get_indexer()

    def match(self, text: str) -> RuleMatch:
        """Evaluate input string against rule patterns.
        
        Returns RuleMatch with matched=True and tool/params if matched,
        otherwise RuleMatch with matched=False.
        """
        cleaned = text.strip().lower()
        if not cleaned:
            return RuleMatch(matched=False)

        # Remove leading wakeword / greeting if present in text
        cleaned = re.sub(r"^(hey\s+)?(deskter|jarvis)[,\s]*", "", cleaned).strip()
        if not cleaned:
            return RuleMatch(matched=True, direct_reply="Yes, I am listening.")

        # Multi-step conjunctions (e.g. "open chrome and search ...", "volume up then mute")
        # should fall through to the LLM for multi-tool sequencing.
        if re.search(r"\b(and\s+also|and\s+then|and|then|afterwards)\b", cleaned):
            return RuleMatch(matched=False)

        # 1. Meta / Help / Status
        if cleaned in ["help", "what can you do", "show commands", "commands"]:
            return RuleMatch(matched=True, tool_name="help", params={})

        if cleaned in ["list apps", "running apps", "what apps are running", "list running apps"]:
            return RuleMatch(matched=True, tool_name="list_running_apps", params={})

        if cleaned in ["refresh apps", "update apps", "rescan apps"]:
            return RuleMatch(matched=True, tool_name="refresh_apps", params={})

        # 2. Time, Date, Battery
        if re.match(r"^(?:what(?:'s|\s+is)?\s+(?:the\s+)?time(?:\s+(?:is\s+it|now|it\s+is))?|tell\s+me\s+the\s+time|current\s+time|time)$", cleaned):
            return RuleMatch(matched=True, tool_name="get_time", params={})

        if re.match(r"^(?:what(?:'s|\s+is)?\s+(?:the\s+|today(?:'s)?\s+)?(date|day)(?:\s+(?:is\s+it|today|now))?|what\s+day\s+is\s+(?:it\s+)?today|today(?:'s)?\s+date|date)$", cleaned):
            return RuleMatch(matched=True, tool_name="get_date", params={})

        if re.match(r"^(?:(?:check\s+|get\s+|what\s+is\s+the\s+)?battery(?:\s+status|\s+percentage|\s+level)?|how\s+much\s+battery(?:\s+(?:is\s+left|do\s+i\s+have))?)$", cleaned):
            return RuleMatch(matched=True, tool_name="get_battery", params={})

        # 3. Screenshot and Screen Lock
        if cleaned in ["screenshot", "take a screenshot", "take screenshot", "capture screen"]:
            return RuleMatch(matched=True, tool_name="screenshot", params={})

        if cleaned in ["lock", "lock screen", "lock computer", "lock pc", "lock workstation"]:
            return RuleMatch(matched=True, tool_name="lock_screen", params={})

        # 4. Power controls (high risk)
        if re.match(r"^(?:sleep|go\s+to\s+sleep|put\s+computer\s+to\s+sleep)(?:\s+(?:pc|computer))?$", cleaned):
            return RuleMatch(matched=True, tool_name="sleep", params={})

        if re.match(r"^(?:shutdown|shut\s+down|power\s+off|turn\s+off)(?:\s+(?:pc|computer))?$", cleaned):
            return RuleMatch(matched=True, tool_name="shutdown", params={})

        if re.match(r"^(?:restart|reboot)(?:\s+(?:pc|computer))?$", cleaned):
            return RuleMatch(matched=True, tool_name="restart", params={})

        # 5. Media keys
        if cleaned in ["play", "pause", "play pause", "play / pause", "resume", "stop music", "pause music", "resume music"]:
            return RuleMatch(matched=True, tool_name="media_play_pause", params={})

        if cleaned in ["next track", "next song", "skip track", "skip song", "next", "skip"]:
            return RuleMatch(matched=True, tool_name="media_next", params={})

        if cleaned in ["previous track", "previous song", "prev track", "prev song", "back track", "previous"]:
            return RuleMatch(matched=True, tool_name="media_prev", params={})

        # 6. Volume & Mute
        if cleaned in ["mute", "mute volume", "mute sound", "mute audio"]:
            return RuleMatch(matched=True, tool_name="mute", params={"state": "on"})

        if cleaned in ["unmute", "unmute volume", "unmute sound", "unmute audio"]:
            return RuleMatch(matched=True, tool_name="mute", params={"state": "off"})

        m = re.match(r"^(?:set\s+)?volume\s+(?:to\s+)?(up|down|max|min|\d+)\%?$", cleaned)
        if m:
            val = m.group(1)
            return RuleMatch(matched=True, tool_name="set_volume", params={"level": val})

        # 7. Brightness
        m = re.match(r"^(?:set\s+)?brightness\s+(?:to\s+)?(\d+)\%?$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="set_brightness", params={"level": int(m.group(1))})

        # 8. Notes
        m = re.match(r"^(?:take\s+note|note\s+that|write\s+down|save\s+note|take\s+a\s+note)\s+(.+)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="take_note", params={"text": m.group(1).strip()})

        if cleaned in ["get notes", "read notes", "show notes", "my notes", "list notes", "notes"]:
            return RuleMatch(matched=True, tool_name="get_notes", params={})

        # 9. Timers
        m = re.match(r"^(?:set\s+(?:a\s+)?)?timer\s+(?:for\s+)?(\d+)\s*(s|sec|secs|seconds|m|min|mins|minutes|h|hr|hrs|hours)?$", cleaned)
        if m:
            num = int(m.group(1))
            unit = (m.group(2) or "seconds").lower()
            if "m" in unit:
                seconds = num * 60
            elif "h" in unit:
                seconds = num * 3600
            else:
                seconds = num
            return RuleMatch(matched=True, tool_name="set_timer", params={"seconds": seconds})

        # 10. Antigravity Voice Bridge Commands
        if re.match(r"^(?:check\s+(?:the\s+)?(?:remaining\s+)?quota|how\s+much\s+quota(?:\s+(?:do\s+i\s+have|is\s+left))?|quota\s+remaining|antigravity\s+quota|check\s+(?:rate\s+)?limits|remaining\s+quota)$", cleaned):
            return RuleMatch(matched=True, tool_name="antigravity_quota", params={})

        if re.match(r"^(?:what\s+model(?:\s+is\s+running|\s+is\s+active)?|antigravity\s+model|model\s+info|active\s+model)$", cleaned):
            return RuleMatch(matched=True, tool_name="antigravity_model_info", params={})

        if re.match(r"^(?:cost\s+estimate|estimated\s+cost|token\s+cost|how\s+much\s+did\s+this\s+cost)$", cleaned):
            return RuleMatch(matched=True, tool_name="antigravity_cost_estimate", params={})

        if re.match(r"^(?:check\s+(?:the\s+)?usage\s+of\s+tokens|check\s+tokens|token\s+usage|how\s+many\s+tokens(?:\s+have\s+been\s+used)?|antigravity\s+tokens)$", cleaned):
            return RuleMatch(matched=True, tool_name="antigravity_token_usage", params={})

        m = re.match(r"^(?:change|set|switch)\s+mode\s+to\s+(.+)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="antigravity_set_mode", params={"mode": m.group(1).strip()})

        m = re.match(r"^(?:(?:ask|prompt|tell)\s+antigravity\s+(?:to\s+)?|antigravity\s+prompt\s+)(.+)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="antigravity_prompt", params={"prompt": m.group(1).strip()})

        if cleaned in ["antigravity status", "status of antigravity", "check antigravity status", "antigravity"]:
            return RuleMatch(matched=True, tool_name="antigravity_status", params={})

        if cleaned in ["list subagents", "active subagents", "antigravity subagents", "subagents"]:
            return RuleMatch(matched=True, tool_name="antigravity_list_subagents", params={})

        if cleaned in ["compact context", "compact tokens", "compact memory", "antigravity compact"]:
            return RuleMatch(matched=True, tool_name="antigravity_compact_context", params={})

        if cleaned in ["clear antigravity history", "reset antigravity", "clear antigravity"]:
            return RuleMatch(matched=True, tool_name="antigravity_clear_history", params={})

        m = re.match(r"^(?:(?:run|activate|execute)\s+)?(?:slash\s+command\s+|/)(goal|plan|schedule|learn|compact|undo|diff|grill-me|boost|browser|teamwork)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="antigravity_slash_command", params={"command": m.group(1).strip()})

        # 11. Web Search
        m = re.match(r"^(?:search\s+(?:for\s+|google\s+for\s+|on\s+google\s+for\s+)?|google\s+|look\s+up\s+)(.+)$", cleaned)
        if m:
            query = m.group(1).strip()
            return RuleMatch(matched=True, tool_name="web_search", params={"query": query})

        # 12. Known Sites
        known_sites = ["youtube", "github", "reddit", "gmail", "wikipedia", "chatgpt", "twitter", "x", "netflix", "spotify"]
        m = re.match(r"^(?:open|go\s+to|launch)\s+(" + "|".join(known_sites) + r")$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="open_site", params={"site": m.group(1)})

        # 13. Browser launch
        if cleaned in ["open browser", "launch browser", "start browser", "open internet"]:
            return RuleMatch(matched=True, tool_name="open_browser", params={})

        # 13. Folders and Files
        m = re.match(r"^(?:open\s+folder|open)\s+(downloads|documents|desktop)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="open_folder", params={"folder_name": m.group(1)})

        m = re.match(r"^(?:find\s+file|search\s+file)\s+(.+)$", cleaned)
        if m:
            return RuleMatch(matched=True, tool_name="find_file", params={"filename": m.group(1).strip()})

        # 14. App Launch / Close
        m = re.match(r"^(?:open|launch|start)\s+(.+)$", cleaned)
        if m:
            target = m.group(1).strip()
            if target.startswith("http://") or target.startswith("https://") or ("." in target and " " not in target):
                return RuleMatch(matched=True, tool_name="open_url", params={"url": target})
            if target in ["chrome", "edge", "firefox", "brave"]:
                return RuleMatch(matched=True, tool_name="open_browser", params={"browser": target})
            # Check if target is a known app or short name
            if len(target.split()) <= 3:
                return RuleMatch(matched=True, tool_name="open_app", params={"app_name": target})

        m = re.match(r"^(?:close|quit|exit|kill)\s+(.+)$", cleaned)
        if m:
            target = m.group(1).strip()
            if len(target.split()) <= 3:
                return RuleMatch(matched=True, tool_name="close_app", params={"app_name": target})

        # 15. Single word high-confidence app match (e.g. "notepad", "calculator", "spotify")
        if " " not in cleaned and len(cleaned) >= 3:
            match_name, path, score = self.indexer.resolve(cleaned)
            if score >= 85.0:
                return RuleMatch(matched=True, tool_name="open_app", params={"app_name": cleaned})

        return RuleMatch(matched=False)
