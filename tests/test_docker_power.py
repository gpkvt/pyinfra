"""Tests for Docker battery-saver configuration validation."""

import pytest


def test_docker_power_save_accepts_valid_container_names(pyinfra_task_harness):
    pyinfra_task_harness.load("docker_power.py", {
        "docker_power_save": ["web", "database_1", "cache-1", "app.v2"],
        "docker_sablier": {"enabled": False},
    })

    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "template"
        and kwargs.get("dest") == "/etc/docker/battery-containers.conf"
    )
    assert operation["containers"] == ["web", "database_1", "cache-1", "app.v2"]


@pytest.mark.parametrize("names", [
    "web",
    ["web; touch /tmp/owned"],
    ["web name"],
    ["../escape"],
    ["-leading-dash"],
    ["x" * 256],
])
def test_docker_power_save_rejects_invalid_container_names(
    pyinfra_task_harness, names,
):
    with pytest.raises(ValueError, match="docker_power_save"):
        pyinfra_task_harness.load("docker_power.py", {
            "docker_power_save": names,
        })


def test_docker_power_save_rejects_duplicate_container_names(pyinfra_task_harness):
    with pytest.raises(ValueError, match="duplicate"):
        pyinfra_task_harness.load("docker_power.py", {
            "docker_power_save": ["web", "web"],
        })
