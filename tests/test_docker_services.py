"""Focused tests for Docker service configuration and directory reconciliation."""

import ast
import builtins
import json
import re
import subprocess
import sys
import types

import pytest

from conftest import ROOT

def test_docker_service_modules_declare_compose_services():
    """Sablier service names are static so first deployment needs no remote Compose fact."""
    for task_path in sorted((ROOT / "tasks/docker").glob("*.py")):
        if task_path.stem == "linkwarden_bookmarks":
            continue

        tree = ast.parse(task_path.read_text())
        deploy_call = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "deploy_docker_service"
        )
        compose_argument = next(
            keyword.value for keyword in deploy_call.keywords
            if keyword.arg == "compose_services"
        )
        declared_services = ast.literal_eval(compose_argument)

        template = ROOT / "templates/docker" / task_path.stem / "docker-compose.yml.j2"
        template_lines = template.read_text().splitlines()
        in_services = False
        template_services = []
        for line in template_lines:
            if line.strip() == "services:":
                in_services = True
                continue
            if in_services and line and not line.startswith(" "):
                break
            if in_services:
                match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
                if match:
                    template_services.append(match.group(1))

        assert declared_services == template_services, task_path.name

def test_docker_sablier_container_inspection_is_deferred_until_execution(
    pyinfra_task_harness,
):
    """The Docker daemon is queried only after its Compose project is deployed."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
        "docker": {"custom": {"sablier": {"enabled": True}}},
        "docker_sablier": {"enabled": True},
    })
    observed = []

    def get_fact(_fact, command="", **_kwargs):
        observed.append(command)
        if command.startswith("id -u"):
            return "1000"
        if "show --property=ActiveState --value custom" in command:
            return "active"
        if "docker compose" in command:
            return "match"
        return ""

    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service(
        "custom",
        "Custom",
        "/home/tester",
        username="tester",
        usergroup="tester",
        compose_services=["app"],
    )
    assert not any("docker compose" in command for command in observed)

    label_operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Recreate custom containers with Sablier labels"
    )
    assert label_operation["_if"]() is False
    assert any("docker compose" in command for command in observed)

def test_sudo_directory_uses_declarative_metadata_reconciliation(pyinfra_task_harness):
    """files.directory handles sudoers directory ownership and mode idempotently."""
    fact_commands = []
    pyinfra_task_harness.host.get_fact = lambda _fact, *args, **kwargs: (
        fact_commands.append(kwargs.get("command", args[0] if args else "")) or ""
    )
    pyinfra_task_harness.load("sudo.py", {"sudoers_rules": ["%sudo ALL=(ALL:ALL) ALL"]})
    directory_calls = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
        and kwargs.get("path") == "/etc/sudoers.d"
    ]
    assert len(directory_calls) == 1
    assert directory_calls[0]["user"] == "root"
    assert directory_calls[0]["group"] == "root"
    assert directory_calls[0]["mode"] == "755"
    assert "_if" not in directory_calls[0]
    assert not any("stat -c" in command for command in fact_commands)

def test_ssh_directory_uses_declarative_metadata_reconciliation(pyinfra_task_harness):
    """files.directory handles SSH directory ownership and mode idempotently."""
    fact_commands = []
    pyinfra_task_harness.host.get_fact = lambda _fact, *args, **kwargs: (
        fact_commands.append(kwargs.get("command", args[0] if args else "")) or ""
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
    assert directory_calls[0]["user"] == "tester"
    assert directory_calls[0]["group"] == "tester"
    assert directory_calls[0]["mode"] == "700"
    assert "_if" not in directory_calls[0]
    assert not any("stat -c" in command for command in fact_commands)

def test_docker_compose_projects_use_managed_directory_and_remove_legacy_files(
    pyinfra_task_harness,
):
    """Compose files and systemd working directories stay below ~/.docker."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
    })
    module.deploy_docker_service(
        "custom",
        "Custom",
        "/home/tester",
        username="tester",
        usergroup="tester",
    )

    compose = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("name") == "Configure custom"
    )
    unit = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("name") == "Deploy custom systemd service"
    )
    legacy = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "file"
        and kwargs.get("name", "").startswith("Remove legacy custom")
    ]

    assert compose["dest"] == "/home/tester/.docker/custom/docker-compose.yml"
    assert unit["compose_files"] == "-f docker-compose.yml"
    assert len(legacy) == 2
    assert all(operation["present"] is False for operation in legacy)

