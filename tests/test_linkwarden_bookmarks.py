"""Tests for the Linkwarden-to-Homepage bookmark synchronization helpers."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "linkwarden_bookmarks", ROOT / "tasks/docker/linkwarden_bookmarks.py"
)


@pytest.fixture
def module(monkeypatch):
    import sys
    import types

    pyinfra = types.ModuleType("pyinfra")
    pyinfra.host = types.SimpleNamespace(data={"docker": {}})
    monkeypatch.setitem(sys.modules, "pyinfra", pyinfra)
    builtins = __import__("builtins")
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    loaded = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(loaded)
    return loaded


def test_fetch_links_follows_cursor_and_rejects_repeated_cursor(module, monkeypatch):
    responses = iter([
        {"data": {"links": [{"id": 1}], "nextCursor": 10}},
        {"data": {"links": [{"id": 2}], "nextCursor": None}},
    ])
    monkeypatch.setattr(module, "api_json", lambda *_args: next(responses))
    assert module.fetch_links("https://links.example", "token") == [
        {"id": 1}, {"id": 2},
    ]


def test_fetch_links_rejects_incomplete_response(module, monkeypatch):
    monkeypatch.setattr(module, "api_json", lambda *_args: {"data": {"links": []}})
    with pytest.raises(RuntimeError, match="Unexpected"):
        module.fetch_links("https://links.example", "token")


def test_bookmarks_are_grouped_and_deduplicated(module, monkeypatch, tmp_path):
    monkeypatch.setattr(module, "download_favicon", lambda *_args: "/icons/example.ico")
    links = [
        {"type": "url", "url": "https://one.example", "name": "One",
         "collection": {"name": "Reading"}},
        {"type": "url", "url": "https://one.example", "name": "Duplicate",
         "collection": {"name": "Reading"}},
        {"type": "url", "url": "https://two.example", "name": "Two",
         "collection": {"name": "Research"}},
    ]
    result = module.build_bookmark_groups(links, "https://links.example", "token", tmp_path)
    assert [next(iter(group)) for group in result] == ["Reading", "Research"]
    assert len(result[0]["Reading"]) == 1
    assert result[0]["Reading"][0]["One"][0]["icon"] == "/icons/example.ico"


def test_managed_bookmark_update_is_idempotent_and_preserves_surrounding_text(
    module, tmp_path,
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
    assert module.update_managed_bookmarks(config, groups) is True
    first = config.read_text(encoding="utf-8")
    assert "before = True" in first and "after = True" in first
    assert module.update_managed_bookmarks(config, groups) is False
    assert config.read_text(encoding="utf-8") == first


def test_managed_bookmark_update_requires_markers(module, tmp_path):
    config = tmp_path / "@local.py"
    config.write_text("bookmarks = []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker"):
        module.update_managed_bookmarks(config, [])
