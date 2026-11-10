# pylint: disable=C1803, E1101
"""Tests for shared deployment initialization."""

import builtins
import json
import subprocess
import sys
import types

from conftest import load_module


def install_pyinfra_fact_stubs(monkeypatch):
    pyinfra = types.ModuleType("pyinfra")
    facts = types.ModuleType("pyinfra.facts")
    files = types.ModuleType("pyinfra.facts.files")
    server = types.ModuleType("pyinfra.facts.server")
    files.File = type("File", (), {})
    server.Which = type("Which", (), {})
    for name, module in (
        ("pyinfra", pyinfra),
        ("pyinfra.facts", facts),
        ("pyinfra.facts.files", files),
        ("pyinfra.facts.server", server),
    ):
        monkeypatch.setitem(sys.modules, name, module)


def test_initialize_without_secrets_sets_empty_dictionary(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_no_secrets")
    host = types.SimpleNamespace(
        get_fact=lambda *_args, **_kwargs: None,
        data={"homedir": "/home/tester"},
    )

    common.initialize(host, check_flatpak=True)

    assert builtins.secrets == {}
    assert builtins.homedir == "/home/tester"
    assert builtins.flatpak is None


def test_initialize_decrypts_secrets(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_with_secrets")
    secret_data = {"wireguard": {"private_key": "example"}}
    host = types.SimpleNamespace(
        get_fact=lambda *_args, **_kwargs: True,
        data={},
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: types.SimpleNamespace(stdout=json.dumps(secret_data)),
    )

    common.initialize(host)

    assert builtins.secrets == secret_data
    assert builtins.homedir == "/root/"
