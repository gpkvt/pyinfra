"""Focused tests for Docker service configuration and directory reconciliation."""

import ast
import re

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
