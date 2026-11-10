# pylint: disable=E0401
"""
Deploy and manage Homepage using Docker Compose.

Configuration:
    docker.homepage (dict):
        image (str): Container image. Defaults to ghcr.io/gethomepage/homepage:latest.
        port (int): Local HTTP port. Defaults to 8020.
        domain (str): Hostname allowed by Homepage. Defaults to homepage.21x9.org.

Persistent configuration:
    ~/.docker/homepage/config/

Security:
    Homepage can display sensitive information through service widgets. Keep it
    behind a trusted reverse proxy, VPN, or Homepage's built-in authentication.
    Docker socket access is intentionally not enabled by this task.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

homepage = host.data.get("docker", {}).get("homepage", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# Homepage requires a writable configuration directory. Creating it before
# starting the container is idempotent and keeps ownership predictable.
files.directory(
    name="Create Homepage configuration directory",
    path=f"{homedir}/.docker/homepage/config/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="homepage",
    description="Homepage Dashboard",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=homepage.get("image", "ghcr.io/gethomepage/homepage:latest"),
    port=homepage.get("port", 8020),
    domain=homepage.get("domain", "homepage.21x9.org"),
)
