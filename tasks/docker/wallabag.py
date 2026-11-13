# pylint: disable=E0401
"""
Deploy and manage Wallabag using Docker Compose.

Configuration:
    docker.wallabag (dict):
        image (str): Wallabag image. Defaults to wallabag/wallabag:latest.
        port (int): Host loopback port. Defaults to 8017.
        domain (str): Public HTTPS URL. Defaults to https://wallabag.21x9.org.

Persistent data:
    Docker-managed named volumes store the SQLite database, application
    data, and article images. Docker manages their ownership so the
    container's www-data process can write to them.

The shared Docker deployment helper manages the Compose file and
user-level systemd service. Unchanged configuration does not trigger
image pulls or service restarts.
"""

from pyinfra import host

from tasks.docker import deploy_docker_service

wallabag = host.data.get("docker", {}).get("wallabag", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

deploy_docker_service(
    service="wallabag",
    description="Wallabag Read-it-later Service",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["wallabag"],
    username=username,
    usergroup=usergroup,
    image=wallabag.get("image", "wallabag/wallabag:latest"),
    port=wallabag.get("port", 8017),
    domain=wallabag.get("domain", "https://wallabag.21x9.org"),
)
