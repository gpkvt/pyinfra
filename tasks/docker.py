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
        _if=lambda: host.get_fact(Command, check_command) != [expected],
    )


if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

@deploy("Deploy Docker service")
def deploy_docker_service( # pylint: disable=R0913,R0917
    service,
    description,
    homedir,
    username="root",
    usergroup="root",
    restart_if=None,
    **template_vars,
):
    # Create Docker service directory
    files.directory(
        name=f"Create {service} directory",
        path=f"{homedir}/.docker/{service}/",
        user=username,
        group=usergroup,
        mode="750",
    )

    # Deploy Docker Compose configuration
    compose_file = files.template(
        name=f"Configure {service}",
        src=f"templates/docker/{service}/docker-compose.yml.j2",
        dest=f"{homedir}/{service}/docker-compose.yml",
        user=username,
        group=usergroup,
        mode="640",
        homedir=homedir,
        **template_vars,
        _sudo=False,
    )

    # Pull Docker images before restarting the service
    server.shell(
        name=f"Pull {service} Docker images",
        commands=[
            f"docker compose -f {homedir}/{service}/docker-compose.yml pull",
        ],
        _sudo=False,
        _if=compose_file.did_change,
    )

    # Deploy systemd unit
    systemd_unit = files.template(
        name=f"Deploy {service} systemd service",
        src="templates/docker/systemd.service.j2",
        dest=f"{homedir}/.config/systemd/user/{service}.service",
        user=username,
        group=usergroup,
        homedir=homedir,
        service=service,
        description=description,
        mode="644",
        _sudo=False,
    )

    # Reload systemd when the unit changes
    server.shell(
        name=f"Reload systemd for {service}",
        commands=[
            "systemctl --user daemon-reload",
            f"systemctl --user enable {service}",
        ],
        _sudo=False,
        _if=systemd_unit.did_change,
    )

    # Restart service when its configuration or an additional input changes.
    restart_triggers = [compose_file, systemd_unit]
    if restart_if is not None:
        restart_triggers.append(restart_if)

    server.shell(
        name=f"Restart {service}",
        commands=[
            f"systemctl --user restart {service}",
        ],
        _sudo=False,
        _if=any_changed(*restart_triggers),
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
