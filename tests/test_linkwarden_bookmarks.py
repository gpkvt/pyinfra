"""Tests for the Linkwarden-to-Homepage bookmark synchronization helpers."""
# pylint: disable=protected-access
import ast
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
    monkeypatch.setattr(loaded_module, "download_favicon", lambda *_args, **_kwargs: "/icons/example.ico")
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


def test_managed_bookmark_groups_are_top_level_and_preserve_homepage_layout(
    loaded_module, tmp_path,
):
    config = tmp_path / "@local.py"
    config.write_text(
        'bookmarks = [\n'
        '    {"Existing": [{"Kept": [{"href": "https://existing.example"}]}]},\n'
        '    # BEGIN LINKWARDEN BOOKMARKS (managed)\n'
        '    # END LINKWARDEN BOOKMARKS (managed)\n'
        ']\n'
        'settings = {"layout": [{"Services": {"style": "row", "columns": 3}}]}\n',
        encoding="utf-8",
    )
    groups = [
        {"Reading": [{"Example": [{"href": "https://example.com"}]}]},
        {"Research": [{"Docs": [{"href": "https://docs.example"}]}]},
    ]

    assert loaded_module.update_managed_bookmarks(config, groups) is True

    parsed = ast.parse(config.read_text(encoding="utf-8"))
    values = {node.targets[0].id: node.value for node in parsed.body}
    bookmarks = values["bookmarks"]
    assert isinstance(bookmarks, ast.List)
    assert len(bookmarks.elts) == 3
    assert all(isinstance(group, ast.Dict) for group in bookmarks.elts)
    assert ast.literal_eval(bookmarks.elts[0]) == {
        "Existing": [{"Kept": [{"href": "https://existing.example"}]}]
    }
    assert ast.literal_eval(bookmarks.elts[1]) == {
        "Reading": [{"Example": [{"href": "https://example.com"}]}]
    }
    assert ast.literal_eval(bookmarks.elts[2]) == {
        "Research": [{"Docs": [{"href": "https://docs.example"}]}]
    }
    assert ast.literal_eval(values["settings"]) == {
        "layout": [{"Services": {"style": "row", "columns": 3}}]
    }


