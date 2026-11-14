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


def test_docker_power_manager_retries_after_partial_stop_failure(tmp_path):
    """A failed stop must not leave a state file that blocks later retries."""
    import os
    import subprocess

    from conftest import ROOT

    config = tmp_path / "battery-containers.conf"
    config.write_text('BATTERY_CONTAINERS=("first" "second")\n', encoding="utf-8")

    state_dir = tmp_path / "state"
    docker_state = tmp_path / "docker-state"
    docker_state.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
case "$1" in
    inspect)
        if [[ -e "$FAKE_DOCKER_STATE/$4" ]]; then
            echo false
        else
            echo true
        fi
        ;;
    stop)
        if [[ "$2" == first && -e "$FAKE_DOCKER_STATE/fail-once" ]]; then
            rm "$FAKE_DOCKER_STATE/fail-once"
            exit 1
        fi
        touch "$FAKE_DOCKER_STATE/$2"
        ;;
    start)
        echo "$2" >> "$FAKE_DOCKER_STATE/started"
        rm -f "$FAKE_DOCKER_STATE/$2"
        ;;
esac
""",
        encoding="utf-8",
    )
    docker.chmod(0o755)
    (docker_state / "fail-once").touch()

    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "DOCKER_POWER_CONFIG": str(config),
        "DOCKER_POWER_STATE_DIR": str(state_dir),
        "FAKE_DOCKER_STATE": str(docker_state),
    }
    manager = ROOT / "files/docker-battery-saver/docker-power-manager"

    first = subprocess.run(
        ["bash", str(manager), "battery"], env=env, check=False,
        capture_output=True, text=True,
    )
    assert first.returncode != 0
    assert (state_dir / "running-containers").is_file()
    assert not (state_dir / "running-containers.complete").exists()

    retry = subprocess.run(
        ["bash", str(manager), "battery"], env=env, check=False,
        capture_output=True, text=True,
    )
    assert retry.returncode == 0
    assert (state_dir / "running-containers.complete").is_file()
    assert (docker_state / "first").is_file()
    assert (docker_state / "second").is_file()

    restore = subprocess.run(
        ["bash", str(manager), "ac"], env=env, check=False,
        capture_output=True, text=True,
    )
    assert restore.returncode == 0
    assert (docker_state / "started").read_text(encoding="utf-8").splitlines() == [
        "first", "second",
    ]
    assert not (state_dir / "running-containers").exists()
    assert not (state_dir / "running-containers.complete").exists()
