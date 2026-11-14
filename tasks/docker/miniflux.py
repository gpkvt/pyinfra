# pylint: disable=E0401
"""
Deploy and manage the Miniflux Docker service using pyinfra.

This module configures and deploys Miniflux using the shared
deploy_docker_service deployment defined in tasks/docker.py.

The Docker Compose configuration is generated from:
    templates/docker/miniflux/docker-compose.yml.j2

The systemd service unit is generated from:
    templates/docker/systemd.service.j2

Configuration:
    docker.miniflux (dict): Miniflux configuration retrieved from
        host.data.docker.miniflux.

        Supported options:
            postgres_version (int): PostgreSQL version used by Miniflux.
                Defaults to 12.

            port (int): Host port exposed by Miniflux.
                Defaults to 8080.

    secrets.docker.miniflux (dict): Miniflux credentials retrieved from
        the deployment secrets configuration.

        Supported options:
            postgres_password (str): PostgreSQL database password.
                Defaults to an empty string.

            admin_username (str): Miniflux administrator username.
                Defaults to an empty string.

            admin_password (str): Miniflux administrator password.
                Defaults to an empty string.

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
            miniflux

        description:
            Miniflux Docker Service

        Template variables:
            postgres_password
            postgres_version
            admin_username
            admin_password
            port
            homedir

File locations:
    Docker configuration directory:
        ~/.docker/miniflux/

    Docker Compose configuration:
        ~/miniflux/docker-compose.yml

    systemd service unit:
        ~/.config/systemd/user/miniflux.service

File permissions:
    - Docker configuration directory: 0750.
    - Docker Compose configuration: 0640.
    - systemd service unit: 0644.

Service:
    miniflux.service

    Managed through the user's systemd instance:

        systemctl --user daemon-reload
        systemctl --user enable miniflux
        systemctl --user restart miniflux

Notes:
    - Docker Compose and systemd configurations are generated using
      shared Jinja2 templates and deployment logic.
    - Database and administrator credentials are supplied through
      the deployment secrets configuration.
    - File deployment and service management run without sudo.
    - The systemd daemon is reloaded and the service enabled when
      the systemd unit file changes.
    - The service is restarted when either the Docker Compose
      configuration or systemd unit file changes.
    - Docker image updates are not automatically pulled.
"""

from pyinfra import host
from tasks.docker import deploy_docker_service

miniflux = host.data.get("docker", {}).get("miniflux", {})
miniflux_secrets = secrets.get("docker", {}).get("miniflux", {}) # pylint: disable=undefined-variable

deploy_docker_service(
    service="miniflux",
    description="Miniflux Docker Service",
    homedir=homedir, # pylint: disable=undefined-variable
    username=host.data.get("username", "root"),
    usergroup=host.data.get("usergroup", "root"),
    postgres_password=miniflux_secrets.get("postgres_password", ""),
    postgres_version=miniflux.get("postgres_version", 12),
    admin_username=miniflux_secrets.get("admin_username", ""),
    admin_password=miniflux_secrets.get("admin_password", ""),
    port=miniflux.get("port", 8080),
)
