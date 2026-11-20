"""Tests for Mullvad Browser configuration reverse synchronization."""

import importlib.util
import json
import runpy

import pytest

from conftest import ROOT


SCRIPT = ROOT / "files/scripts/sync-mullvad-browser.py"


def load_sync_module():
    """Load the standalone command without executing its CLI."""
    spec = importlib.util.spec_from_file_location("sync_mullvad_browser", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_browser(tmp_path):
    """Create a distribution directory with one known and one unknown XPI."""
    distro = tmp_path / "distribution"
    extensions = distro / "extensions"
    extensions.mkdir(parents=True)
    (extensions / "known@example.invalid.xpi").write_bytes(b"test add-on")
    (extensions / "unknown@example.invalid.xpi").write_bytes(b"test add-on")
    (distro / "user.js").write_text(
        '// user.js\n'
        'user_pref("extensions.installDistroAddons", true);\n'
        'user_pref("privacy.resistFingerprinting", true);\n'
        'user_pref("browser.startup.homepage", "https://private.example");\n',
        encoding="utf-8",
    )
    return distro


def test_literal_assignments_do_not_evaluate_python():
    sync = load_sync_module()
    source = (
        'other = undefined_function()\n'
        'mullvad_extensions = {"Known": {"id": "known@example.invalid", '
        '"url": "https://addons.example/known.xpi"}}\n'
        'mullvad_browser_prefs = {"privacy.resistFingerprinting": True}\n'
    )
    parsed = sync.literal_assignments(source)
    assert parsed["mullvad_extensions"]["Known"]["id"] == "known@example.invalid"
    assert parsed["mullvad_browser_prefs"] == {"privacy.resistFingerprinting": True}


def test_valid_url_rejects_http_and_credentials():
    sync = load_sync_module()
    assert sync.valid_url("https://addons.example/extension.xpi")
    assert not sync.valid_url("http://addons.example/extension.xpi")
    assert not sync.valid_url("https://user:secret@addons.example/xpi")


def test_browser_extensions_and_metadata(tmp_path):
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "extensions.json").write_text(json.dumps({
        "addons": [
            {"id": "profile@example.invalid", "active": True,
             "sourceURI": "https://addons.example/profile.xpi"},
            {"id": "inactive@example.invalid", "active": False,
             "sourceURI": "https://addons.example/inactive.xpi"},
            {"id": "unsafe@example.invalid", "active": True,
             "sourceURI": "http://addons.example/unsafe.xpi"},
        ],
    }), encoding="utf-8")
    ids = sync.browser_extensions(distro, profile)
    assert {"known@example.invalid", "unknown@example.invalid",
            "profile@example.invalid"} <= ids
    assert "inactive@example.invalid" not in ids
    sources = sync.addon_sources(profile)
    assert sources["profile@example.invalid"].startswith("https://")
    assert "unsafe@example.invalid" not in sources


def test_browser_preferences_skip_sensitive_and_unknown_values(tmp_path):
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    prefs = sync.browser_preferences(distro / "user.js")
    assert prefs["privacy.resistFingerprinting"] is True
    assert prefs["extensions.installDistroAddons"] is True
    assert "browser.startup.homepage" not in prefs


def test_replace_assignments_preserves_other_top_level_configuration():
    sync = load_sync_module()
    source = (
        'hostname = "example"  # preserve me\n'
        'mullvad_extensions = {}  # old value\n'
        'docker = {"homepage": {}}\n'
    )
    updated = sync.replace_assignments(source, {
        "mullvad_extensions": {"Example": {
            "id": "example@example.invalid",
            "url": "https://addons.example/example.xpi",
        }},
        "mullvad_browser_prefs": {"privacy.resistFingerprinting": True},
    })
    assert 'hostname = "example"  # preserve me' in updated
    assert 'docker = {"homepage": {}}' in updated
    assert sync.literal_assignments(updated)["mullvad_browser_prefs"] == {
        "privacy.resistFingerprinting": True
    }
    assert sync.replace_assignments(updated, {
        "mullvad_extensions": sync.literal_assignments(updated)["mullvad_extensions"],
        "mullvad_browser_prefs": {"privacy.resistFingerprinting": True},
    }) == updated


