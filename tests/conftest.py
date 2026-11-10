# pylint: disable=E1101
"""Shared test helpers for pyinfra deployment tests."""

import importlib.util
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
