# pylint: disable=E0401
"""
Deploy AdGuard Home as a Docker container.

Configuration:
    docker.adguard_home (dict):
        image (str): AdGuard Home image. Defaults to adguard/adguardhome:v0.107.80.

Persistent data:
    ~/.docker/adguard-home/conf/
    ~/.docker/adguard-home/work/

The container uses host networking so DNS can listen directly on port 53.
Restrict access to trusted LAN and WireGuard networks with the host firewall.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

adguard_home = host.data.get("docker", {}).get("adguard_home", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

for directory in ("conf", "work"):
    files.directory(
        name=f"Create AdGuard Home {directory} directory",
        path=f"{homedir}/.docker/adguard-home/{directory}/",  # pylint: disable=undefined-variable
        user=username,
        group=usergroup,
        mode="750",
    )

deploy_docker_service(
    service="adguard-home",
    description="AdGuard Home DNS",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["adguard-home"],
    username=username,
    usergroup=usergroup,
    image=adguard_home.get("image", "adguard/adguardhome:v0.107.80"),
)