def test_synchronize_preserves_known_urls_and_reports_unknown(tmp_path):
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    inventory = tmp_path / "workstation.py"
    original = (
        'workstation = {"desktop": {"enabled": False}}\n'
        'mullvad_extensions = {"Known": {"id": "known@example.invalid", '
        '"url": "https://addons.example/known.xpi"}}\n'
    )
    inventory.write_text(original, encoding="utf-8")
    before, after, unresolved = sync.synchronize(
        distro, None, distro / "user.js", inventory
    )
    assert before == original
    assert unresolved == ["unknown@example.invalid"]
    parsed = sync.literal_assignments(after)
    assert parsed["mullvad_extensions"]["Known"]["url"] == (
        "https://addons.example/known.xpi"
    )
    assert parsed["mullvad_browser_prefs"]["privacy.resistFingerprinting"] is True
    assert "workstation = " in after
    inventory.write_text(after, encoding="utf-8")
    assert sync.synchronize(distro, None, distro / "user.js", inventory)[1] == after


def test_synchronize_never_prunes_unresolved_extensions(tmp_path):
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    inventory = tmp_path / "@local.py"
    inventory.write_text(
        'mullvad_extensions = {"Missing": {"id": "old@example.invalid", '
        '"url": "https://addons.example/old.xpi"}}\n',
        encoding="utf-8",
    )
    _, updated, missing = sync.synchronize(
        distro, None, distro / "user.js", inventory, prune=True
    )
    assert missing == ["known@example.invalid", "unknown@example.invalid"]
    assert sync.literal_assignments(updated)["mullvad_extensions"] == {}


def test_main_is_preview_only_until_write(tmp_path, capsys):
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    inventory = tmp_path / "@local.py"
    inventory.write_text('mullvad_extensions = {}\n', encoding="utf-8")
    args = ["--inventory", str(inventory), "--distribution", str(distro)]
    sync.main(args)
    assert inventory.read_text(encoding="utf-8") == 'mullvad_extensions = {}\n'
    assert "Preview only" in capsys.readouterr().out
    sync.main([*args, "--write"])
    applied = inventory.read_text(encoding="utf-8")
    assert "mullvad_browser_prefs" in applied
    sync.main([*args, "--write"])
    assert inventory.read_text(encoding="utf-8") == applied
    assert "No changes." in capsys.readouterr().out


def test_profile_prefs_js_only_exports_safe_allowlisted_values(tmp_path):
    """Import UI/privacy toggles, never arbitrary private profile metadata."""
    sync = load_sync_module()
    prefs = tmp_path / "prefs.js"
    prefs.write_text(
        'user_pref("privacy.resistFingerprinting", true);\n'
        'user_pref("browser.tabs.warnOnClose", false);\n'
        'user_pref("browser.startup.homepage", "https://personal.example");\n'
        'user_pref("extensions.someAddon.token", "private");\n'
        'user_pref("network.proxy.http", "internal.example");\n',
        encoding="utf-8",
    )
    assert sync.browser_preferences(prefs) == {
        "privacy.resistFingerprinting": True,
        "browser.tabs.warnOnClose": False,
    }


def test_profile_sync_keeps_other_explicit_preferences(tmp_path):
    """Incomplete prefs.js never erases inventory preferences."""
    sync = load_sync_module()
    distro = fixture_browser(tmp_path)
    profile = tmp_path / "profile"
    profile.mkdir()
    (profile / "prefs.js").write_text(
        'user_pref("privacy.resistFingerprinting", false);\n'
        'user_pref("browser.startup.homepage", "https://personal.example");\n',
        encoding="utf-8",
    )
    inventory = tmp_path / "workstation.py"
    inventory.write_text(
        'mullvad_extensions = {}\n'
        'mullvad_browser_prefs = {"browser.tabs.minWidth": 88}\n',
        encoding="utf-8",
    )
    sync.main([
        "--profile", str(profile), "--distribution", str(distro),
        "--inventory", str(inventory), "--write",
    ])
    values = sync.literal_assignments(inventory.read_text(encoding="utf-8"))
    assert values["mullvad_browser_prefs"] == {
        "browser.tabs.minWidth": 88,
        "privacy.resistFingerprinting": False,
    }


def test_example_inventory_contains_optional_managed_preferences():
    example = runpy.run_path(str(ROOT / "group_data/@local.py.example"))
    assert example["mullvad_browser_prefs"] == {}
