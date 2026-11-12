# pylint: disable=R0912, R0914, W0613, E1101, R0915, W0621, R0911
"""Smoke and focused regression tests for top-level deployment tasks.

These tests deliberately mock pyinfra's host and operation APIs. They verify
that task modules can be evaluated and that selected helpers/facts preserve
important behavior without contacting or modifying a real machine.
"""

import builtins
import importlib.util
import json
import os
import runpy
import subprocess
import sys
import types
from pathlib import Path

import pytest

from conftest import ROOT


class OperationResult:
    """Small stand-in for pyinfra operation results."""

    changed = False
    def did_change(self):
        return False


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
        result["fints.example:443"]["route"]["handle"]
        ["sablier http://127.0.0.1:10000"]["group"]
        == "firefly-iii"
    )
    assert "reverse_proxy" in config["linkwarden.example:443"]


def test_docker_service_app_services_come_from_service_configuration(pyinfra_task_harness):
    """Systemd unit receives app services from Docker config, with a generic fallback."""
    module = pyinfra_task_harness.load("docker.py", {
        "docker_sablier": {"enabled": True},
        "docker": {
            "custom": {
                "app_services": ["worker", "scheduler"],
                "sablier_services": ["worker", "scheduler", "database"],
            },
            "generic": {},
        },
    })

    pyinfra_task_harness.host.get_fact = lambda _fact, command="", **_kwargs: (
        "1000" if command.startswith("id -u")
        else ("worker scheduler database" if "/custom/" in command else "generic")
    ) if "config --services" in command or command.startswith("id -u") else ""

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
    override_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("src") == "templates/docker/sablier-override.yml.j2"
    ]
    assert [call["sablier_services"] for call in override_calls] == [
        ["database", "scheduler", "worker"],
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

def test_docker_service_treats_missing_systemd_status_as_inactive(pyinfra_task_harness):
    """A missing Command fact must not abort Docker service deployment."""
    module = pyinfra_task_harness.load("docker.py", {
        "docker": {"custom": {}},
    })
    pyinfra_task_harness.host.get_fact = lambda _fact, command="", **_kwargs: (
        "1000" if command.startswith("id -u")
        else ("custom" if "config --services" in command else None)
    )

    module.deploy_docker_service("custom", "Custom", "/home/tester")

    service_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload systemd and ensure custom is prepared"
    ]
    assert len(service_calls) == 1
    assert service_calls[0]["_if"]() is True


def test_caddy_deploys_and_enables_daily_renewal_timer(pyinfra_task_harness, monkeypatch):
    """Caddy certificate renewal is scheduled by the user systemd timer."""
    monkeypatch.setattr(builtins, "secrets", {
        "dehydrated": {"hetzner_api_token": "test-token"},
    })
    pyinfra_task_harness.load("caddy.py", {
        "docker": {"custom": {"port": 8080}},
        "caddy_config": {"example.org:443": {"reverse_proxy": "127.0.0.1:8080"}},
        "dehydrated_domains": [["example.org"]],
    })

    timer_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Enable daily Caddy certificate renewal"
    ]
    assert len(timer_calls) == 1
    assert any(
        command.endswith("systemctl --user enable --now caddy-renew.timer")
        for command in timer_calls[0]["commands"]
    )
    assert timer_calls[0]["_if"]() is True

def test_dehydrated_hook_handles_text_exit_argument():
    """A textual Dehydrated exit_hook argument must not trigger nounset errors."""
    hook = ROOT / "files/dehydrated_hook.sh"
    result = subprocess.run(
        ["bash", str(hook), "exit_hook", "The challenge failed"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "API_TOKEN": "test-token"},
    )
    assert result.returncode == 0
    assert "dehydrated reported an error: The challenge failed" in result.stderr


def test_caddy_image_creates_dehydrated_config_include_directory():
    """The configured CONFIG_D path exists in the built Caddy image."""
    dockerfile = (ROOT / "files/caddy/Dockerfile").read_text()
    assert "mkdir -p /etc/dehydrated/conf.d" in dockerfile
    assert "ca-certificates setpriv" in dockerfile

    renewal_service = (ROOT / "templates/caddy/dehydrated-renew.service.j2").read_text()
    assert "docker exec --user {{ uid }}:{{ gid }} caddy /usr/local/bin/renew.sh" in renewal_service

    compose = (ROOT / "templates/docker/caddy/docker-compose.yml.j2").read_text()
    assert "    user:" not in compose
    assert "      - ALL" in compose
    assert "      - NET_BIND_SERVICE" in compose
    assert "      - SETUID" in compose
    assert "      - SETGID" in compose
    assert 'CADDY_UID: "{{ uid }}"' in compose
    assert 'CADDY_GID: "{{ gid }}"' in compose

    entrypoint = (ROOT / "files/caddy/entrypoint.sh").read_text()
    assert "--inh-caps=+net_bind_service" in entrypoint
    assert "--ambient-caps=+net_bind_service" in entrypoint
    assert 'exec setpriv' in entrypoint

