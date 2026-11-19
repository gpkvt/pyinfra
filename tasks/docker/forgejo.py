# pylint: disable=E0401
"""
Deploy and manage a Forgejo Git service using Docker Compose.

Configuration:
    docker.forgejo (dict):
        image (str): Container image. Defaults to the stable Forgejo image.
        port (int): Local HTTP host port. Defaults to 8027.
        ssh_port (int): Local Git SSH port. Defaults to 2222.
        domain (str): Public hostname used by Forgejo. Defaults to
            forgejo.21x9.org.

Persistent data:
    ~/.docker/forgejo/data/

The shared Docker deployment helper manages the Compose file and
user-level systemd service. Unchanged configuration does not trigger
image pulls or service restarts.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

forgejo = host.data.get("docker", {}).get("forgejo", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

port = forgejo.get("port", 8027)
if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
    raise ValueError("docker.forgejo.port must be an integer between 1 and 65535")

# Keep persistent data owned by the configured host user.
files.directory(
    name="Create Forgejo data directory",
    path=f"{homedir}/.docker/forgejo/data/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="forgejo",
    description="Forgejo Git Service",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["forgejo"],
    username=username,
    usergroup=usergroup,
    image=forgejo.get("image", "codeberg.org/forgejo/forgejo:17"),
    port=port,
    ssh_port=forgejo.get("ssh_port", 2222),
    ssh_server=forgejo.get("ssh_server", False),
    domain=forgejo.get("domain", "forgejo.21x9.org"),
)
