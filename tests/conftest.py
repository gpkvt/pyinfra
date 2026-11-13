# pylint: disable=E1101
"""Shared test helpers for pyinfra deployment tests."""

import builtins
import importlib.util
import json
import runpy
import subprocess
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


class Data(dict):
    """Dictionary that also supports pyinfra-style attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def load_module(path, name):
    """Load a Python file under an isolated module name."""
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OperationResult:
    """Small stand-in for pyinfra operation results."""
    changed = False

    def did_change(self):
        return False


class HostData(dict):
    """Dictionary with pyinfra-style attribute access."""
    __getattr__ = dict.__getitem__


@pytest.fixture
def task_environment(monkeypatch):
    """Install lightweight pyinfra stubs and return operation mocks."""
    calls = {"apt": [], "files": [], "server": []}

    def operation(kind):
        def record(**kwargs):
            calls[kind].append(kwargs)
        return record

    pyinfra = types.ModuleType("pyinfra")
    pyinfra.host = types.SimpleNamespace(data=Data())
    operations = types.ModuleType("pyinfra.operations")
    for name in ("apt", "files", "server"):
        module = types.ModuleType(f"pyinfra.operations.{name}")
        for function in ("packages", "template", "service"):
            setattr(module, function, operation(name))
        setattr(operations, name, module)
        monkeypatch.setitem(sys.modules, f"pyinfra.operations.{name}", module)

    monkeypatch.setitem(sys.modules, "pyinfra", pyinfra)
    monkeypatch.setitem(sys.modules, "pyinfra.operations", operations)

    def load(feature, config):
        pyinfra.host.data = Data(workstation={feature: config})
        return load_module(
            f"tasks/workstation/{feature}.py",
            f"tested_workstation_{feature}",
        )

    return calls, load


@pytest.fixture
def pyinfra_task_harness(monkeypatch):
    """Install generic pyinfra stubs and capture scheduled operations."""
    calls = []
    included = []
    result = OperationResult()
    def make_operation(namespace, name):
        def operation(**kwargs):
            calls.append((namespace, name, kwargs))
            return result
        return operation

    host_data = HostData(runpy.run_path(str(ROOT / "group_data/@local.py")))
    host_data.update({
        "docker": {},
        "caddy_config": {},
        "proton": {
            "mail": False, "bridge": False, "vpn": False,
            "pass": False, "flatpak": False, "drive_cli": False,
        },
        "apparmor_profiles": [],
        "ufw": {},
        "apt_sources": {},
        "apt_packages": [],
        "flatpak_packages": [],
        "wireguard_config": {},
    })
    def get_fact(fact, *args, **kwargs):
        name = getattr(fact, "__name__", "")
        if name in {"Directory", "File"}:
            return False
        if name == "Command":
            command = kwargs.get("command", args[0] if args else "")
            if command.strip() == "id -u" or command.startswith("id -u "):
                return "1000"
            if command.startswith("id -g "):
                return "1000"
            if "remote-list" in command:
                return ""
            return ""
        if name == "SystemLocale":
            return host_data.get("locale")
        if name == "UfwActive":
            return False
        if name == "UfwRules":
            return set()
        if name == "UfwDefaults":
            return {"incoming": "deny", "outgoing": "allow"}
        if name == "AppArmorStatus":
            return {}
        if name in {"FlatpakUpdates", "FlatpakSystemUpdates"}:
            return []
        if name == "VSCodiumExtensions":
            return set()
        if name == "CertNeedsRenewal":
            return False
        if name == "SudoersFile":
            return ""
        return False

    shell_output = types.SimpleNamespace(
        stdout_lines=[json.dumps([])],
        combined_lines=[],
        stdout="",
        stderr="",
    )
    host = types.SimpleNamespace(
        data=host_data,
        name="test-host",
        get_fact=get_fact,
        run_shell_command=lambda *args, **kwargs: (True, shell_output),
    )
    local = types.SimpleNamespace(include=included.append)
    pyinfra = types.ModuleType("pyinfra")
    pyinfra.host = host
    pyinfra.local = local
    pyinfra.logger = types.SimpleNamespace(
        debug=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
    )
    pyinfra.facts = types.ModuleType("pyinfra.facts")
    api = types.ModuleType("pyinfra.api")
    api.FactBase = type("FactBase", (), {})
    api.QuoteString = lambda value: value
    api.StringCommand = lambda *args, **kwargs: (args, kwargs)
    def decorator_factory(*_args, **_kwargs):
        def decorate(function):
            return function
        return decorate

    def operation_decorator(*_args, **_kwargs):
        def decorate(function):
            def schedule(*args, **kwargs):
                calls.append(("operation", function.__name__, kwargs))
                return result
            return schedule
        return decorate

    api.operation = operation_decorator
    api.deploy = decorator_factory
    operations = types.ModuleType("pyinfra.operations")
    for namespace in ("apt", "files", "server", "systemd", "flatpak"):
        module = types.ModuleType(f"pyinfra.operations.{namespace}")
        names = {
            "apt": ("packages", "update", "upgrade"),
            "files": (
                "directory", "download", "template", "put", "sync",
                "line", "file", "link", "unarchive",
            ),
            "server": (
                "shell", "service", "hostname", "timezone", "locale",
                "sysctl", "user", "user_authorized_keys", "etc_hosts",
            ),
            "systemd": ("service",),
            "flatpak": ("packages",),
        }[namespace]
        for name in names:
            setattr(module, name, make_operation(namespace, name))
        setattr(operations, namespace, module)
        monkeypatch.setitem(sys.modules, f"pyinfra.operations.{namespace}", module)

    util = types.ModuleType("pyinfra.operations.util")
    util.any_changed = lambda *_operations: (lambda: False)
    facts = types.ModuleType("pyinfra.facts")
    facts_files = types.ModuleType("pyinfra.facts.files")
    facts_files.Directory = type("Directory", (), {})
    facts_files.File = type("File", (), {})
    pyinfra.facts.files = facts_files
    facts_server = types.ModuleType("pyinfra.facts.server")
    facts_server.Command = type("Command", (), {})
    for name, module in (
        ("pyinfra", pyinfra),
        ("pyinfra.api", api),
        ("pyinfra.operations", operations),
        ("pyinfra.operations.util", util),
        ("pyinfra.facts", facts),
        ("pyinfra.facts.files", facts_files),
        ("pyinfra.facts.server", facts_server),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    # Task modules expect common.py to have initialized these globals.
    monkeypatch.setattr(builtins, "homedir", "/home/tester", raising=False)
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    monkeypatch.setattr(builtins, "flatpak", False, raising=False)
    def load_task(filename, data=None):
        if data:
            host.data.update(data)
        module_name = f"tested_root_task_{Path(filename).stem}"
        path = ROOT / "tasks" / filename
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return types.SimpleNamespace(
        calls=calls,
        included=included,
        host=host,
        load=load_task,
        result=result,
    )

