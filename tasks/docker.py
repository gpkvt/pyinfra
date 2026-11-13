# pylint: disable=E0401, C0116, E1101, C0303

"""
Install Docker and deploy configured Docker services using pyinfra.

This module installs Docker Engine, configures the user's Docker directory,
and provides a reusable deployment function for managing Docker Compose
services and their corresponding user-level systemd units.

Configuration:
    docker (dict): Docker service configuration retrieved from
        host.data.docker. Defaults to an empty dictionary.

    username (str): User who owns Docker configuration files and
        directories. Defaults to "root".

    usergroup (str): Group that owns Docker configuration files and
        directories. Defaults to "root".

    homedir (str): Home directory of the configured user.
        Defined globally in the main deployment configuration.

Deployments:

    deploy_docker_service(
        service,
        description,
        homedir,
        username="root",
        usergroup="root",
        restart_if=None,
        **template_vars,
    )

    Deploys a Docker Compose service and its user-level systemd unit.

    Parameters:
        service (str): Service name. Used to determine template locations,
            destination paths, and systemd service names.

        description (str): Description assigned to the systemd unit.

        homedir (str): Home directory used for service configuration files.

        username (str): Owner of deployed files and directories.
            Defaults to "root".

        usergroup (str): Group ownership of deployed files and directories.
            Defaults to "root".

        **template_vars: Additional variables passed to the Docker Compose
            Jinja2 template. The homedir variable is passed automatically.

    Operations:
        1. Create the service-specific Docker configuration directory at
           ~/.docker/<service>/.

        2. Generate the Docker Compose configuration from
           templates/docker/<service>/docker-compose.yml.j2
           and deploy it to ~/<service>/docker-compose.yml.

        3. Generate the user-level systemd unit from
           templates/docker/systemd.service.j2
           and deploy it to
           ~/.config/systemd/user/<service>.service.

        4. Reload the user systemd daemon and enable the service when
           the systemd unit file changes.

        5. Restart the service when the Docker Compose configuration,
           systemd unit file, or an additional restart trigger changes.

    File permissions:
        - Docker configuration directory: 0750.
        - Docker Compose configuration: 0640.
        - Systemd service unit: 0644.

    Service management:
        Services are managed through the configured user's systemd
        instance without sudo:

            systemctl --user daemon-reload
            systemctl --user enable <service>
            systemctl --user restart <service>

Docker installation:
    Installs the following packages using sudo:
        - docker-ce
        - docker-ce-cli
        - docker-ce-rootless-extras

Docker directory:
    Creates ~/.docker/ with the configured user and group ownership
    and permissions set to 0750.

Conditional service deployments:
    Additional service-specific deployment modules are included when
    their respective keys are present in host.data.docker:

        - miniflux: tasks/docker/miniflux.py
        - timetagger: tasks/docker/timetagger.py
        - wallabag: tasks/docker/wallabag.py
        - vaultwarden: tasks/docker/vaultwarden.py

Notes:
    - Docker Compose and systemd configurations are generated using
      Jinja2 templates.
    - Service-specific credentials and settings should be supplied
      through the deployment configuration and template variables.
    - Systemd operations run without sudo and manage the user's
      systemd instance.
    - Unchanged configuration files do not trigger unnecessary
      systemd reloads or service restarts.
    - Changes to the systemd unit trigger daemon-reload, enable,
      and restart.
    - Changes to the Docker Compose configuration trigger a
      service restart.
    - Service-specific operations can be supplied as additional
      restart triggers through restart_if.
    - Docker image updates are not automatically pulled.
"""

import shlex

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server
from pyinfra.operations.util import any_changed


def ensure_numeric_directory(path, uid, gid, mode, sudo=True):
    """Ensure a directory has the requested numeric ownership and mode.

    Unlike files.directory, this check compares numeric UID/GID values,
    which is important for container data directories owned by numeric
    container users that may not exist in the host's user database.
    """
    quoted_path = shlex.quote(path)
    expected = f"{uid}:{gid}:{mode}"
    check_command = (
        f"if [ -d {quoted_path} ]; then "
        f"stat -c '%u:%g:%a' -- {quoted_path}; "
        "else printf 'missing\\n'; fi"
    )

    server.shell(
        name=f"Ensure directory metadata: {path}",
        commands=[
            f"install -d -o {uid} -g {gid} -m {mode} {quoted_path}",
        ],
        _sudo=sudo,
        _if=lambda: host.get_fact(Command, check_command) != expected,
    )


