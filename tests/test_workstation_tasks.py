"""Unit tests for workstation task selection and validation."""

import pytest


def test_disabled_feature_does_not_schedule_operations(task_environment):
    calls, load = task_environment
    load("storage", {"enabled": False})

    assert calls["apt"] == []


def test_hardware_installs_amd_microcode(task_environment):
    calls, load = task_environment
    load("hardware", {"enabled": True, "cpu_vendor": "amd"})

    assert calls["apt"][0]["packages"] == ["fwupd", "amd64-microcode"]


def test_hardware_installs_intel_microcode(task_environment):
    calls, load = task_environment
    load("hardware", {"enabled": True, "cpu_vendor": "intel"})

    assert calls["apt"][0]["packages"] == ["fwupd", "intel-microcode"]


def test_hardware_rejects_unknown_cpu_vendor(task_environment):
    _calls, load = task_environment

    with pytest.raises(ValueError, match="cpu_vendor"):
        load("hardware", {"enabled": True, "cpu_vendor": "arm"})


@pytest.mark.parametrize(
    ("manager", "expected_package", "conflicting_package"),
    [
        ("tlp", "tlp", "power-profiles-daemon"),
        ("power-profiles-daemon", "power-profiles-daemon", "tlp"),
    ],
)
def test_power_installs_selected_manager_and_removes_alternative(
    task_environment, manager, expected_package, conflicting_package
):
    calls, load = task_environment
    load("power", {"enabled": True, "manager": manager})

    assert calls["apt"][0]["packages"] == [expected_package]
    assert calls["apt"][1]["packages"] == [conflicting_package]
    assert calls["apt"][1]["present"] is False
    assert calls["server"][0]["service"] == manager


def test_power_rejects_unknown_manager(task_environment):
    _calls, load = task_environment

    with pytest.raises(ValueError, match="power.manager"):
        load("power", {"enabled": True, "manager": "unknown"})


def test_desktop_uses_default_packages(task_environment):
    calls, load = task_environment
    load("desktop", {"enabled": True})

    assert calls["apt"][0]["packages"] == [
        "xdg-utils", "xdg-user-dirs", "xdg-user-dirs-gtk",
    ]


def test_desktop_accepts_custom_packages(task_environment):
    calls, load = task_environment
    load("desktop", {"enabled": True, "packages": ["my-desktop-tool"]})

    assert calls["apt"][0]["packages"] == ["my-desktop-tool"]


@pytest.mark.parametrize("packages", ["not-a-list", ["", "valid"], [1]])
def test_desktop_rejects_invalid_package_configuration(task_environment, packages):
    _calls, load = task_environment

    with pytest.raises(ValueError, match="desktop.packages"):
        load("desktop", {"enabled": True, "packages": packages})


def test_peripherals_do_nothing_when_neither_option_is_enabled(task_environment):
    calls, load = task_environment
    load("peripherals", {"enabled": True, "printing": False, "scanning": False})

    assert calls["apt"] == []
    assert calls["server"] == []


def test_peripherals_install_and_enable_printing(task_environment):
    calls, load = task_environment
    load("peripherals", {"enabled": True, "printing": True, "scanning": False})

    assert calls["apt"][0]["packages"] == [
        "cups", "cups-client", "system-config-printer",
    ]
    assert calls["server"][0]["service"] == "cups"
    assert calls["server"][0]["enabled"] is True


def test_peripherals_install_scanning_without_printing_service(task_environment):
    calls, load = task_environment
    load("peripherals", {"enabled": True, "printing": False, "scanning": True})

    assert calls["apt"][0]["packages"] == ["sane-utils", "simple-scan"]
    assert calls["server"] == []


def test_backup_installs_tools_and_deploys_config(task_environment):
    calls, load = task_environment
    load("backup", {"enabled": True})

    assert calls["apt"][0]["packages"] == [
        "restic", "borgbackup", "rsync", "borgmatic",
    ]
    assert calls["files"][0]["dest"] == "/etc/borgmatic/config.yaml"


def test_storage_installs_health_tools(task_environment):
    calls, load = task_environment
    load("storage", {"enabled": True})

    assert calls["apt"][0]["packages"] == ["smartmontools", "nvme-cli"]


def test_maintenance_installs_utilities_without_scheduling_reboots(task_environment):
    calls, load = task_environment
    load("maintenance", {"enabled": True})

    assert calls["apt"][0]["packages"] == [
        "needrestart", "debian-goodies", "apt-file",
    ]
    assert calls["server"] == []