def test_caddy_does_not_rebuild_or_recreate_when_image_and_container_are_current(
    pyinfra_task_harness, monkeypatch,
):
    """An unchanged Caddy image and healthy container cause no Docker actions."""
    monkeypatch.setattr(builtins, "secrets", {
        "dehydrated": {"hetzner_api_token": "test-token"},
    })

    status_sudo_flags = []
    def get_fact(fact, command="", **kwargs):
        if "systemctl --user is-active caddy-renew.timer" in command:
            status_sudo_flags.append(kwargs.get("_sudo"))
        if "id -u" in command or "id -g" in command:
            return "1000"
        if "docker image inspect" in command:
            return "present"
        if "docker inspect -f '{{.State.Running}}'" in command:
            return "true"
        if "docker inspect -f '{{.State.Health.Status}}'" in command:
            return "healthy"
        if "systemctl --user is-active caddy-renew.timer" in command:
            return "active"
        return ""

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("caddy.py", {
        "username": "tester",
        "usergroup": "tester",
        "homedir": "/home/tester",
        "docker": {"custom": {"port": 8080}},
        "caddy_config": {"example.org:443": {"reverse_proxy": "127.0.0.1:8080"}},
        "dehydrated_domains": [["example.org"]],
    })

    docker_actions = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") in {
            "Enable daily Caddy certificate renewal",
            "Build Caddy image with Sablier plugin and Dehydrated",
            "Start Caddy and Dehydrated containers",
            "Wait for Caddy container health",
            "Reload Caddy after Caddyfile changes",
        }
    ]
    assert len(docker_actions) == 5
    assert all(call["_if"]() is False for call in docker_actions)
    assert status_sudo_flags == [False]



def test_sablier_systemd_preparation_reconciles_existing_containers():
    """Sablier preparation updates labels without starting on-demand services."""
    unit = (ROOT / "templates/docker/systemd.service.j2").read_text()
    assert "docker compose {{ compose_files }} up --no-start" in unit
    assert "docker compose {{ compose_files }} create" not in unit


def test_sudo_directory_is_skipped_when_metadata_matches(pyinfra_task_harness):
    """An already-correct sudoers directory is not scheduled for reconciliation."""
    pyinfra_task_harness.host.get_fact = lambda fact, command="", **_kwargs: (
        "root:root:755" if "stat -c" in command else ""
    )
    pyinfra_task_harness.load("sudo.py", {"sudoers_rules": ["%sudo ALL=(ALL:ALL) ALL"]})

    directory_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
        and kwargs.get("path") == "/etc/sudoers.d"
    ]
    assert len(directory_calls) == 1
    assert directory_calls[0]["_if"]() is False


def test_ssh_directory_is_skipped_when_metadata_matches(pyinfra_task_harness):
    """An already-correct SSH directory is not scheduled for reconciliation."""
    pyinfra_task_harness.host.get_fact = lambda fact, command="", **_kwargs: (
        "tester:tester:700" if "stat -c" in command else ""
    )
    pyinfra_task_harness.load("ssh_keys.py", {
        "username": "tester",
        "usergroup": "tester",
        "ssh_authorized_keys": {"tester": []},
    })

    directory_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
        and kwargs.get("path") == "/home/tester/.ssh/"
    ]
    assert len(directory_calls) == 1
    assert directory_calls[0]["_if"]() is False



