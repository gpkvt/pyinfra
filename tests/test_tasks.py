# pylint: disable=R0914, W0613, E1101, R0915, W0621, R0911
"""Smoke and focused regression tests for top-level deployment tasks.

These tests deliberately mock pyinfra's host and operation APIs. They verify
that task modules can be evaluated and that selected helpers/facts preserve
important behavior without contacting or modifying a real machine.
"""

import builtins
import importlib.util
import json
import runpy
import sys
import types
from pathlib import Path

import pytest

from conftest import ROOT


class OperationResult:
    """Small stand-in for pyinfra operation results."""

    changed = False
    did_change = False


class HostData(dict):
    """Dictionary with pyinfra-style attribute access."""

    __getattr__ = dict.__getitem__


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
            command = kwargs.get("command", "")
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


ROOT_TASKS = sorted(
    path.name for path in (ROOT / "tasks").glob("*.py")
    if path.name != "__init__.py"
)


@pytest.mark.parametrize("task_name", ROOT_TASKS)
def test_top_level_task_module_loads_with_mocked_pyinfra(pyinfra_task_harness, task_name):
    """Every top-level task should be importable without a real pyinfra host."""
    pyinfra_task_harness.load(task_name)


def test_apt_update_helper_forces_update_when_repository_changed(pyinfra_task_harness):
    module = pyinfra_task_harness.load("apt.py")
    changed_operation = OperationResult()
    forced, cached = module.update_apt_sources([changed_operation])

    assert forced is not None
    assert cached is not None
    apt_updates = [
        call for call in pyinfra_task_harness.calls
        if call[0] == "apt" and call[1] == "update"
    ]
    assert any(call[2]["name"] == "Force APT update (repositories changed)"
               for call in apt_updates)
    assert any(call[2].get("cache_time") == 14400 for call in apt_updates)


def test_hosts_task_schedules_each_configured_mapping(pyinfra_task_harness):
    pyinfra_task_harness.load("hosts.py", {
        "hostnames": {"192.0.2.10": "example.test alias.test"},
    })

    calls = [call for call in pyinfra_task_harness.calls if call[1] == "etc_hosts"]
    assert len(calls) == 1
    assert calls[0][2]["ip"] == "192.0.2.10"
    assert calls[0][2]["hostnames"] == "example.test alias.test"


def test_docker_container_includes_only_configured_services(pyinfra_task_harness):
    pyinfra_task_harness.load("docker_container.py", {
        "docker": {"miniflux": {}, "grav": {}},
    })

    assert pyinfra_task_harness.included == [
        "tasks/docker/miniflux.py",
        "tasks/docker/grav.py",
    ]


def test_vscodium_rejects_invalid_extension_configuration(pyinfra_task_harness):
    with pytest.raises(ValueError, match="Invalid VSCodium extension ID"):
        pyinfra_task_harness.load("vscodium.py", {
            "vscodium": {"extensions": ["not-an-extension"]},
        })


def test_vscodium_deduplicates_extensions_and_installs_missing_ids(pyinfra_task_harness):
    pyinfra_task_harness.load("vscodium.py", {
        "vscodium": {"extensions": ["vendor.extension", "vendor.extension"]},
    })

    installs = [
        call for call in pyinfra_task_harness.calls
        if call[1] == "shell" and "Install VSCodium extension" in call[2].get("name", "")
    ]
    assert len(installs) == 1
    assert "vendor.extension" in installs[0][2]["commands"][0]


def test_system_locale_fact_parses_lang_value(pyinfra_task_harness):
    module = pyinfra_task_harness.load("system.py")
    assert module.SystemLocale().process(['LANG="en_GB.UTF-8"']) == "en_GB.UTF-8"
    assert module.SystemLocale().process(["# no locale configured"]) is None


def test_dehydrated_fact_reports_expiring_certificates(pyinfra_task_harness):
    module = pyinfra_task_harness.load("dehydrated.py")
    assert module.CertNeedsRenewal().process(["false"]) is False
    assert module.CertNeedsRenewal().process(["true"]) is True


def test_flatpak_facts_ignore_blank_output_lines(pyinfra_task_harness):
    module = pyinfra_task_harness.load("flatpak.py")
    assert module.FlatpakUpdates().process(["app.one", "", " app.two "]) == [
        "app.one", " app.two ",
    ]
    assert module.FlatpakSystemUpdates().process([""]) == []


def test_ufw_fact_parsers_and_rule_matching(pyinfra_task_harness):
    module = pyinfra_task_harness.load("ufw.py")

    assert module.UfwActive().process(["Status: active"]) is True
    assert module.UfwActive().process(["Status: inactive"]) is False
    assert module.UfwRules().process([
        "Status: active", "To                         Action      From",
        "22/tcp                     ALLOW IN    Anywhere",
    ]) == {"22/tcp                     ALLOW IN    Anywhere"}
    assert module.UfwDefaults().process([
        "Default: deny (incoming), allow (outgoing), disabled (routed)",
    ]) == {"incoming": "deny", "outgoing": "allow", "routed": "disabled"}

    pyinfra_task_harness.host.get_fact = lambda *_args, **_kwargs: {
        "22/tcp ALLOW Anywhere",
    }
    assert module.ufw_rule_exists("22/tcp") is True
    assert module.ufw_rule_exists("80/tcp") is False


