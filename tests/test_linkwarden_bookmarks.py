"""Tests for the Linkwarden-to-Homepage bookmark synchronization helpers."""
# pylint: disable=redefined-outer-name
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "linkwarden_bookmarks", ROOT / "tasks/docker/linkwarden_bookmarks.py"
)


@pytest.fixture
def loaded_module(monkeypatch):
    pyinfra = types.ModuleType("pyinfra")
    pyinfra.host = types.SimpleNamespace(data={"docker": {}})
    monkeypatch.setitem(sys.modules, "pyinfra", pyinfra)
    builtins = __import__("builtins")
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    loaded = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(loaded)
    return loaded


def test_fetch_links_follows_cursor_and_rejects_repeated_cursor(loaded_module, monkeypatch):
    responses = iter([
        {"data": {"links": [{"id": 1}], "nextCursor": 10}},
        {"data": {"links": [{"id": 2}], "nextCursor": None}},
    ])
    monkeypatch.setattr(loaded_module, "api_json", lambda *_args: next(responses))
    assert loaded_module.fetch_links("https://links.example", "token") == [
        {"id": 1}, {"id": 2},
    ]


def test_fetch_links_rejects_incomplete_response(loaded_module, monkeypatch):
    monkeypatch.setattr(loaded_module, "api_json", lambda *_args: {"data": {"links": []}})
    with pytest.raises(RuntimeError, match="Unexpected"):
        loaded_module.fetch_links("https://links.example", "token")


def test_bookmarks_are_grouped_and_deduplicated(loaded_module, monkeypatch, tmp_path):
    monkeypatch.setattr(loaded_module, "download_favicon", lambda *_args: "/icons/example.ico")
    links = [
        {"type": "url", "url": "https://one.example", "name": "One",
         "collection": {"name": "Reading"}},
        {"type": "url", "url": "https://one.example", "name": "Duplicate",
         "collection": {"name": "Reading"}},
        {"type": "url", "url": "https://two.example", "name": "Two",
         "collection": {"name": "Research"}},
    ]
    result = loaded_module.build_bookmark_groups(links, "https://links.example", "token", tmp_path)
    assert [next(iter(group)) for group in result] == ["Reading", "Research"]
    assert len(result[0]["Reading"]) == 1
    assert result[0]["Reading"][0]["One"][0]["icon"] == "/icons/example.ico"


def test_managed_bookmark_update_is_idempotent_and_preserves_surrounding_text(
    loaded_module, tmp_path,
):
    config = tmp_path / "@local.py"
    config.write_text(
        'before = True\n        "bookmarks": [\n'
        '            # BEGIN LINKWARDEN BOOKMARKS (managed)\n'
        '            # END LINKWARDEN BOOKMARKS (managed)\n'
        '        ],\nafter = True\n',
        encoding="utf-8",
    )
    groups = [{"Reading": [{"Example": [{"href": "https://example.com"}]}]}]
    assert loaded_module.update_managed_bookmarks(config, groups) is True
    first = config.read_text(encoding="utf-8")
    assert "before = True" in first and "after = True" in first
    assert loaded_module.update_managed_bookmarks(config, groups) is False
    assert config.read_text(encoding="utf-8") == first


def test_managed_bookmark_update_requires_markers(loaded_module, tmp_path):
    config = tmp_path / "@local.py"
    config.write_text("bookmarks = []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker"):
        loaded_module.update_managed_bookmarks(config, [])


def test_dry_run_does_not_download_icons_or_modify_config(loaded_module, monkeypatch, tmp_path):
    config = tmp_path / "@local.py"
    original = (
        'bookmarks = [\\n'
        '            # BEGIN LINKWARDEN BOOKMARKS (managed)\\n'
        '            # END LINKWARDEN BOOKMARKS (managed)\\n'
        '        ]\\n'
    )
    config.write_text(original, encoding="utf-8")
    monkeypatch.setattr(loaded_module, "fetch_links", lambda *_args: [
        {"type": "url", "url": "https://example.com", "name": "Example",
         "collection": {"name": "Reading"}},
    ])
    monkeypatch.setattr(
        loaded_module, "download_favicon",
        lambda *_args: pytest.fail("dry run must not download favicons"),
    )
    assert loaded_module.synchronize(
        config, tmp_path / "icons", "https://links.example", "token", dry_run=True
    ) is False
    assert config.read_text(encoding="utf-8") == original
    assert not (tmp_path / "icons").exists()
