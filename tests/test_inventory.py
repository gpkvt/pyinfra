"""Tests for inventory and workstation group data."""

import runpy

from conftest import ROOT


def test_workstation_group_contains_local_host():
    inventory = runpy.run_path(str(ROOT / "inventory.py"))

    assert inventory["workstation"] == ["@local"]
    assert any(hostname == "@local" for hostname, _options in inventory["production"])


def test_disabled_hosts_are_excluded_from_production():
    inventory = runpy.run_path(str(ROOT / "inventory.py"))

    production_hosts = {hostname for hostname, _options in inventory["production"]}
    assert production_hosts.isdisjoint(inventory["disabled_hosts"])


def test_workstation_group_data_has_expected_features_and_defaults():
    group_data = runpy.run_path(str(ROOT / "group_data/workstation.py"))
    workstation = group_data["workstation"]

    expected_features = {
        "backup", "power", "hardware", "storage",
        "peripherals", "desktop", "maintenance",
    }
    assert set(workstation) == expected_features
    assert all(isinstance(config["enabled"], bool) for config in workstation.values())
    assert workstation["power"]["manager"] in {
        "power-profiles-daemon", "tlp",
    }
    assert workstation["hardware"]["cpu_vendor"] in {"intel", "amd"}