def test_managed_bookmark_update_requires_markers(loaded_module, tmp_path):
    config = tmp_path / "@local.py"
    config.write_text("bookmarks = []\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="marker"):
        loaded_module.update_managed_bookmarks(config, [])


def test_dry_run_does_not_download_icons_or_modify_config(loaded_module, monkeypatch, tmp_path):
    config = tmp_path / "@local.py"
    original = (
        'bookmarks = [\n'
        '            # BEGIN LINKWARDEN BOOKMARKS (managed)\n'
        '            # END LINKWARDEN BOOKMARKS (managed)\n'
        '        ]\n'
    )
    config.write_text(original, encoding="utf-8")
    monkeypatch.setattr(loaded_module, "fetch_links", lambda *_args: [
        {"type": "url", "url": "https://example.com", "name": "Example",
         "collection": {"name": "Reading"}},
    ])
    monkeypatch.setattr(
        loaded_module, "download_favicon",
        lambda *_args, **_kwargs: pytest.fail("dry run must not download favicons"),
    )
    assert loaded_module.synchronize(
        config, tmp_path / "icons", "https://links.example", "token", dry_run=True
    ) is False
    assert config.read_text(encoding="utf-8") == original
    assert not (tmp_path / "icons").exists()



def test_resolve_sync_settings_reads_linkwarden_api_key_from_secrets(loaded_module):
    config = {"docker": {
        "linkwarden": {"domain": "links.example"},
        "homepage": {"bookmarks": []},
    }}
    secret_data = {"docker": {"linkwarden": {"api_key": "linkwarden-token"}}}
    assert loaded_module.resolve_sync_settings(config, secret_data) == (
        "links.example", "linkwarden-token"
    )


def test_resolve_sync_settings_supports_homepage_environment_fallback(loaded_module):
    config = {"docker": {
        "linkwarden": {},
        "homepage": {"bookmarks": []},
    }}
    secret_data = {"docker": {"homepage": {"environment": {
        "HOMEPAGE_VAR_LINKWARDEN_API_KEY": "homepage-token"
    }}}}
    assert loaded_module.resolve_sync_settings(config, secret_data) == (
        "linkwarden.21x9.org", "homepage-token"
    )


def test_resolve_sync_settings_prefers_linkwarden_api_key(loaded_module):
    config = {"docker": {"linkwarden": {}, "homepage": {"bookmarks": []}}}
    secret_data = {"docker": {
        "linkwarden": {"api_key": "linkwarden-token"},
        "homepage": {"environment": {
            "HOMEPAGE_VAR_LINKWARDEN_API_KEY": "homepage-token"
        }},
    }}
    assert loaded_module.resolve_sync_settings(config, secret_data)[1] == "linkwarden-token"


def test_resolve_sync_settings_reports_missing_api_key(loaded_module):
    config = {"docker": {"linkwarden": {}, "homepage": {"bookmarks": []}}}
    with pytest.raises(ValueError, match="secrets.docker.linkwarden.api_key"):
        loaded_module.resolve_sync_settings(config, {})


def test_select_local_secrets_uses_inventory_target_not_system_hostname(loaded_module):
    secret_document = {
        "shared": {"shared_value": True},
        "hosts": {
            "@local": {"docker": {"linkwarden": {"api_key": "local-token"}}},
            "chao": {"docker": {"linkwarden": {"api_key": "wrong-token"}}},
        },
    }
    selected_host = []
    selected = loaded_module.select_local_secrets(
        secret_document,
        lambda document, host: selected_host.append(host) or document["hosts"][host],
    )
    assert selected_host == ["@local"]
    assert selected["docker"]["linkwarden"]["api_key"] == "local-token"


@pytest.mark.parametrize(
    ("content_type", "extension"),
    [
        ("image/x-icon", ".ico"),
        ("image/vnd.microsoft.icon", ".ico"),
        ("image/png", ".png"),
        ("image/svg+xml; charset=utf-8", ".svg"),
        ("image/jpeg", ".jpg"),
        ("image/webp", ".webp"),
        ("image/gif", ".gif"),
    ],
)
def test_favicon_extension_matches_content_type(loaded_module, content_type, extension):
    assert loaded_module.favicon_extension(content_type) == extension


def test_favicon_extension_rejects_unknown_content_type(loaded_module):
    assert loaded_module.favicon_extension("text/html") is None


def test_download_favicon_uses_detected_extension_and_is_idempotent(
    loaded_module, monkeypatch, tmp_path,
):
    class Response:
        headers = {"Content-Type": "image/png"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return b"png-image-data"

    monkeypatch.setattr(loaded_module.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())
    destination = tmp_path / loaded_module.favicon_filename("https://example.com", ".ico")
    result = loaded_module.download_favicon(
        "https://links.example", "https://example.com", "token", destination
    )
    assert result.endswith(".png")
    icon_path = tmp_path / result.rsplit("/", 1)[1]
    assert icon_path.read_bytes() == b"png-image-data"
    before = icon_path.stat().st_mtime_ns
    assert loaded_module.download_favicon(
        "https://links.example", "https://example.com", "token", destination
    ) == result
    assert icon_path.stat().st_mtime_ns == before


def test_collect_service_favicons_downloads_only_missing_local_icons(
    loaded_module, monkeypatch, tmp_path,
):
    (tmp_path / "existing.png").write_bytes(b"existing")
    calls = []

    def download(_base, url, _token, _destination, **kwargs):
        prefix = kwargs.get("prefix", "linkwarden")
        calls.append((url, prefix))
        return f"/icons/{prefix}-new.png"

    monkeypatch.setattr(loaded_module, "download_favicon", download)
    services = [
        {"Services": [
            {"Existing": {"href": "https://existing.example", "icon": "/icons/existing.png"}},
            {"Missing": {"href": "https://missing.example"}},
            {"MissingFile": {"href": "https://missing-file.example", "icon": "/icons/not-here.png"}},
            {"Material": {"href": "https://material.example", "icon": "mdi-database"}},
        ]},
    ]
    result = loaded_module.collect_service_favicons(
        services, "https://links.example", "token", tmp_path
    )
    assert result == {
        "Missing": "/icons/homepage-new.png",
        "MissingFile": "/icons/homepage-new.png",
    }
    assert calls == [
        ("https://missing.example", "homepage"),
        ("https://missing-file.example", "homepage"),
    ]


def test_update_service_icon_references_is_idempotent_and_adds_missing_icon(
    loaded_module, tmp_path,
):
    config = tmp_path / "@local.py"
    config.write_text(
        'docker = {"homepage": {"services": [{"Services": ['
        '{"AppFlowy": {"href": "https://appflowy.example"}}, '
        '{"NocoDB": {"icon": "/icons/missing.png", "href": "https://nocodb.example"}}'
        ']}]}}\n',
        encoding="utf-8",
    )
    references = {
        "AppFlowy": "/icons/homepage-appflowy.svg",
        "NocoDB": "/icons/homepage-nocodb.png",
    }
    assert loaded_module.update_service_icon_references(config, references) is True
    result = config.read_text(encoding="utf-8")
    parsed = ast.parse(result)
    docker = ast.literal_eval(parsed.body[0].value)
    services = docker["homepage"]["services"][0]["Services"]
    assert services[0]["AppFlowy"]["icon"] == "/icons/homepage-appflowy.svg"
    assert services[1]["NocoDB"]["icon"] == "/icons/homepage-nocodb.png"
    assert loaded_module.update_service_icon_references(config, references) is False
    assert config.read_text(encoding="utf-8") == result



def test_favicon_filename_is_shared_by_urls_on_same_origin(loaded_module):
    first = loaded_module.favicon_filename("https://example.com/one", ".png")
    second = loaded_module.favicon_filename("https://example.com/two?q=1", ".png")
    assert first == second


def test_discover_favicon_urls_resolves_nonstandard_and_relative_paths(
    loaded_module, monkeypatch,
):
    class Response:
        headers = {"Content-Type": "text/html"}
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def geturl(self):
            return "https://example.com/path/page"
        def read(self, _size):
            return (
                b'<link rel="shortcut icon" href="/assets/site-mark.png">'
                b'<link rel="apple-touch-icon" href="../touch.png">'
            )

    monkeypatch.setattr(
        loaded_module.urllib.request, "urlopen",
        lambda *_args, **_kwargs: Response(),
    )
    assert loaded_module.discover_favicon_urls("https://example.com/path/page") == [
        "https://example.com/assets/site-mark.png",
        "https://example.com/touch.png",
        "https://example.com/favicon.ico",
    ]


def test_download_favicon_reuses_origin_cache_without_network(
    loaded_module, monkeypatch, tmp_path,
):
    cache = {"https://example.com": "/icons/shared.png"}
    monkeypatch.setattr(
        loaded_module, "discover_favicon_urls",
        lambda *_args: pytest.fail("cached favicon must not trigger discovery"),
    )
    assert loaded_module.download_favicon(
        "https://links.example", "https://example.com/page", "token",
        tmp_path / "unused.ico", icon_cache=cache,
    ) == "/icons/shared.png"


def test_bookmarks_on_same_site_download_one_favicon(
    loaded_module, monkeypatch, tmp_path,
):
    calls = []
    def download(_base, url, _token, _destination, **kwargs):
        icon_cache = kwargs["icon_cache"]
        origin = loaded_module.favicon_origin(url)
        if origin in icon_cache:
            return icon_cache[origin]
        calls.append(url)
        icon_cache[origin] = "/icons/shared.png"
        return "/icons/shared.png"

    monkeypatch.setattr(loaded_module, "download_favicon", download)
    links = [
        {"type": "url", "url": "https://example.com/one", "name": "One",
         "collection": {"name": "Reading"}},
        {"type": "url", "url": "https://example.com/two", "name": "Two",
         "collection": {"name": "Reading"}},
    ]
    groups = loaded_module.build_bookmark_groups(
        links, "https://links.example", "token", tmp_path
    )
    assert len(calls) == 1
    assert all(
        entry[next(iter(entry))][0]["icon"] == "/icons/shared.png"
        for entry in groups[0]["Reading"]
    )



def test_cleanup_unused_favicons_removes_only_unreferenced_managed_icons(
    loaded_module, tmp_path,
):
    config = tmp_path / "@local.py"
    config.write_text(
        'bookmarks = [{"Reading": [{"Kept": [{"href": "https://kept.example", '
        '"icon": "/icons/linkwarden-kept.png"}]}]}]\n'
        'docker = {"homepage": {"services": [{"Services": ['
        '{"UsedService": {"icon": "/icons/homepage-used.svg"}}]}]}}\n',
        encoding="utf-8",
    )
    icons = tmp_path / "icons"
    icons.mkdir()
    for name in (
        "linkwarden-kept.png", "linkwarden-orphan.ico",
        "homepage-used.svg", "homepage-orphan.png", "custom-icon.png",
    ):
        (icons / name).write_bytes(b"icon")

    assert loaded_module.cleanup_unused_favicons(config, icons) is True
    assert sorted(path.name for path in icons.iterdir()) == [
        "custom-icon.png", "homepage-used.svg", "linkwarden-kept.png",
    ]
    assert loaded_module.cleanup_unused_favicons(config, icons) is False


def test_cleanup_unused_favicons_preserves_shared_icon_until_last_reference(
    loaded_module, tmp_path,
):
    config = tmp_path / "@local.py"
    config.write_text(
        'bookmarks = [{"A": [{"One": [{"icon": "/icons/linkwarden-shared.png"}]}, '
        '{"Two": [{"icon": "/icons/linkwarden-shared.png"}]}]}]\n',
        encoding="utf-8",
    )
    icons = tmp_path / "icons"
    icons.mkdir()
    shared = icons / "linkwarden-shared.png"
    shared.write_bytes(b"icon")

    assert loaded_module.cleanup_unused_favicons(config, icons) is False
    config.write_text(
        'bookmarks = [{"A": [{"Two": [{"icon": "/icons/linkwarden-shared.png"}]}]}]\n',
        encoding="utf-8",
    )
    assert loaded_module.cleanup_unused_favicons(config, icons) is False
    config.write_text("bookmarks = []\n", encoding="utf-8")
    assert loaded_module.cleanup_unused_favicons(config, icons) is True
    assert not shared.exists()


def test_cleanup_unused_favicons_handles_missing_directory(loaded_module, tmp_path):
    config = tmp_path / "@local.py"
    config.write_text("bookmarks = []\n", encoding="utf-8")
    assert loaded_module.cleanup_unused_favicons(config, tmp_path / "missing") is False


def test_bookmark_blacklist_filters_by_linkwarden_id_before_favicon_download(
    loaded_module, monkeypatch, tmp_path,
):
    downloaded = []
    monkeypatch.setattr(
        loaded_module, "download_favicon",
        lambda _base, url, *_args, **_kwargs: downloaded.append(url) or "/icons/example.ico",
    )
    links = [
        {"id": 101, "type": "url", "url": "https://blocked.example", "name": "Blocked",
         "collection": {"name": "Reading"}},
        {"id": "202", "type": "url", "url": "https://kept.example", "name": "Kept",
         "collection": {"name": "Reading"}},
        {"id": 303, "type": "url", "url": "https://also-blocked.example", "name": "Also blocked",
         "collection": {"name": "Reading"}},
    ]

    groups = loaded_module.build_bookmark_groups(
        links, "https://links.example", "token", tmp_path,
        blacklist=[101, "303"],
    )

    assert [next(iter(entry)) for entry in groups[0]["Reading"]] == ["Kept"]
    assert downloaded == ["https://kept.example"]


def test_bookmark_blacklist_defaults_to_empty(loaded_module, monkeypatch, tmp_path):
    monkeypatch.setattr(loaded_module, "download_favicon", lambda *_args, **_kwargs: None)
    links = [{
        "id": 101, "type": "url", "url": "https://example.com", "name": "Example",
        "collection": {"name": "Reading"},
    }]
    groups = loaded_module.build_bookmark_groups(
        links, "https://links.example", "token", tmp_path,
    )
    assert [next(iter(entry)) for entry in groups[0]["Reading"]] == ["Example"]


def test_api_json_sends_bearer_token_and_parses_json(loaded_module, monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"data": {"ok": true}}'

    observed = {}

    def open_request(request, timeout):
        observed["url"] = request.full_url
        observed["authorization"] = request.get_header("Authorization")
        observed["accept"] = request.get_header("Accept")
        observed["timeout"] = timeout
        return Response()

    monkeypatch.setattr(loaded_module.urllib.request, "urlopen", open_request)

    assert loaded_module.api_json("https://links.example/api", "secret") == {
        "data": {"ok": True}
    }
    assert observed == {
        "url": "https://links.example/api",
        "authorization": "Bearer secret",
        "accept": "application/json",
        "timeout": loaded_module.TIMEOUT,
    }


def test_api_json_rejects_non_success_http_status(loaded_module, monkeypatch):
    class Response:
        status = 503

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"{}"

    monkeypatch.setattr(
        loaded_module.urllib.request, "urlopen", lambda *_args, **_kwargs: Response()
    )
    with pytest.raises(RuntimeError, match="HTTP 503"):
        loaded_module.api_json("https://links.example/api", "secret")


def test_favicon_origin_normalizes_scheme_and_host(loaded_module):
    assert loaded_module.favicon_origin("HTTPS://Example.COM/path?q=1") == (
        "https://example.com"
    )


def test_favicon_html_parser_collects_only_icon_links(loaded_module):
    parser = loaded_module.FaviconHTMLParser()
    parser.feed(
        '<link rel="stylesheet" href="style.css">'
        '<link rel="shortcut icon" href="/favicon.ico">'
        '<link rel="apple-touch-icon" href="/touch.png">'
        '<a href="/not-an-icon">ignored</a>'
    )
    assert parser.icons == ["/favicon.ico", "/touch.png"]


@pytest.mark.parametrize(
    ("content_type", "content", "expected"),
    [
        ("image/png", b"png", (b"png", ".png")),
        ("text/html", b"<html>", None),
        ("image/png", b"", None),
    ],
)
def test_download_image_accepts_only_nonempty_supported_images(
    loaded_module, monkeypatch, content_type, content, expected
):
    class Response:
        headers = {"Content-Type": content_type}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return content

    monkeypatch.setattr(
        loaded_module.urllib.request, "urlopen",
        lambda *_args, **_kwargs: Response(),
    )
    assert loaded_module._download_image("https://example.com/icon") == expected


def test_download_image_rejects_content_over_size_limit(loaded_module, monkeypatch):
    class Response:
        headers = {"Content-Type": "image/png"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, size):
            assert size == 5
            return b"12345"

    monkeypatch.setattr(loaded_module, "MAX_FAVICON_SIZE", 4)
    monkeypatch.setattr(
        loaded_module.urllib.request, "urlopen",
        lambda *_args, **_kwargs: Response(),
    )
    assert loaded_module._download_image("https://example.com/icon") is None


def test_main_uses_local_secrets_and_passes_dry_run_to_sync(
    loaded_module, monkeypatch, tmp_path
):
    root = tmp_path
    monkeypatch.setattr(loaded_module, "__file__", str(root / "tasks/docker/linkwarden_bookmarks.py"))
    monkeypatch.setattr(loaded_module.Path, "resolve", lambda _path: root / "tasks/docker/linkwarden_bookmarks.py")
    monkeypatch.setattr(loaded_module.sys, "argv", ["linkwarden_bookmarks.py", "--dry-run"])
    monkeypatch.setattr(
        loaded_module.runpy, "run_path",
        lambda _path: {
            "docker": {
                "linkwarden": {"blacklist": ["blocked"]},
                "homepage": {"services": [{"Services": []}]},
            }
        },
    )
    monkeypatch.setattr(
        loaded_module.subprocess, "run",
        lambda *_args, **_kwargs: types.SimpleNamespace(stdout='{"hosts": {"@local": {"docker": {"linkwarden": {"api_key": "local-token"}}}}}'),
    )
    common = types.ModuleType("common")
    common.select_host_secrets = lambda document, host: document["hosts"][host]
    monkeypatch.setitem(sys.modules, "common", common)
    calls = []
    monkeypatch.setattr(
        loaded_module, "synchronize",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    loaded_module.main()

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args[2:] == ("linkwarden.21x9.org", "local-token")
    assert kwargs["dry_run"] is True
    assert kwargs["blacklist"] == ["blocked"]
