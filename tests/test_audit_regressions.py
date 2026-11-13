"""Regression tests for pyinfra API use and task idempotency."""

import builtins
import json
from pathlib import Path
import sys
import types

import pytest


def test_proton_drive_cli_uses_configured_version(pyinfra_task_harness):
    """The configured version determines the Proton Drive download URL."""
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "9.8.7",
        },
    })

    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Proton Drive CLI"
    )
    assert "https://proton.me/download/drive/cli/9.8.7/linux-x64/proton-drive" in install["commands"][0]


def test_proton_drive_cli_skips_install_when_requested_version_is_current(
    pyinfra_task_harness,
):
    pyinfra_task_harness.host.get_fact = (
        lambda _fact, command, **_kwargs: "9.8.7"
        if "/usr/local/share/proton-drive/version" in command
        else ""
    )
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "9.8.7",
        },
    })

    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Proton Drive CLI"
    )
    assert install["_if"]() is False


def test_proton_drive_cli_rejects_invalid_version(pyinfra_task_harness):
    with pytest.raises(ValueError, match="Invalid Proton Drive CLI version"):
        pyinfra_task_harness.load("proton.py", {
            "proton": {
                "mail": False,
                "bridge": False,
                "vpn": False,
                "pass": False,
                "flatpak": False,
                "drive_cli": True,
                "drive_cli_version": "0.9.0; touch /tmp/pwned",
            },
        })


def test_udev_reload_uses_execute_phase_change_detection(pyinfra_task_harness):
    """udevadm reload is gated by the actual file operation result."""
    pyinfra_task_harness.load("system.py", {
        "udev": {"99-example.rules": "SUBSYSTEM==\\\"usb\\\", MODE=\\\"0660\\\""},
    })
    reload = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload udev rules"
    )
    assert reload["_if"]() is False
    pyinfra_task_harness.result.changed = True
    assert reload["_if"]() is True


def test_timetagger_requires_credentials_and_passes_compose_escaped_hash(
    pyinfra_task_harness, monkeypatch,
):
    captured = {}
    docker_module = types.ModuleType("tasks.docker")
    docker_module.deploy_docker_service = lambda **kwargs: captured.update(kwargs)
    monkeypatch.setitem(sys.modules, "tasks.docker", docker_module)
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"docker": {"timetagger": {"credentials": "tester:$2a$08$hash"}}},
        raising=False,
    )
    pyinfra_task_harness.load("docker/timetagger.py", {
        "docker": {"timetagger": {}},
        "username": "tester",
        "usergroup": "tester",
        "homedir": "/home/tester",
    })

    assert captured["service"] == "timetagger"
    assert captured["credentials"] == (
        "tester:" + "$" * 2 + "2a" + "$" * 2 + "08" + "$" * 2 + "hash"
    )


def test_timetagger_rejects_missing_credentials(pyinfra_task_harness, monkeypatch):
    monkeypatch.delitem(sys.modules, "tasks.docker", raising=False)
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    with pytest.raises(ValueError, match="credentials must be a single-line"):
        pyinfra_task_harness.load("docker/timetagger.py", {
            "docker": {"timetagger": {}},
        })

def test_system_timezone_is_skipped_when_already_configured(pyinfra_task_harness):
    """An already-correct timezone does not schedule a change."""
    pyinfra_task_harness.host.get_fact = lambda fact, **_kwargs: (
        "UTC" if fact.__name__ == "Timezone" else None
    )
    pyinfra_task_harness.load("system.py", {"timezone": "UTC"})

    assert not any(
        namespace == "server" and name == "timezone"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )


def test_system_timezone_is_set_when_it_differs(pyinfra_task_harness):
    """A mismatched timezone still schedules the required correction."""
    pyinfra_task_harness.host.get_fact = lambda _fact, **_kwargs: "Europe/Berlin"
    pyinfra_task_harness.load("system.py", {"timezone": "UTC"})

    assert any(
        namespace == "server" and name == "timezone"
        and kwargs["timezone"] == "UTC"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_powerline_fonts_extract_and_refresh_only_after_archive_changes(
    pyinfra_task_harness,
):
    pyinfra_task_harness.load("fonts.py", {"powerline_fonts": True})
    extraction = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "unarchive"
        and kwargs.get("name") == "Extract Powerline fonts"
    )
    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Powerline fonts"
    )
    refresh = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Refresh font cache"
    )

    assert extraction["creates"].endswith("/fonts-master/fonts")
    assert install["_if"]() is False
    assert refresh["_if"]() is False
    pyinfra_task_harness.result.changed = True
    assert install["_if"]() is True
    assert refresh["_if"]() is True


def test_encrypted_secrets_example_is_valid_json_and_documents_timetagger():
    example = Path(__file__).resolve().parents[1] / "secrets.json.gpg.example"
    secrets = json.loads(example.read_text(encoding="utf-8"))

    assert secrets["hosts"]["@local"]["docker"]["timetagger"]["credentials"]
