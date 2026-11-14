"""Tests for the opt-in Samba dropbox task and its scripts."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_samba_is_not_configured_when_disabled(pyinfra_task_harness):
    pyinfra_task_harness.load("samba.py", {"samba": {"enabled": False}})
    assert pyinfra_task_harness.calls == []


def test_samba_configures_two_distinct_shares(pyinfra_task_harness):
    pyinfra_task_harness.load("samba.py", {
        "samba": {
            "enabled": True,
            "allowed_networks": ["192.168.1.0/24"],
            "upload": {"path": "/srv/samba/incoming"},
            "download": {"path": "/srv/samba/outgoing"},
        },
    })
    rendered = [
        call[2] for call in pyinfra_task_harness.calls
        if call[0] == "files" and call[1] == "template"
        and call[2].get("dest") == "/etc/samba/smb.conf"
    ]
    assert len(rendered) == 1
    assert rendered[0]["upload_path"] == "/srv/samba/incoming"
    assert rendered[0]["download_path"] == "/srv/samba/outgoing"


@pytest.mark.parametrize("network", ["not-a-network", "192.168.1.1/99"])
def test_samba_rejects_invalid_networks(pyinfra_task_harness, network):
    with pytest.raises(ValueError, match="Invalid samba.allowed_networks"):
        pyinfra_task_harness.load("samba.py", {
            "samba": {"enabled": True, "allowed_networks": [network]},
        })


def test_samba_share_security_and_lifecycle_are_explicit():
    config = (ROOT / "templates/samba/smb.conf.j2").read_text()
    assert "[Upload]" in config and "guest ok = yes" in config
    assert "[Download]" in config and "read only = yes" in config
    assert "server min protocol = SMB2" in config
    start = (ROOT / "templates/samba/samba-start.j2").read_text()
    stop = (ROOT / "templates/samba/samba-stop.j2").read_text()
    assert "systemctl unmask smbd.service" in start
    assert "ufw show added" in start
    assert "systemctl mask smbd.service" in stop
    assert "ufw --force delete" in stop
    assert "samba-idle.timer" in stop
    assert "nft delete table inet samba_idle" in stop
    checker = (ROOT / "templates/samba/samba-idle-check.j2").read_text()
    timer = (ROOT / "templates/samba/samba-idle.timer.j2").read_text()
    assert "CURRENT_BYTES" in checker and "TIMEOUT" in checker
    assert "OnUnitActiveSec=60s" in timer


@pytest.mark.parametrize("timeout", [-1, 1.5, True])
def test_samba_rejects_invalid_idle_timeout(pyinfra_task_harness, timeout):
    with pytest.raises(ValueError, match="samba.idle_timeout"):
        pyinfra_task_harness.load("samba.py", {
            "samba": {
                "enabled": True,
                "allowed_networks": ["192.168.1.0/24"],
                "idle_timeout": timeout,
            },
        })


@pytest.mark.parametrize("timeout", [0, 1, 60, 1799, 1800])
def test_samba_accepts_non_negative_integer_idle_timeout(pyinfra_task_harness, timeout):
    pyinfra_task_harness.load("samba.py", {
        "samba": {
            "enabled": True,
            "allowed_networks": ["192.168.1.0/24"],
            "idle_timeout": timeout,
        },
    })