def test_apparmor_fact_parses_json_profiles(pyinfra_task_harness):
    module = pyinfra_task_harness.load("apparmor.py")
    assert module.AppArmorStatus().process(['{"profiles": {"/usr/bin/foo": "enforce"}}']) == {
        "/usr/bin/foo": "enforce",
    }


def test_sudoers_fact_preserves_file_content_with_trailing_newline(pyinfra_task_harness):
    module = pyinfra_task_harness.load("sudo.py")
    assert module.SudoersFile().process(["Defaults timestamp_timeout=10"]) == (
        "Defaults timestamp_timeout=10\n"
    )
    assert module.SudoersFile().process([]) == ""


def test_wireguard_skips_service_when_host_is_on_local_network(pyinfra_task_harness):
    output = types.SimpleNamespace(stdout_lines=[json.dumps([
        {"addr_info": [{"family": "inet", "local": "192.168.42.25"}]},
    ])])
    pyinfra_task_harness.host.run_shell_command = lambda *args, **kwargs: (True, output)
    pyinfra_task_harness.load("vpn.py")

    service_calls = [
        call for call in pyinfra_task_harness.calls
        if call[0] == "server" and call[1] == "service"
    ]
    assert len(service_calls) == 1
    assert service_calls[0][2]["service"] == "wg-quick@home"
    assert service_calls[0][2]["_if"]() is False


def test_wireguard_raises_when_interface_discovery_fails(pyinfra_task_harness):
    pyinfra_task_harness.host.run_shell_command = lambda *args, **kwargs: (False, None)
    with pytest.raises(RuntimeError, match="Unable to retrieve network interfaces"):
        pyinfra_task_harness.load("vpn.py")



def test_sablier_caddy_routes_only_wrap_configured_docker_services(pyinfra_task_harness):
    """Only configured Docker reverse proxies should be routed through Sablier."""
    module = pyinfra_task_harness.load("caddy.py")
    config = {
        "linkwarden.example:443": {"reverse_proxy": "127.0.0.1:8021"},
        "fints.example:443": {"reverse_proxy": "127.0.0.1:8024"},
        "external.example:443": {"reverse_proxy": "127.0.0.1:9000"},
        "custom.example:443": {"reverse_proxy": "127.0.0.1:8123"},
        "custom-extra.example:443": {"reverse_proxy": "127.0.0.1:8124"},
    }
    docker = {
        "linkwarden": {"port": 8021},
        "firefly-iii": {"port": 8023, "fints_port": 8024},
        "custom": {"port": 8123, "metrics_port": 8124},
    }
    result = module.build_sablier_caddy_config(
        config,
        docker,
        {"enabled": True, "default_duration": "45m", "blocking_timeout": "3m"},
    )

    assert "route" in result["linkwarden.example:443"]
    assert "route" in result["fints.example:443"]
    assert "route" in result["custom.example:443"]
    assert "route" in result["custom-extra.example:443"]
    assert result["external.example:443"]["reverse_proxy"] == "127.0.0.1:9000"
    assert (
        result["fints.example:443"]["route"]
        ["sablier http://127.0.0.1:10000"]["group"]
        == "firefly-iii"
    )
    assert "reverse_proxy" in config["linkwarden.example:443"]


def test_docker_service_app_services_come_from_service_configuration(pyinfra_task_harness):
    """Systemd unit receives app services from Docker config, with a generic fallback."""
    module = pyinfra_task_harness.load("docker.py", {
        "docker_sablier": {"enabled": True},
        "docker": {
            "custom": {"app_services": ["worker", "scheduler"]},
            "generic": {},
        },
    })

    module.deploy_docker_service("custom", "Custom", "/home/tester")
    module.deploy_docker_service("generic", "Generic", "/home/tester")

    unit_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("src") == "templates/docker/systemd.service.j2"
    ]
    assert [call["app_services"] for call in unit_calls] == [
        ["worker", "scheduler"],
        ["generic"],
    ]



def test_dehydrated_domains_support_multiple_certificates_and_sans(pyinfra_task_harness):
    module = pyinfra_task_harness.load("caddy.py")
    assert module.build_domains_file([
        ["21x9.org", "*.21x9.org"],
        ["example.com", "www.example.com", "api.example.com"],
    ]) == [
        "21x9.org *.21x9.org",
        "example.com www.example.com api.example.com",
    ]


def test_dehydrated_domains_reject_empty_or_duplicate_definitions(pyinfra_task_harness):
    module = pyinfra_task_harness.load("caddy.py")
    with pytest.raises(ValueError, match="at least one certificate"):
        module.build_domains_file([])
    with pytest.raises(ValueError, match="more than one certificate"):
        module.build_domains_file([
            ["example.com", "www.example.com"],
            ["example.net", "www.example.com"],
        ])
    with pytest.raises(ValueError, match="Invalid domain"):
        module.build_domains_file([["not a domain"]])
