# pylint: disable=C1803, E1101
"""Tests for shared deployment initialization and host secret selection."""

import builtins
import json
import subprocess
import sys
import types

import pytest

from conftest import load_module


def install_pyinfra_fact_stubs(monkeypatch):
    pyinfra = types.ModuleType("pyinfra")
    facts = types.ModuleType("pyinfra.facts")
    files = types.ModuleType("pyinfra.facts.files")
    server = types.ModuleType("pyinfra.facts.server")
    files.File = type("File", (), {})
    server.Command = type("Command", (), {})
    server.Which = type("Which", (), {})
    for name, module in (
        ("pyinfra", pyinfra),
        ("pyinfra.facts", facts),
        ("pyinfra.facts.files", files),
        ("pyinfra.facts.server", server),
    ):
        monkeypatch.setitem(sys.modules, name, module)



def test_command_output_text_normalizes_fact_lines_and_empty_values(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_command_output")

    assert common.command_output_text(["first", "second"]) == "first\nsecond"
    assert common.command_output_text(["one"]) == "one"
    assert common.command_output_text([]) == ""
    assert common.command_output_text(None) == ""
    assert common.command_output_text("already text") == "already text"




def test_initialize_without_secrets_sets_empty_dictionary(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_no_secrets")
    host = types.SimpleNamespace(
        name="test-host",
        get_fact=lambda *_args, **_kwargs: None,
        data={"homedir": "/home/tester"},
    )

    monkeypatch.setattr(common.shutil, "which", lambda _command: None)

    common.initialize(host, check_flatpak=True)

    assert builtins.secrets == {}
    assert builtins.homedir == "/home/tester"
    assert builtins.flatpak is None


def test_initialize_decrypts_and_selects_host_secrets(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_with_secrets")
    monkeypatch.setattr(common.Path, "is_file", lambda _path: True)
    secret_data = {
        "shared": {"git_credentials": ["https://example.test/shared"]},
        "hosts": {
            "test-host": {"wireguard": {"home": {"privatekey": "host-key"}}},
            "other-host": {"wireguard": {"home": {"privatekey": "other-key"}}},
        },
    }
    host = types.SimpleNamespace(
        name="test-host",
        get_fact=lambda *_args, **_kwargs: True,
        data={"hostname": "test-host"},
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: types.SimpleNamespace(stdout=json.dumps(secret_data)),
    )

    common.initialize(host)

    assert builtins.secrets == {
        "git_credentials": ["https://example.test/shared"],
        "wireguard": {"home": {"privatekey": "host-key"}},
    }
    assert builtins.homedir == "/root/"


def test_select_host_secrets_recursively_merges_host_over_shared(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_merge")
    data = {
        "shared": {
            "docker": {
                "miniflux": {"admin_username": "shared-user", "admin_password": "shared-pass"},
                "vaultwarden": {"admin_token": "shared-token"},
            },
            "git_credentials": ["shared-credential"],
        },
        "hosts": {
            "host-a": {
                "docker": {
                    "miniflux": {"admin_password": "host-pass"},
                },
                "git_credentials": ["host-credential"],
            },
        },
    }

    assert common.select_host_secrets(data, "host-a") == {
        "docker": {
            "miniflux": {"admin_username": "shared-user", "admin_password": "host-pass"},
            "vaultwarden": {"admin_token": "shared-token"},
        },
        "git_credentials": ["host-credential"],
    }
    assert common.select_host_secrets(data, "host-b") == data["shared"]


def test_select_host_secrets_falls_back_to_inventory_alias(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_inventory_alias")
    data = {
        "shared": {"docker": {"miniflux": {"shared_value": "shared"}}},
        "hosts": {
            "@local": {
                "docker": {
                    "miniflux": {
                        "postgres_password": "local-db-password",
                        "admin_username": "local-admin",
                        "admin_password": "local-admin-password",
                    }
                }
            }
        },
    }

    selected = common.select_host_secrets(data, "chao", "@local")

    assert selected["docker"]["miniflux"] == {
        "shared_value": "shared",
        "postgres_password": "local-db-password",
        "admin_username": "local-admin",
        "admin_password": "local-admin-password",
    }


def test_select_host_secrets_prefers_hostname_over_inventory_alias(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_hostname_precedence")
    data = {
        "hosts": {
            "chao": {"docker": {"miniflux": {"admin_username": "hostname-user"}}},
            "@local": {"docker": {"miniflux": {"admin_username": "alias-user"}}},
        }
    }

    selected = common.select_host_secrets(data, "chao", "@local")

    assert selected["docker"]["miniflux"]["admin_username"] == "hostname-user"


def test_select_host_secrets_uses_alias_during_initialize(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_initialize_alias")
    monkeypatch.setattr(common.Path, "is_file", lambda _path: True)
    secret_data = {"hosts": {"@local": {"docker": {"miniflux": {
        "postgres_password": "db-password",
        "admin_username": "admin",
        "admin_password": "admin-password",
    }}}}}
    host = types.SimpleNamespace(
        name="@local",
        get_fact=lambda *_args, **_kwargs: True,
        data={"hostname": "chao"},
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: types.SimpleNamespace(stdout=json.dumps(secret_data)),
    )

    common.initialize(host)

    assert builtins.secrets["docker"]["miniflux"]["postgres_password"] == "db-password"
    assert builtins.secrets["docker"]["miniflux"]["admin_username"] == "admin"
    assert builtins.secrets["docker"]["miniflux"]["admin_password"] == "admin-password"


def test_select_host_secrets_preserves_legacy_flat_structure(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_legacy")
    legacy = {"wireguard": {"home": {"privatekey": "legacy-key"}}}

    assert common.select_host_secrets(legacy, "test-host") == legacy


@pytest.mark.parametrize("data", [[], "invalid", None])
def test_select_host_secrets_rejects_non_object_document(monkeypatch, data):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_invalid_document")

    with pytest.raises(ValueError, match="expected a JSON object"):
        common.select_host_secrets(data, "test-host")


def test_select_host_secrets_rejects_invalid_sections(monkeypatch):
    install_pyinfra_fact_stubs(monkeypatch)
    common = load_module("common.py", "tested_common_invalid_sections")

    with pytest.raises(ValueError, match="'shared' must be an object"):
        common.select_host_secrets({"shared": [], "hosts": {}}, "test-host")
    with pytest.raises(ValueError, match="'hosts' must be an object"):
        common.select_host_secrets({"shared": {}, "hosts": []}, "test-host")
    with pytest.raises(ValueError, match="Invalid secrets for host"):
        common.select_host_secrets({"hosts": {"test-host": []}}, "test-host")
