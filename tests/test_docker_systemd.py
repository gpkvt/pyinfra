"""Docker systemd and Sablier reconciliation task tests."""

def test_docker_systemd_commands_run_as_configured_user_when_root(pyinfra_task_harness):
    """Root-driven deployments must execute user-systemd commands as the owner."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "docker": {"custom": {}},
        "docker_sablier": {"enabled": False},
    })
    sudo_flags = []
    status_sudo_flags = []
    def get_fact(_fact, command="", **kwargs):
        sudo_flags.append(kwargs.get("_sudo"))
        if "show --property=ActiveState --value custom" in command:
            status_sudo_flags.append(kwargs.get("_sudo"))
        if command == "id -u":
            return "0"
        if command == "id -u tester":
            return "1000"
        if "config --services" in command:
            return "custom"
        if "show --property=ActiveState --value custom" in command:
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
        if "show --property=ActiveState --value custom" in command:
            status_sudo_flags.append(kwargs.get("_sudo"))
        if command in {"id -u", "id -u tester"}:
            return "1000"
        if "config --services" in command:
            return "custom"
        if "show --property=ActiveState --value custom" in command:
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


def test_docker_service_restarts_when_sablier_labels_drift(pyinfra_task_harness):
    """Existing containers with missing Sablier labels trigger service preparation."""
    module = pyinfra_task_harness.load("docker.py", {
        "username": "tester",
        "docker": {"custom": {}},
        "docker_sablier": {"enabled": True},
    })
    def get_fact(_fact, command="", **_kwargs):
        if command.startswith("id -u"):
            return "1000"
        if "show --property=ActiveState --value custom" in command:
            return "active"
        if "container_ids=" in command:
            return "drift"
        return ""

    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service(
        "custom", "Custom", "/home/tester", compose_services=["web", "db"]
    )
    reconcile_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Recreate custom containers with Sablier labels"
    )
    restart_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload systemd and ensure custom is prepared"
    )
    assert reconcile_call["_if"]() is True
    assert restart_call["_if"]() is True


def test_docker_service_starts_when_systemd_unit_is_inactive(pyinfra_task_harness):
    """Inactive systemd units are detected without a failing is-active fact."""
    module = pyinfra_task_harness.load("docker.py", {
        "docker": {"custom": {}},
        "docker_sablier": {"enabled": False},
    })
    commands = []
    def get_fact(_fact, command="", **_kwargs):
        commands.append(command)
        if command.startswith("id -u"):
            return "1000"
        if "show --property=ActiveState --value custom" in command:
            return "inactive"
        raise AssertionError("Unexpected fact: " + command)

    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service("custom", "Custom", "/home/tester")
    assert any(
        "show --property=ActiveState --value custom" in command
        for command in commands
    )
    assert not any("is-active custom" in command for command in commands)
    service_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload systemd and ensure custom is prepared"
    )
    assert service_call["commands"][-1].endswith("start custom")
    assert service_call["_if"]() is True


def test_docker_service_uses_configured_compose_services_on_first_deployment(
    pyinfra_task_harness,
):
    """Static Compose services avoid querying a file not yet deployed."""
    module = pyinfra_task_harness.load("docker.py", {
        "docker": {"custom": {}},
        "docker_sablier": {"enabled": True},
    })
    commands = []
    def get_fact(_fact, command="", **_kwargs):
        commands.append(command)
        if command.startswith("id -u"):
            return "1000"
        if "show --property=ActiveState --value custom" in command:
            return "active"
        if "docker inspect" in command:
            return "match"
        raise AssertionError("Unexpected fact during first deployment: " + command)
    pyinfra_task_harness.host.get_fact = get_fact
    module.deploy_docker_service(
        "custom",
        "Custom",
        "/home/tester",
        compose_services=["worker", "web", "database"],
    )
    assert not any("config --services" in command for command in commands)
    override_call = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("src") == "templates/docker/sablier-override.yml.j2"
    )
    assert override_call["sablier_services"] == ["database", "web", "worker"]
