# pylint: disable=E0401
"""
Deploy and manage TasmoAdmin using Docker Compose.

Configuration:
    docker.tasmoadmin (dict):
        image (str): Docker image. Defaults to the official GHCR image.
        port (int): Local HTTP port. Defaults to 8016.

Persistent data:
    ~/.docker/tasmoadmin/data/
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

tasmoadmin = host.data.get("docker", {}).get("tasmoadmin", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

files.directory(
    name="Create TasmoAdmin data directory",
    path=f"{homedir}/.docker/tasmoadmin/data/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="tasmoadmin",
    description="TasmoAdmin Tasmota Management",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["tasmoadmin"],
    username=username,
    usergroup=usergroup,
    image=tasmoadmin.get("image", "ghcr.io/tasmoadmin/tasmoadmin:latest"),
    port=tasmoadmin.get("port", 8016),
)
