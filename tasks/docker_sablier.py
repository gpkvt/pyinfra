"""Deploy Sablier as a Docker service using the Docker provider."""

import shlex

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from common import command_output_text

options = host.data.get("docker_sablier", {})

if options.get("enabled", False):
    provider_strategy = options.get("provider_strategy", "pause")
    if provider_strategy not in ("stop", "pause"):
        raise ValueError(
            "docker_sablier.provider_strategy must be 'stop' or 'pause'"
        )

    username = host.data.get("username", "root")
    usergroup = host.data.get("usergroup", "root")
    homedir = host.data.get("homedir", f"/home/{username}")

    files.directory(
        name="Create Sablier Docker directory",
        path=f"{homedir}/.docker/sablier",
        user=username, group=usergroup, mode="750",
    )
    config = files.template(
        name="Configure Sablier Docker provider and session defaults",
        src="templates/sablier/sablier.yaml.j2",
        dest=f"{homedir}/.docker/sablier/sablier.yaml",
        user=username, group=usergroup, mode="640",
        default_duration=options.get("default_duration", "15m"),
        provider_strategy=provider_strategy,
        _sudo=False,
    )
    compose = files.template(
        name="Configure Sablier Docker provider",
        src="templates/docker/sablier/docker-compose.yml.j2",
        dest=f"{homedir}/.docker/sablier/docker-compose.yml",
        user=username, group=usergroup, mode="640",
        sablier_version=options.get("version", "1.20.0"),
        homedir=homedir,
        _sudo=False,
    )
    server.shell(
        name="Enable lingering for Docker service user",
        commands=[f"loginctl enable-linger {shlex.quote(username)}"],
        _sudo=True,
        _if=lambda: command_output_text(host.get_fact(
            Command, f"loginctl show-user {shlex.quote(username)} -p Linger"
        )).strip() != "Linger=yes",
    )
    compose_file = shlex.quote(f"{homedir}/.docker/sablier/docker-compose.yml")

    server.shell(
        name="Pull Sablier image",
        commands=[f"docker compose -f {compose_file} pull"],
        _sudo=False, _if=lambda: compose.did_change() or config.did_change(),
    )
    server.shell(
        name="Ensure Sablier container is running",
        commands=[f"docker compose -f {compose_file} up -d"],
        _sudo=False,
        _if=lambda: (
            compose.did_change()
            or config.did_change()
            or command_output_text(host.get_fact(
                Command,
                "docker inspect -f '{{.State.Running}}' sablier 2>/dev/null || true",
            )).strip() != "true"
        ),
    )
