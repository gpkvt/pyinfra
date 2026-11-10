# pylint: disable=E0401
"""
Deploy and manage Portainer CE using Docker Compose.

Configuration:
    docker.portainer (dict):
        image (str): Portainer CE image. Defaults to portainer/portainer-ce:lts.
        port (int): Host loopback port for the HTTP interface. Defaults to 9000.

Persistent data:
    ~/.docker/portainer/data/

Security:
    Portainer mounts the Docker socket and therefore has administrative
    control over the Docker host. Its HTTP port is bound to loopback and
    should only be exposed through a trusted, authenticated reverse proxy.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

portainer = host.data.get("docker", {}).get("portainer", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

files.directory(
    name="Create Portainer data directory",
    path=f"{homedir}/.docker/portainer/data/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="portainer",
    description="Portainer Docker Management",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=portainer.get("image", "portainer/portainer-ce:lts"),
    port=portainer.get("port", 9000),
)
