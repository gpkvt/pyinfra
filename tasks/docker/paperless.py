# pylint: disable=E0401
"""Deploy Paperless-ngx and its supporting services with Docker Compose.

Persistent application and database data use host bind mounts below
`~/.docker/paperless/`. Set the Paperless UID/GID to match the owner of the
host data directories (defaults to 1000:1000). PostgreSQL's data directory is
owned by the postgres:alpine container user (70:70).
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

paperless = host.data.get("docker", {}).get("paperless", {})
paperless_secrets = secrets.get("docker", {}).get("paperless", {})  # pylint: disable=undefined-variable
if not paperless_secrets.get("postgres_password") or not paperless_secrets.get("secret_key"):
    raise ValueError("Paperless-ngx requires docker.paperless.postgres_password and docker.paperless.secret_key in encrypted secrets")
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
uid = int(paperless.get("uid", 1000))
gid = int(paperless.get("gid", 1000))

# PostgreSQL 17 Alpine runs as UID/GID 70:70. files.directory checks the
# directory metadata and only applies changes when ownership or mode differs.
files.directory(
    name="Ensure Paperless PostgreSQL storage directory",
    path=f"{homedir}/.docker/paperless/postgres",  # pylint: disable=undefined-variable
    user="70",
    group="70",
    mode="700",
    _sudo=True,
)

# Paperless application storage.
for directory in ("data", "media", "consume", "export"):
    files.directory(
        name=f"Ensure Paperless {directory} storage directory",
        path=f"{homedir}/.docker/paperless/{directory}",  # pylint: disable=undefined-variable
        user=str(uid),
        group=str(gid),
        mode="750",
        _sudo=True,
    )

deploy_docker_service(
    service="paperless",
    description="Paperless-ngx Document Management",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=paperless.get("image", "ghcr.io/paperless-ngx/paperless-ngx:latest"),
    port=paperless.get("port", 8022),
    domain=paperless.get("domain", "paperless.21x9.org"),
    uid=uid,
    gid=gid,
    timezone=host.data.get("timezone", "UTC"),
    postgres_password=paperless_secrets.get("postgres_password", ""),
    secret_key=paperless_secrets.get("secret_key", ""),
)