if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

@deploy("Deploy Docker service")
def deploy_docker_service( # pylint: disable=R0912,R0913,R0914,R0915,R0917
    service, description, homedir, username="root", usergroup="root",
    restart_if=None, app_services=None, compose_services=None, **template_vars,
):
    """Deploy one Compose project and prepare its containers for Sablier."""
    files.directory(
        name=f"Create {service} directory",
        path=f"{homedir}/.docker/{service}/",
        user=username, group=usergroup, mode="750",
    )
    compose_file = files.template(
        name=f"Configure {service}",
        src=f"templates/docker/{service}/docker-compose.yml.j2",
        dest=f"{homedir}/{service}/docker-compose.yml",
        user=username, group=usergroup, mode="640",
        homedir=homedir, **template_vars, _sudo=False,
    )

    sablier_options = host.data.get("docker_sablier", {})
    service_options = host.data.get("docker", {}).get(service, {})
    service_sablier = service_options.get("sablier", {})
    sablier_enabled = (
        bool(sablier_options.get("enabled", False))
        and service_sablier.get("enabled", True)
    )
    sablier_group = service_sablier.get("group", service)
    stop_dependencies = service_sablier.get(
        "stop_dependencies", sablier_options.get("stop_dependencies", True)
    )
    app_services = app_services or service_options.get("app_services", [service])

    if sablier_enabled and (not isinstance(sablier_group, str) or not sablier_group.strip()):
        raise ValueError(f"Invalid Sablier group for Docker service {service!r}")
    if not app_services or not all(isinstance(item, str) and item for item in app_services):
        raise ValueError(f"Invalid app_services configuration for Docker service {service!r}")

    if sablier_enabled:
        if compose_services is None:
            compose_services = service_options.get("sablier_services")

        if compose_services is not None:
            if (
                not isinstance(compose_services, (list, tuple))
                or not compose_services
                or not all(isinstance(item, str) and item for item in compose_services)
            ):
                raise ValueError(
                    f"Invalid Compose services configuration for {service!r}"
                )
            sablier_services = sorted(compose_services)
        else:
            compose_path = shlex.quote(f"{homedir}/{service}/docker-compose.yml")
            sablier_services_output = host.get_fact(
                Command,
                f"docker compose -f {compose_path} config --services",
            ) or ""
            sablier_services = sorted(sablier_services_output.split())

        if not sablier_services:
            raise ValueError(
                f"Docker Compose returned no services for {service!r}; "
                "cannot assign Sablier groups"
            )
    else:
        sablier_services = []


    if sablier_enabled:
        override_file = files.template(
            name=f"Configure Sablier labels for all {service} containers",
            src="templates/docker/sablier-override.yml.j2",
            dest=f"{homedir}/{service}/docker-compose.sablier.yml",
            user=username, group=usergroup, mode="640",
            sablier_services=sablier_services, sablier_group=sablier_group, _sudo=False,
        )
    else:
        override_file = files.file(
            name=f"Remove obsolete Sablier override for {service}",
            path=f"{homedir}/{service}/docker-compose.sablier.yml",
            present=False, _sudo=False,
        )

    compose_files = (
        "-f docker-compose.yml -f docker-compose.sablier.yml"
        if sablier_enabled else "-f docker-compose.yml"
    )

    server.shell(
        name=f"Pull {service} Docker images",
        commands=[f"docker compose -f {homedir}/{service}/docker-compose.yml pull"],
        _sudo=False, _if=compose_file.did_change,
    )

    systemd_unit = files.template(
        name=f"Deploy {service} systemd service",
        src="templates/docker/systemd.service.j2",
        dest=f"{homedir}/.config/systemd/user/{service}.service",
        user=username, group=usergroup, homedir=homedir,
        service=service, description=description,
        sablier_enabled=sablier_enabled, stop_dependencies=stop_dependencies,
        app_services=app_services, compose_files=compose_files,
        mode="644", _sudo=False,
    )
    restart_triggers = [compose_file, override_file, systemd_unit]
    if restart_if is not None:
        if isinstance(restart_if, (list, tuple)):
            restart_triggers.extend(restart_if)
        else:
            restart_triggers.append(restart_if)

    # pyinfra does not necessarily inherit the interactive user's systemd
    # environment. Set it explicitly so an active unit is not misdetected as
    # inactive (which would restart every service on every deployment).
    user_uid = (host.get_fact(Command, f"id -u {shlex.quote(username)}") or "").strip()
    current_uid = (host.get_fact(Command, "id -u", _sudo=False) or "").strip()
    if not user_uid.isdigit():
        raise RuntimeError(f"Unable to determine UID for systemd user {username!r}")
    if current_uid == user_uid:
        systemctl_user = (
            f"env XDG_RUNTIME_DIR=/run/user/{user_uid} "
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user_uid}/bus "
            "systemctl --user"
        )
    elif current_uid == "0":
        systemctl_user = (
            f"runuser -u {shlex.quote(username)} -- env "
            f"XDG_RUNTIME_DIR=/run/user/{user_uid} "
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{user_uid}/bus "
            "systemctl --user"
        )
    else:
        raise RuntimeError(
            f"Cannot manage systemd user {username!r} (UID {user_uid}) "
            f"from unprivileged UID {current_uid}"
        )
    service_status = host.get_fact(
        Command,
        f"{systemctl_user} show --property=ActiveState --value "
        f"{shlex.quote(service)}",
        _sudo=False,
    ) or ""
    service_active = service_status.strip() == "active"

    # Check every container, including replicas, for the expected labels.
    # Compose config alone is insufficient: Docker labels are immutable after
    # container creation.
    if sablier_enabled:
        compose_dir = shlex.quote(f"{homedir}/{service}")
        compose_base = shlex.quote(f"{homedir}/{service}/docker-compose.yml")
        compose_override = shlex.quote(
            f"{homedir}/{service}/docker-compose.sablier.yml"
        )
        expected_labels = shlex.quote(f"true|{sablier_group}")
        label_checks = []
        for service_name in sablier_services:
            compose_service = shlex.quote(service_name)
            label_checks.append(
                f'container_ids=$(/usr/bin/docker compose -f {compose_base} '
                f'-f {compose_override} ps -a -q {compose_service}); '
                'if [ -z "$container_ids" ]; then printf drift; exit 0; fi; '
                'actual_labels=$(/usr/bin/docker inspect --format '
                '\'{{ index .Config.Labels "sablier.enable" }}|'
                '{{ index .Config.Labels "sablier.group" }}\' $container_ids) || '
                '{ printf drift; exit 0; }; '
                f'if [ "$(printf "%s\\n" "$actual_labels" | sort -u)" '
                f'!= {expected_labels} ]; then printf drift; exit 0; fi;'
            )
        label_check_command = " ".join(label_checks) + " printf match"
        sablier_labels_match = (
            host.get_fact(Command, label_check_command) or ""
        ).strip() == "match"

        server.shell(
            name=f"Recreate {service} containers with Sablier labels",
            commands=[
                f"cd {compose_dir} && /usr/bin/docker compose "
                f"-f docker-compose.yml -f docker-compose.sablier.yml "
                "up --no-start --force-recreate"
            ],
            _sudo=False,
            _if=lambda: not sablier_labels_match,
        )
    else:
        sablier_labels_match = True

    server.shell(
        name=f"Reload systemd and ensure {service} is prepared",
        commands=[
            f"{systemctl_user} daemon-reload",
            f"{systemctl_user} enable {shlex.quote(service)}",
            f"{systemctl_user} {'restart' if service_active else 'start'} {shlex.quote(service)}",
        ],
        _sudo=False,
        _if=lambda: (
            any_changed(*restart_triggers)()
            or not service_active
        ),
    )

container = host.data.get("docker", {})

apt.packages(
    name="Install docker",
    packages=[
        "docker-ce",
        "docker-ce-cli",
        "docker-ce-rootless-extras",
    ],
    _sudo=True,
)

files.directory(
    name="Create docker directory structure",
    path=f"{homedir}/.docker/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="750",
)