def test_timetagger_stores_credentials_in_private_env_file(
    pyinfra_task_harness, monkeypatch,
):
    """TimeTagger credentials are kept out of the Compose template."""
    docker_module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
    })
    monkeypatch.setitem(sys.modules, "tasks.docker", docker_module)
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"docker": {"timetagger": {"credentials": "tester:$2a$08$hash"}}},
        raising=False,
    )

    pyinfra_task_harness.load("docker/timetagger.py", {
        "docker": {"timetagger": {}},
        "homedir": "/home/tester",
        "username": "tester",
        "usergroup": "tester",
    })

    credentials_file = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Configure private timetagger environment"
    )
    assert credentials_file["mode"] == "600"
    assert credentials_file["dest"] == "/home/tester/.docker/timetagger/.env"
    assert credentials_file["src"].getvalue() == "TIMETAGGER_CREDENTIALS='tester:$2a$08$hash'\n"

    template = (ROOT / "templates/docker/timetagger/docker-compose.yml.j2").read_text()
    assert 'TIMETAGGER_CREDENTIALS: "${TIMETAGGER_CREDENTIALS:?}"' in template
    assert "test:test" not in template




def test_timetagger_rejects_missing_encrypted_credentials(
    pyinfra_task_harness, monkeypatch,
):
    docker_module = types.ModuleType("tasks.docker")
    docker_module.deploy_docker_service = lambda **_kwargs: None
    monkeypatch.setitem(sys.modules, "tasks.docker", docker_module)
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)

    with pytest.raises(ValueError, match="credentials must be a single-line"):
        pyinfra_task_harness.load("docker/timetagger.py", {
            "docker": {"timetagger": {}},
            "homedir": "/home/tester",
        })

def test_all_compose_data_uses_host_bind_mounts_under_docker_directory():
    """Compose projects never use Docker-managed named volumes."""
    templates = sorted((ROOT / "templates/docker").glob("*/docker-compose.yml.j2"))
    assert templates

    for template in templates:
        lines = template.read_text().splitlines()
        assert not any(re.match(r"^volumes:\s*$", line) for line in lines), template

        for index, line in enumerate(lines):
            if not re.match(r"^    volumes:\s*$", line):
                continue

            mount_index = index + 1
            while mount_index < len(lines):
                mount_line = lines[mount_index]
                if not mount_line.strip():
                    mount_index += 1
                    continue
                if not mount_line.startswith("      - "):
                    break

                mount = mount_line.strip()[2:].strip().strip('"')
                host_path = mount.split(":", 1)[0]
                assert (
                    host_path.startswith("{{ homedir }}/.docker/")
                    or host_path == "/var/run/docker.sock"
                ), f"{template}: unexpected volume source {host_path!r}"
                mount_index += 1

def test_secrets_example_is_valid_json_and_documents_timetagger_credentials():
    """The tracked encrypted-secrets example remains parseable and complete."""
    example = json.loads((ROOT / "secrets.json.gpg.example").read_text())

    assert example["hosts"]["@local"]["docker"]["timetagger"]["credentials"] == (
        "REPLACE_USERNAME:REPLACE_WITH_BCRYPT_HASH"
    )

