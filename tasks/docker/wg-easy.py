# pylint: disable=E0401
"""
Deploy WG-Easy v15 using Docker Compose.

Configuration:
    docker.wg-easy (dict):
        image (str): Container image. Defaults to ghcr.io/wg-easy/wg-easy:15.
        ui_port (int): Loopback-only web UI port. Defaults to 51821.

Persistent data:
    A host bind mount at ~/.docker/wg-easy/ stores
    WireGuard keys, peer configuration and WG-Easy application data.

The public WireGuard listener uses UDP port 51820. The web UI is bound
to loopback and is intended to be accessed through the configured Caddy
reverse proxy. WG-Easy v15 configures its public endpoint in the initial
setup wizard rather than through the legacy WG_HOST environment variable.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

wg_easy = host.data.get("docker", {}).get("wg-easy", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# Create the bind-mount directory before Docker starts the container.
files.directory(
    name="Create WG-Easy storage directory",
    path=f"{homedir}/.docker/wg-easy/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="wg-easy",
    description="WG-Easy WireGuard VPN",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["wg-easy"],
    username=username,
    usergroup=usergroup,
    image=wg_easy.get("image", "ghcr.io/wg-easy/wg-easy:15"),
    ui_port=wg_easy.get("ui_port", 51821),
)
