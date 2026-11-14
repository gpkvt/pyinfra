# pylint: disable=E0401
"""
Deploy and manage the Grav CMS Docker service using pyinfra.

This module configures and deploys Grav using the shared
deploy_docker_service deployment defined in tasks/docker.py.

Configuration:
    docker.grav (dict): Grav configuration retrieved from
        host.data.docker.grav.

        Supported options:
            image (str): Docker image.
                Defaults to "getgrav/grav:1.7".

            port (int): Host port exposed by Grav.
                Defaults to 8080.

            channel (str): Grav release channel.
                Defaults to "stable".

            setup (bool): Automatically install Grav on an empty
                data directory.
                Defaults to True.

            scheduler (bool): Enable Grav scheduler.
                Defaults to True.

            fix_permissions (bool): Fix container file permissions
                on startup.
                Defaults to True.

    homedir (str): Home directory of the configured user.
    username (str): Owner of deployed files.
    usergroup (str): Group owning deployed files.

Operations:
    Delegates deployment and service management to
    deploy_docker_service().

File locations:
    Docker configuration:
        ~/.docker/grav/

    Grav persistent data:
        ~/.docker/grav/data/

    Docker Compose configuration:
        ~/.docker/grav/docker-compose.yml

    systemd service unit:
        ~/.config/systemd/user/grav.service

Notes:
    - Uses the official getgrav/grav Docker image.
    - Grav data persists outside the container.
    - The service is managed through user-level systemd.
    - Docker image updates are not automatically pulled.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

grav = host.data.get("docker", {}).get("grav", {})

username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# Create persistent Grav data directory
files.directory(
    name="Create Grav data directory",
    path=f"{homedir}/.docker/grav/data/", # pylint: disable=undefined-variable
    user="www-data",
    group="www-data",
    mode="750",
)

deploy_docker_service(
    service="grav",
    description="Grav CMS Docker Service",
    homedir=homedir, # pylint: disable=undefined-variable
    compose_services=["grav"],
    username=username,
    usergroup=usergroup,
    image=grav.get("image", "getgrav/grav:1.7"),
    port=grav.get("port", 8080),
    channel=grav.get("channel", "stable"),
    setup=grav.get("setup", True),
    scheduler=grav.get("scheduler", True),
    fix_permissions=grav.get("fix_permissions", True),
)
