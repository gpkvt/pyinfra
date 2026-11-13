# pylint: disable=E0401
"""Deploy Paperless-ngx and its supporting services with Docker Compose.

Persistent application and database data use host bind mounts below
`~/.docker/paperless/`. Set the Paperless UID/GID to match the owner of the
host data directories (defaults to 1000:1000). PostgreSQL's data directory is
owned by the postgres:alpine container user (70:70).
"""

from pyinfra import host
from pyinfra.operations import files
from tasks.docker import deploy_docker_service, ensure_numeric_directory

paperless = host.data.get("docker", {}).get("paperless", {})
paperless_secrets = secrets.get("docker", {}).get("paperless", {})  # pylint: disable=undefined-variable
if not paperless_secrets.get("postgres_password") or not paperless_secrets.get("secret_key"):
    raise ValueError("Paperless-ngx requires docker.paperless.postgres_password and docker.paperless.secret_key in encrypted secrets")
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
uid = int(paperless.get("uid", 1000))
gid = int(paperless.get("gid", 1000))

# PostgreSQL 17 Alpine runs as UID/GID 70:70.
ensure_numeric_directory(
    f"{homedir}/.docker/paperless/postgres", 70, 70, "700"  # pylint: disable=E0602
)

# Paperless application storage.
for directory in ("data", "media", "consume", "export"):
    ensure_numeric_directory(
        f"{homedir}/.docker/paperless/{directory}", uid, gid, "750"  # pylint: disable=E0602
    )

# Expose the consume directory at a convenient, non-hidden host path.
# Dropping files into ~/Paperless imports them into Paperless-ngx.
files.link(
    name="Create Paperless host import folder",
    path=f"{homedir}/Paperless",
    target=f"{homedir}/.docker/paperless/consume",
    user=username,
    group=usergroup,
    symbolic=True,
    _sudo=False,
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