def test_docker_private_environment_is_literal_and_excluded_from_compose(
    pyinfra_task_harness,
):
    """Private environment values are uploaded separately with restrictive mode."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
    })
    module.deploy_docker_service(
        "custom",
        "Custom",
        "/home/tester",
        username="tester",
        usergroup="tester",
        private_env={"API_TOKEN": "token-with-$-characters"},
    )

    env_file = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Configure private custom environment"
    )
    compose = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("name") == "Configure custom"
    )

    assert env_file["dest"] == "/home/tester/.docker/custom/.env"
    assert env_file["mode"] == "600"
    assert env_file["src"].getvalue() == "API_TOKEN='token-with-$-characters'\n"
    assert "private_env" not in compose
    assert "token-with-$-characters" not in repr(compose)


def test_docker_private_environment_rejects_unsafe_keys_and_values(
    pyinfra_task_harness,
):
    """Private env files reject names and values that could alter parsing."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
    })
    with pytest.raises(ValueError, match="Invalid private environment variable"):
        module.deploy_docker_service(
            "custom", "Custom", "/home/tester",
            private_env={"BAD-KEY": "value"},
        )

    with pytest.raises(ValueError, match="single-line string"):
        module.deploy_docker_service(
            "custom", "Custom", "/home/tester",
            private_env={"API_TOKEN": "line1\nline2"},
        )

def test_secret_bearing_compose_templates_use_private_environment_variables():
    """Secret values are interpolated from private project env files, not Jinja."""
    templates = {
        "firefly-iii": ("DATABASE_PASSWORD", "MYSQL_ROOT_PASSWORD", "APP_KEY", "STATIC_CRON_TOKEN"),
        "linkwarden": ("POSTGRES_PASSWORD", "NEXTAUTH_SECRET", "MEILI_MASTER_KEY"),
        "miniflux": ("POSTGRES_PASSWORD", "ADMIN_PASSWORD"),
        "paperless": ("POSTGRES_PASSWORD", "PAPERLESS_SECRET_KEY"),
        "snipe-it": ("DATABASE_PASSWORD", "MYSQL_ROOT_PASSWORD", "APP_KEY"),
        "vaultwarden": ("ADMIN_TOKEN",),
        "timetagger": ("TIMETAGGER_CREDENTIALS",),
    }

    for service, variables in templates.items():
        content = (
            ROOT / f"templates/docker/{service}/docker-compose.yml.j2"
        ).read_text()
        assert not re.search(r"{{[^}]*?(password|secret|token|key)[^}]*}}", content, re.I)
        for variable in variables:
            assert "${" + variable in content, f"{service} does not interpolate {variable}"

    homepage = (
        ROOT / "templates/docker/homepage/docker-compose.yml.j2"
    ).read_text()
    assert "environment_keys" in homepage

