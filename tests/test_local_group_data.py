"""Tests for portable, non-machine-specific group-data examples."""

import runpy

from conftest import ROOT


def test_local_example_has_safe_portable_defaults():
    """The local example contains placeholders and no live host configuration."""
    data = runpy.run_path(str(ROOT / "group_data/@local.py.example"))

    assert data["hostname"] == "example-host"
    assert data["username"] == "YOUR_USERNAME"
    assert data["usergroup"] == "YOUR_USERNAME"
    assert data["homedir"] == "/home/YOUR_USERNAME"
    assert data["timezone"] == "Etc/UTC"
    assert data["locale"] == "en_US.UTF-8"
    assert data["keyboard"]["layout"] == "us"
    assert data["apt_packages"] == []
    assert data["apt_sources"] == {}
    assert data["flatpak_packages"] == []
    assert data["hostnames"] == {}
    assert data["wireguard_config"] == {}
    assert data["wireguard_enabled"] is True
    assert data["vpn_enabled"] is True
    assert data["docker"] == {}
    assert data["docker_power_monitor"] is True
    assert data["caddy_enabled"] is True
    assert data["apparmor_enabled"] is True
    assert data["mullvad_browser_enabled"] is True
    assert data["vscodium_enabled"] is True
    assert data["proton"] == {"drive_cli_version": "0.9.0"}
    assert data["ufw"] == {}


def test_workstation_example_disables_machine_specific_features_by_default():
    """Workstation features require explicit opt-in and hardware selection."""
    data = runpy.run_path(str(ROOT / "group_data/workstation.py.example"))
    config = data["workstation"]

    assert {
        "backup", "power", "hardware", "storage", "peripherals",
        "desktop", "maintenance", "limusic",
    } <= config.keys()
    assert all(section["enabled"] is False for section in config.values())
    assert config["hardware"]["cpu_vendor"] is None
    assert config["peripherals"]["printing"] is False
    assert config["peripherals"]["scanning"] is False
    assert "applets" not in config["cosmic"]["panel"]
    assert "applets" not in config["cosmic"]["dock"]

    # Omitting applet overrides preserves the defaults in the panel/dock tasks.
    assert "applets" not in config["cosmic"]["panel"]
    assert "applets" not in config["cosmic"]["dock"]


def test_machine_specific_configuration_files_are_ignored():
    """Real per-machine files are excluded while examples remain trackable."""
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "group_data/@local.py" in ignored
    assert "group_data/workstation.py" in ignored
    assert (ROOT / "group_data/@local.py.example").is_file()
    assert (ROOT / "group_data/workstation.py.example").is_file()
