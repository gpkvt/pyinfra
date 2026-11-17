"""Tests for the Pyinfra Manager local backend."""
# pylint: disable=E1101,C0301
import importlib.util
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[1] / "apps/pyinfra-manager/backend/manager.py"
SPEC = importlib.util.spec_from_file_location("manager_backend", MODULE)
manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager)


def test_discover_tasks_includes_core_and_nested_task_modules():
    tasks = {item["path"]: item for item in manager.discover_tasks()}
    assert "tasks/apt.py" in tasks
    assert "tasks/system.py" in tasks
    assert "tasks/workstation/cosmic/deploy.py" in tasks
    assert "tasks/workstation/backup.py" in tasks
    assert "tasks/docker/miniflux.py" in tasks


def test_config_validation_does_not_execute_python(tmp_path):
    marker = tmp_path / "executed"
    source = f"open({str(marker)!r}, 'w').write('unsafe')"
    manager.validate_config(source)
    assert not marker.exists()


def test_invalid_config_reports_syntax_error():
    with pytest.raises(manager.ManagerError, match="syntax error"):
        manager.validate_config("broken = (")


def test_save_config_is_idempotent_and_creates_private_backup(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    target = tmp_path / "@local.py"
    target.write_text("hostname = 'before'\n", encoding="utf-8")
    monkeypatch.setattr(manager, "_safe_config_path", lambda _key: target)
    assert manager.save_config("local", "hostname = 'after'\n") is True
    assert target.read_text(encoding="utf-8") == "hostname = 'after'\n"
    backup = tmp_path / "state/pyinfra-manager/backups/@local.py.bak"
    assert backup.read_text(encoding="utf-8") == "hostname = 'before'\n"
    assert backup.stat().st_mode & 0o777 == 0o600
    assert manager.save_config("local", "hostname = 'after'\n") is False


def test_save_config_refuses_to_overwrite_existing_backup(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    target = tmp_path / "workstation.py"
    target.write_text("workstation = {}\n", encoding="utf-8")
    backup = tmp_path / "state/pyinfra-manager/backups/workstation.py.bak"
    backup.parent.mkdir(parents=True)
    backup.write_text("previous", encoding="utf-8")
    monkeypatch.setattr(manager, "_safe_config_path", lambda _key: target)
    with pytest.raises(manager.ManagerError, match="Backup already exists"):
        manager.save_config("workstation", "workstation = {'cosmic': {}}\n")