def test_empty_private_environment_removes_stale_credentials(pyinfra_task_harness):
    """Removing configured secrets deletes the old private project env file."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "usergroup": "tester",
    })
    module.deploy_docker_service(
        "custom",
        "Custom",
        "/home/tester",
        username="tester",
        usergroup="tester",
        private_env={},
    )

    removal = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "file"
        and kwargs.get("name") == "Remove private custom environment"
    )
    assert removal["path"] == "/home/tester/.docker/custom/.env"
    assert removal["present"] is False


def test_adguard_home_is_dispatched_only_when_configured():
    """AdGuard Home remains opt-in through the docker host-data mapping."""
    source = (ROOT / "tasks/docker_container.py").read_text()
    assert 'if "adguard_home" in container:' in source
    assert 'local.include("tasks/docker/adguard_home.py")' in source


def test_adguard_home_uses_host_network_and_persistent_bind_mounts():
    """DNS binds directly to the host while all state remains under ~/.docker."""
    template = (
        ROOT / "templates/docker/adguard_home/docker-compose.yml.j2"
    ).read_text()
    assert "network_mode: host" in template
    assert "{{ homedir }}/.docker/adguard_home/work:/opt/adguardhome/work" in template
    assert "{{ homedir }}/.docker/adguard_home/conf:/opt/adguardhome/conf" in template
    assert "ports:" not in template
    assert "volumes:" not in template.split("services:", 1)[0]


def test_adguard_public_dns_firewall_rule_is_documented_as_opt_in():
    """The sample exposes an explicit, opt-in UFW rule for public DNS."""
    example = (ROOT / "group_data/@local.py.example").read_text()
    documentation = (ROOT / "docs/docker.md").read_text()
    firewall_task = (ROOT / "tasks/ufw.py").read_text()

    assert '"adguard-dns"' in example
    assert '"action": "Allow"' in example
    assert '"rule": "53"' in example
    assert "both TCP and UDP port 53" in example
    assert "open resolver" in example
    assert '"rule": "53"' in documentation
    assert "both TCP and UDP port 53" in documentation
    assert "ufw {custom_action.lower()} {rule_arguments}" in firewall_task


@pytest.mark.parametrize(("settings", "expected"), [
    ({}, "127.0.0.1:3000"),
    ({"web_port": 3001}, "127.0.0.1:3001"),
])
def test_adguard_web_port_defaults_and_is_configurable(pyinfra_task_harness, settings, expected):
    """AdGuard keeps the legacy port by default and accepts an explicit web port."""
    config = {"adguard_home": settings}
    pyinfra_task_harness.host.data["docker"] = config
    module = pyinfra_task_harness.load("docker/adguard_home.py", {
        "docker": config,
        "homedir": "/home/tester",
        "username": "tester",
        "usergroup": "tester",
    })

    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Configure AdGuard Home web UI listen address"
    )
    assert expected in operation["commands"][0]
    assert operation["_sudo"] is True
    assert operation["_if"]() is False  # Missing config is a no-op during first-run setup.
    assert any(
        kwargs.get("restart_if") is not None
        for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
    ) is False
    assert module._ADGUARD_CONFIG_SCRIPT


@pytest.mark.parametrize("web_port", [0, 65536, True, "3001", 1.5])
def test_adguard_rejects_invalid_web_ports(pyinfra_task_harness, web_port):
    """Invalid ports fail before scheduling changes."""
    with pytest.raises(ValueError, match="web_port must be an integer"):
        pyinfra_task_harness.load("docker/adguard_home.py", {
            "docker": {"adguard_home": {"web_port": web_port}},
            "homedir": "/home/tester",
        })


def test_adguard_config_reconciliation_preserves_settings_and_is_idempotent(
    pyinfra_task_harness, tmp_path,
):
    """Only http.address changes; a second reconciliation is a no-op."""
    module = pyinfra_task_harness.load("docker/adguard_home.py", {
        "docker": {"adguard_home": {"web_port": 3001}},
        "homedir": "/home/tester",
    })
    config = tmp_path / "AdGuardHome.yaml"
    original = (
        "http:\\n"
        "  pprof:\\n"
        "    port: 6060\\n"
        "  address: 0.0.0.0:3000\\n"
        "users:\\n"
        "- name: admin\\n"
        "  password: hash\\n"
    )
    config.write_text(original, encoding="utf-8")

    def run(mode):
        return subprocess.run(
            [sys.executable, "-c", module._ADGUARD_CONFIG_SCRIPT,
             str(config), "127.0.0.1:3001", mode],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    assert run("check") == "change"
    assert run("apply") == "changed"
    updated = config.read_text(encoding="utf-8")
    assert updated == original.replace(
        "  address: 0.0.0.0:3000",
        "  address: 127.0.0.1:3001",
    )
    assert run("check") == "unchanged"
    assert run("apply") == "unchanged"
    assert config.read_text(encoding="utf-8") == updated


def test_adguard_config_reconciliation_adds_http_section_without_replacing_config(
    pyinfra_task_harness, tmp_path,
):
    """A config without an http section gets one appended with other data intact."""
    module = pyinfra_task_harness.load("docker/adguard_home.py", {
        "docker": {"adguard_home": {"web_port": 3001}},
        "homedir": "/home/tester",
    })
    config = tmp_path / "AdGuardHome.yaml"
    config.write_text("users: []\\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-c", module._ADGUARD_CONFIG_SCRIPT,
         str(config), "127.0.0.1:3001", "apply"],
        check=True, capture_output=True, text=True,
    )
    assert result.stdout.strip() == "changed"
    assert config.read_text(encoding="utf-8") == (
        "users: []\\nhttp:\\n  address: 127.0.0.1:3001\\n"
    )
