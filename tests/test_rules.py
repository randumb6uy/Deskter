"""Unit tests for Fast-path RuleMatcher."""

import pytest
from jarvis.brain.rules import RuleMatcher


@pytest.fixture
def matcher() -> RuleMatcher:
    return RuleMatcher()


def test_rule_matcher_system_queries(matcher: RuleMatcher) -> None:
    # Time
    m = matcher.match("what time is it")
    assert m.matched is True
    assert m.tool_name == "get_time"

    # Date
    m = matcher.match("what's the date today")
    assert m.matched is True
    assert m.tool_name == "get_date"

    # Battery
    m = matcher.match("check battery")
    assert m.matched is True
    assert m.tool_name == "get_battery"

    # Lock & Screenshot
    m = matcher.match("take a screenshot")
    assert m.matched is True
    assert m.tool_name == "screenshot"

    m = matcher.match("lock screen")
    assert m.matched is True
    assert m.tool_name == "lock_screen"


def test_rule_matcher_volume_and_media(matcher: RuleMatcher) -> None:
    m = matcher.match("set volume to 80")
    assert m.matched is True
    assert m.tool_name == "set_volume"
    assert m.params["level"] == "80"

    m = matcher.match("volume up")
    assert m.matched is True
    assert m.tool_name == "set_volume"
    assert m.params["level"] == "up"

    m = matcher.match("mute")
    assert m.matched is True
    assert m.tool_name == "mute"
    assert m.params["state"] == "on"

    m = matcher.match("play")
    assert m.matched is True
    assert m.tool_name == "media_play_pause"

    m = matcher.match("next song")
    assert m.matched is True
    assert m.tool_name == "media_next"


def test_rule_matcher_search_and_sites(matcher: RuleMatcher) -> None:
    m = matcher.match("search for python async tutorials")
    assert m.matched is True
    assert m.tool_name == "web_search"
    assert m.params["query"] == "python async tutorials"

    m = matcher.match("open youtube")
    assert m.matched is True
    assert m.tool_name == "open_site"
    assert m.params["site"] == "youtube"


def test_rule_matcher_apps_and_browser(matcher: RuleMatcher) -> None:
    m = matcher.match("launch chrome")
    assert m.matched is True
    assert m.tool_name == "open_browser"
    assert m.params["browser"] == "chrome"

    m = matcher.match("open notepad")
    assert m.matched is True
    assert m.tool_name == "open_app"
    assert m.params["app_name"] == "notepad"

    m = matcher.match("close notepad")
    assert m.matched is True
    assert m.tool_name == "close_app"
    assert m.params["app_name"] == "notepad"


def test_rule_matcher_utilities(matcher: RuleMatcher) -> None:
    m = matcher.match("take note buy groceries tomorrow")
    assert m.matched is True
    assert m.tool_name == "take_note"
    assert "buy groceries" in m.params["text"]

    m = matcher.match("set timer for 5 minutes")
    assert m.matched is True
    assert m.tool_name == "set_timer"
    assert m.params["seconds"] == 300

    m = matcher.match("help")
    assert m.matched is True
    assert m.tool_name == "help"


def test_rule_matcher_unmatched_to_llm(matcher: RuleMatcher) -> None:
    # Complex or conversational queries should not match fast path
    m = matcher.match("Can you write a poem about artificial intelligence?")
    assert m.matched is False

    m = matcher.match("Open Chrome and also search for machine learning papers")
    assert m.matched is False
