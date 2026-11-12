"""Deploy Sablier as a Docker service using the Docker provider."""

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

SABLIER_VERSION = "1.20.0"
options = host.data.get("docker_sablier", {})

if options.get("enabled", False):
    username = host.data.get("username", "root")
    usergroup = host.data.get("usergroup", "root")
    homedir = host.data.get("homedir", f"/home/{username}")

    # Retire the previous host-installed Sablier systemd provider before
    # binding the Docker provider to its former API port.
    legacy_unit = f"{homedir}/.config/systemd/user/sablier.service"
    legacy_active = host.get_fact(
        Command, "systemctl --user is-active sablier.service 2>/dev/null || true"
    ).strip() == "active"
    legacy_enabled = host.get_fact(
        Command, "systemctl --user is-enabled sablier.service 2>/dev/null || true"
    ).strip() == "enabled"
    legacy_unit_present = host.get_fact(
        Command, f"test -f {legacy_unit} && echo yes || echo no"
    ).strip() == "yes"
    server.shell(
        name="Stop obsolete host Sablier service",
        commands=["systemctl --user disable --now sablier.service || true"],
        _sudo=False,
        _if=lambda: legacy_active or legacy_enabled,
    )
    files.file(
        name="Remove obsolete Sablier user service unit",
        path=legacy_unit,
        present=False,
        _sudo=False,
    )
    files.file(
        name="Remove obsolete Sablier binary",
        path=f"{homedir}/.local/bin/sablier",
        present=False,
        _sudo=False,
    )
    files.file(
        name="Remove obsolete Sablier systemd-provider configuration",
        path=f"{homedir}/.config/sablier/sablier.yaml",
        present=False,
        _sudo=False,
    )
    server.shell(
        name="Reload user systemd after retiring host Sablier",
        commands=["systemctl --user daemon-reload"],
        _sudo=False,
        _if=lambda: legacy_unit_present,
    )
    files.directory(
        name="Create Sablier Docker directory",
        path=f"{homedir}/.docker/sablier",
        user=username, group=usergroup, mode="750",
    )
    compose = files.template(
        name="Configure Sablier Docker provider",
        src="templates/docker/sablier/docker-compose.yml.j2",
        dest=f"{homedir}/.docker/sablier/docker-compose.yml",
        user=username, group=usergroup, mode="640",
        sablier_version=SABLIER_VERSION,
        default_duration=options.get("default_duration", "60m"),
        _sudo=False,
    )
    server.shell(
        name="Enable lingering for Docker service user",
        commands=[f"loginctl enable-linger {username}"],
        _sudo=True,
        _if=lambda: host.get_fact(
            Command, f"loginctl show-user {username} -p Linger"
        ).strip() != "Linger=yes",
    )
    server.shell(
        name="Pull Sablier image",
        commands=[f"docker compose -f {homedir}/.docker/sablier/docker-compose.yml pull"],
        _sudo=False, _if=compose.did_change,
    )
    server.shell(
        name="Ensure Sablier container is running",
        commands=[f"docker compose -f {homedir}/.docker/sablier/docker-compose.yml up -d"],
        _sudo=False,
        _if=lambda: (
            compose.did_change
            or host.get_fact(
                Command,
                "docker inspect -f '{{.State.Running}}' sablier 2>/dev/null || true",
            ).strip() != "true"
        ),
    )
