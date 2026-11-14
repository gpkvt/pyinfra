"""Validation tests for WireGuard interface configuration."""

import builtins

import pytest


@pytest.mark.parametrize("interface", ["../escape", "interface/name", "way-too-long-interface"])
def test_wireguard_rejects_invalid_interface_names(
    pyinfra_task_harness, monkeypatch, interface,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"wireguard": {interface: {"privatekey": "private", "peers": []}}},
        raising=False,
    )
    with pytest.raises(ValueError, match="Invalid WireGuard interface name"):
        pyinfra_task_harness.load("wireguard.py", {
            "wireguard_config": {interface: {"interface": {"Address": ["10.0.0.2/32"]}}},
        })


def test_wireguard_rejects_missing_interface_secrets(pyinfra_task_harness, monkeypatch):
    monkeypatch.setattr(builtins, "secrets", {"wireguard": {}}, raising=False)
    with pytest.raises(ValueError, match="Missing WireGuard secrets"):
        pyinfra_task_harness.load("wireguard.py", {
            "wireguard_config": {
                "wg0": {"interface": {"Address": ["10.0.0.2/32"]}},
            },
        })


def test_wireguard_rejects_missing_private_key(pyinfra_task_harness, monkeypatch):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"wireguard": {"wg0": {"peers": []}}},
        raising=False,
    )
    with pytest.raises(ValueError, match="requires a privatekey"):
        pyinfra_task_harness.load("wireguard.py", {
            "wireguard_config": {
                "wg0": {"interface": {"Address": ["10.0.0.2/32"]}},
            },
        })


def test_wireguard_deploys_valid_interface_with_matching_secret(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"wireguard": {"wg0": {"privatekey": "private", "peers": []}}},
        raising=False,
    )
    pyinfra_task_harness.load("wireguard.py", {
        "wireguard_config": {
            "wg0": {"interface": {"Address": ["10.0.0.2/32"]}},
        },
    })
    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("dest") == "/etc/wireguard/wg0.conf"
    )
    assert operation["secrets"] == {"privatekey": "private", "peers": []}
