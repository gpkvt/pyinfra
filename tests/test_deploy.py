# pylint: disable=W0613
"""Tests for conditional workstation task orchestration in deploy.py."""

import builtins
import sys
import types

from conftest import Data, load_module


def run_deploy(monkeypatch, workstation, cron_jobs=None):
    included = []
    data = Data(
        ssh_config=False,
        workstation=workstation,
        cron_jobs=cron_jobs or [],
    )
    host = types.SimpleNamespace(data=data)
    local = types.SimpleNamespace(include=included.append)

    pyinfra = types.ModuleType("pyinfra")
    pyinfra.host = host
    pyinfra.local = local

    common = types.ModuleType("common")

    def initialize(_host, check_flatpak=False):
        builtins.flatpak = False
        builtins.secrets = {}

    common.initialize = initialize
    monkeypatch.setitem(sys.modules, "pyinfra", pyinfra)
    monkeypatch.setitem(sys.modules, "common", common)
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    monkeypatch.setattr(builtins, "flatpak", False, raising=False)

    load_module("deploy.py", "tested_deploy")
    return included


def test_deploy_includes_only_enabled_workstation_features(monkeypatch):
    included = run_deploy(
        monkeypatch,
        {
            "backup": {"enabled": True},
            "power": {"enabled": False},
            "hardware": {"enabled": True},
            "desktop": {},
        },
    )

    assert "tasks/workstation/backup.py" in included
    assert "tasks/workstation/hardware.py" in included
    assert not any("tasks/workstation/power.py" in path for path in included)
    assert not any("tasks/workstation/desktop.py" in path for path in included)


def test_deploy_does_not_include_workstation_tasks_when_group_data_missing(monkeypatch):
    included = run_deploy(monkeypatch, {})

    assert not any(path.startswith("tasks/workstation/") for path in included)


def test_deploy_keeps_core_tasks_enabled(monkeypatch):
    included = run_deploy(monkeypatch, {})

    for path in (
        "tasks/apt.py",
        "tasks/hosts.py",
        "tasks/system.py",
        "tasks/git.py",
    ):
        assert path in included



def test_deploy_includes_cron_task_only_when_jobs_are_configured(monkeypatch):
    without_jobs = run_deploy(monkeypatch, {}, cron_jobs=[])
    assert "tasks/cron.py" not in without_jobs

    with_jobs = run_deploy(
        monkeypatch,
        {},
        cron_jobs=[{
            "name": "daily",
            "command": "/usr/local/bin/daily",
            "special_time": "@daily",
        }],
    )
    assert "tasks/cron.py" in with_jobs
