# pylint: disable=E0401
"""
Deploy and manage NocoDB using Docker Compose.

Configuration:
    docker.nocodb (dict):
        image (str): Container image. Defaults to nocodb/nocodb:latest.
        port (int): Local HTTP port. Defaults to 8019.
        domain (str): Public URL. Defaults to https://nocodb.21x9.org.

Persistent data:
    ~/.docker/nocodb/data/
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

nocodb = host.data.get("docker", {}).get("nocodb", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# Ensure the persistent application directory exists with stable ownership.
files.directory(
    name="Create NocoDB data directory",
    path=f"{homedir}/.docker/nocodb/data/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="nocodb",
    description="NocoDB Database Platform",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=nocodb.get("image", "nocodb/nocodb:latest"),
    port=nocodb.get("port", 8019),
    domain=nocodb.get("domain", "https://nocodb.21x9.org"),
)
