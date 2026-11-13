# pylint: disable=E0401
"""
Deploy and manage the TimeTagger Docker service using pyinfra.

This module configures and deploys TimeTagger using the shared
deploy_docker_service deployment defined in tasks/docker.py.

The Docker Compose configuration is generated from:
    templates/docker/timetagger/docker-compose.yml.j2

The systemd service unit is generated from:
    templates/docker/systemd.service.j2

Configuration:
    docker.timetagger (dict): TimeTagger configuration retrieved from
        host.data.docker.timetagger.

        Supported options:
            port (int): Host port exposed by TimeTagger.
                Defaults to 8080.

    homedir (str): Home directory of the configured user.
        Defined globally in the main deployment configuration.

    username (str): User who owns deployed files and directories.
        Retrieved from host.data.username. Defaults to "root".

    usergroup (str): Group that owns deployed files and directories.
        Retrieved from host.data.usergroup. Defaults to "root".

Operations:
    Delegates deployment and service management to deploy_docker_service()
    with the following parameters:

        service:
            timetagger

        description:
            TimeTagger Docker Service

        Template variables:
            port
            homedir

File locations:
    Docker configuration directory:
        ~/.docker/timetagger/

    Docker Compose configuration:
        ~/.docker/timetagger/docker-compose.yml

    systemd service unit:
        ~/.config/systemd/user/timetagger.service

File permissions:
    - Docker configuration directory: 0750.
    - Docker Compose configuration: 0640.
    - systemd service unit: 0644.

Service:
    timetagger.service

    Managed through the user's systemd instance:

        systemctl --user daemon-reload
        systemctl --user enable timetagger
        systemctl --user restart timetagger

Notes:
    - Docker Compose and systemd configurations are generated using
      shared Jinja2 templates and deployment logic.
    - The exposed port is configurable through host configuration.
    - File deployment and service management run without sudo.
    - The systemd daemon is reloaded and the service enabled when
      the systemd unit file changes.
    - The service is restarted when either the Docker Compose
      configuration or systemd unit file changes.
    - Docker image updates are not automatically pulled.
"""

from pyinfra import host
from tasks.docker import deploy_docker_service

timetagger = host.data.get("docker", {}).get("timetagger", {})

deploy_docker_service(
    service="timetagger",
    description="TimeTagger Docker Service",
    homedir=homedir, # pylint: disable=undefined-variable
    username=host.data.get("username", "root"),
    usergroup=host.data.get("usergroup", "root"),
    port=timetagger.get("port", 8080),
)