def test_docker_systemd_commands_run_as_configured_user_when_root(pyinfra_task_harness):
    """Root-driven deployments must execute user-systemd commands as the owner."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "docker": {"custom": {}},
    })

    sudo_flags = []
    status_sudo_flags = []
    def get_fact(_fact, command="", **kwargs):
        sudo_flags.append(kwargs.get("_sudo"))
        if "is-active custom" in command:
            status_sudo_flags.append(kwargs.get("_sudo"))
        if command == "id -u":
            return "0"
        if command == "id -u tester":
            return "1000"
        if "config --services" in command:
            return "custom"
        if "is-active custom" in command:
            return "active"
        return ""

    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service("custom", "Custom", "/home/tester", username="tester")

    service_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload systemd and ensure custom is prepared"
    )
    assert service_call["_if"]() is False
    assert service_call["commands"][0].startswith("runuser -u tester -- env ")
    assert False in sudo_flags
    assert status_sudo_flags == [False]


def test_docker_systemd_commands_use_current_configured_user(pyinfra_task_harness):
    """Deployments already running as the configured user avoid runuser."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "docker": {"custom": {}},
    })

    sudo_flags = []
    status_sudo_flags = []
    def get_fact(_fact, command="", **kwargs):
        sudo_flags.append(kwargs.get("_sudo"))
        if "is-active custom" in command:
            status_sudo_flags.append(kwargs.get("_sudo"))
        if command in {"id -u", "id -u tester"}:
            return "1000"
        if "config --services" in command:
            return "custom"
        if "is-active custom" in command:
            return "active"
        return ""

    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service("custom", "Custom", "/home/tester", username="tester")

    service_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload systemd and ensure custom is prepared"
    )
    assert service_call["_if"]() is False
    assert service_call["commands"][0].startswith("env XDG_RUNTIME_DIR=/run/user/1000")
    assert False in sudo_flags
    assert status_sudo_flags == [False]



def test_homepage_api_requests_bypass_sablier_only_on_matching_paths(pyinfra_task_harness):
    """Homepage widget API prefixes bypass Sablier; other requests remain protected."""
    module = pyinfra_task_harness.load("caddy.py")
    homepage_services = [
        {"Services": [
            {"Miniflux": {"widget": {"type": "miniflux", "url": "https://rss.example"}}},
            {"Linkwarden": {"widget": {"type": "linkwarden", "url": "https://links.example"}}},
            {"Paperless": {"widget": {"type": "paperlessngx", "url": "https://paper.example"}}},
            {"Firefly": {"widget": {"type": "firefly", "url": "https://firefly.example"}}},
            {"Portainer": {"widget": {"type": "portainer", "url": "https://portainer.example", "env": 3}}},
            {"Forgejo": {"widget": {"type": "gitea", "url": "https://forgejo.example"}}},
            {"NocoDB": {"widget": {"type": "customapi", "url": "https://nocodb.example/api/v2/meta/bases/"}}},
            {"Snipe": {"widget": {"type": "customapi", "url": "https://snipe.example/api/v1/dashboard/companies"}}},
            {"TimeTagger": {"widget": {"type": "customapi", "url": "https://time.example/timetagger/api/v2/records?running=true"}}},
        ]},
    ]
    from tasks.homepage_config import homepage_api_exclusions

    original = __import__("copy").deepcopy(homepage_services)
    exclusions = homepage_api_exclusions(homepage_services)
    assert exclusions["rss.example"] == ["/api/*", "/v1/*"]
    assert exclusions["links.example"] == ["/api/*", "/v1/*"]
    assert exclusions["portainer.example"] == ["/api/*", "/v1/*"]
    assert exclusions["nocodb.example"] == ["/api/*", "/api/v2/meta/bases/", "/v1/*"]
    assert exclusions["snipe.example"] == ["/api/*", "/api/v1/dashboard/companies", "/v1/*"]
    assert exclusions["time.example"] == ["/api/*", "/timetagger/api/v2/records", "/v1/*"]
    assert homepage_services == original

    # Widgets sharing a hostname are combined without changing Homepage config.
    homepage_services[0]["Services"].append(
        {"Second": {"widget": {"type": "customapi", "url": "https://rss.example/custom/status?x=1"}}}
    )
    combined = homepage_api_exclusions(homepage_services)
    assert combined["rss.example"] == ["/api/*", "/custom/status", "/v1/*"]

    config = {
        "links.example:443": {"reverse_proxy": "127.0.0.1:8021", "header": ["-Server"]},
        "other.example:443": {"reverse_proxy": "127.0.0.1:8022"},
    }
    result = module.build_sablier_caddy_config(
        config,
        {"linkwarden": {"port": 8021}, "paperless": {"port": 8022}},
        {"enabled": True, "homepage_services": homepage_services},
    )
    linkwarden_route = result["links.example:443"]["route"]
    assert linkwarden_route["@homepage_api"]["path"] == "/api/* /v1/*"
    assert linkwarden_route["handle @homepage_api"]["reverse_proxy"] == "127.0.0.1:8021"
    assert linkwarden_route["handle @homepage_api"]["header"] == ["-Server"]
    assert "sablier http://127.0.0.1:10000" in linkwarden_route["handle"]
    assert result["other.example:443"]["route"]["handle"]["sablier http://127.0.0.1:10000"]


