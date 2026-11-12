# pylint: disable=E0401
"""
Deploy and manage Linkwarden using Docker Compose.

Configuration:
    docker.linkwarden (dict):
        image (str): Linkwarden image. Defaults to ghcr.io/linkwarden/linkwarden:latest.
        port (int): Host loopback port. Defaults to 8021.
        domain (str): Public hostname. Defaults to linkwarden.21x9.org.

Secrets:
    secrets.docker.linkwarden (dict):
        postgres_password (str): URL-safe PostgreSQL password.
        nextauth_secret (str): Secret used to sign authentication sessions.
        meili_master_key (str): Meilisearch master key.

Persistent data:
    Host bind mounts at:
        ~/.docker/linkwarden/postgres/
        ~/.docker/linkwarden/data/
        ~/.docker/linkwarden/meili/
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service, ensure_numeric_directory

linkwarden = host.data.get("docker", {}).get("linkwarden", {})
linkwarden_secrets = secrets.get("docker", {}).get("linkwarden", {})  # pylint: disable=undefined-variable
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# PostgreSQL 16 Alpine runs as UID/GID 70:70 and needs exclusive access.
ensure_numeric_directory(
    f"{homedir}/.docker/linkwarden/postgres", 70, 70, "700"  # pylint: disable=E0602
)

for directory in ("data", "meili"):
    files.directory(
        name=f"Create Linkwarden {directory} storage directory",
        path=f"{homedir}/.docker/linkwarden/{directory}/", # pylint: disable=E0602
        user=username,
        group=usergroup,
        mode="750",
    )

deploy_docker_service(
    service="linkwarden",
    description="Linkwarden Bookmark Manager",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=linkwarden.get("image", "ghcr.io/linkwarden/linkwarden:latest"),
    port=linkwarden.get("port", 8021),
    domain=linkwarden.get("domain", "linkwarden.21x9.org"),
    postgres_password=linkwarden_secrets.get("postgres_password", ""),
    nextauth_secret=linkwarden_secrets.get("nextauth_secret", ""),
    meili_master_key=linkwarden_secrets.get("meili_master_key", ""),
)
