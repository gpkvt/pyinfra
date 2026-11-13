"""Validate the isolated CI inventory fixtures."""

import runpy
from pathlib import Path


def test_ci_inventory_values_are_explicit_and_nonempty():
    inventory = runpy.run_path(
        str(Path(__file__).parents[1] / ".github" / "ci" / "inventory.py")
    )
    config = inventory["ci"][0][1]

    expected = {
        "apt_packages", "apt_sources", "hostname", "timezone", "locale",
        "editor", "visual_editor", "keyboard", "hostnames", "sudoers_rules",
        "ssh_config", "ssh_keys", "ssh_authorized_keys", "sysctl", "udev",
        "usbguard", "flatpak", "wireguard_config", "local_network_cidr",
        "wireguard_interface", "syncthing", "zsh", "powerline",
        "powerline_fonts", "ufw", "docker_install", "docker",
        "docker_sablier", "docker_power_monitor", "caddy_config",
        "apparmor_profiles",  "mullvad_extensions", "vscodium",
        "proton", "cron_jobs", "workstation",
    }

    assert expected <= config.keys()
    for key in expected:
        value = config[key]
        assert value is not None, key
        assert value != "", key
        assert value != [], key
        assert value != {}, key


def test_ci_inventory_gates_runner_unsafe_features():
    inventory = runpy.run_path(
        str(Path(__file__).parents[1] / ".github" / "ci" / "inventory.py")
    )
    config = inventory["ci"][0][1]

    assert config["ssh_authorized_keys_enabled"] is False
    assert config["wireguard_enabled"] is False
    assert config["vpn_enabled"] is False
    assert config["syncthing"]["enabled"] is False
    assert config["ufw"]["enabled"] is False
    assert config["caddy_enabled"] is False
    assert config["apparmor_enabled"] is False
    assert config["mullvad_browser_enabled"] is False
    assert config["vscodium_enabled"] is False
    assert all(value is False for value in config["proton"].values())
