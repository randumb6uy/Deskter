"""Unit tests for app discovery, indexing, and fuzzy matching."""

from jarvis.actions.apps import AppIndexer


def test_app_indexer_manual_aliases():
    aliases = {"myeditor": "C:\\fake\\editor.exe", "music": "C:\\fake\\music.exe"}
    indexer = AppIndexer(aliases=aliases)

    assert "myeditor" in indexer.index
    assert "music" in indexer.index


def test_app_indexer_fuzzy_resolution():
    indexer = AppIndexer(aliases={"super secret editor pro": "C:\\mock\\editor.exe", "fast video player": "C:\\mock\\player.exe"})

    # Exact
    name, path, score = indexer.resolve("super secret editor pro")
    assert name == "super secret editor pro"
    assert score == 100.0

    # Fuzzy partial / abbreviation
    name, path, score = indexer.resolve("fast video")
    assert name == "fast video player"
    assert score >= 70.0

    name, path, score = indexer.resolve("super secret editor")
    assert name == "super secret editor pro"
    assert score >= 80.0
