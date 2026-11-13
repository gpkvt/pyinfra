"""Deploy the official AppFlowy Self-Hosted Commercial Compose stack."""

import builtins
import re

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files

from tasks.docker import deploy_docker_service, ensure_numeric_directory

appflowy = host.data.get("docker", {}).get("appflowy", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
homedir = host.data.get("homedir", getattr(builtins, "homedir", "/root"))
appflowy_secrets = getattr(builtins, "secrets", {}).get("docker", {}).get("appflowy", {})

required_secrets = (
    "postgres_password",
    "admin_password",
    "jwt_secret",
    "minio_access_key",
    "minio_secret_key",
)
missing = [key for key in required_secrets if not appflowy_secrets.get(key)]
if missing:
    raise ValueError(
        "Missing required secrets.docker.appflowy values: " + ", ".join(missing)
    )

# These values are interpolated into PostgreSQL connection URLs and must not
# require URL encoding. Keep the check narrow and never include secret values.
for key in ("postgres_password",):
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,}", appflowy_secrets[key]):
        raise ValueError(
            f"secrets.docker.appflowy.{key} must be at least 32 URL-safe characters"
        )
if not re.fullmatch(r"[A-Za-z0-9_-]{32,}", appflowy_secrets["jwt_secret"]):
    raise ValueError(
        "secrets.docker.appflowy.jwt_secret must be at least 32 URL-safe characters"
    )
if not re.fullmatch(r"[A-Za-z0-9_-]{20,}", appflowy_secrets["minio_access_key"]):
    raise ValueError(
        "secrets.docker.appflowy.minio_access_key must be at least 20 URL-safe characters"
    )
if not re.fullmatch(r"[A-Za-z0-9_-]{32,}", appflowy_secrets["minio_secret_key"]):
    raise ValueError(
        "secrets.docker.appflowy.minio_secret_key must be at least 32 URL-safe characters"
    )

port = appflowy.get("port", 8026)
domain = appflowy.get("domain", "appflowy.21x9.org")
admin_email = appflowy.get("admin_email", "admin@appflowy.21x9.org")

data_root = f"{homedir}/.docker/appflowy"
for path in (
    data_root,
    f"{data_root}/nginx",
    f"{homedir}/appflowy",
):
    files.directory(
        name=f"Create AppFlowy directory {path}",
        path=path,
        user=username,
        group=usergroup,
        mode="750",
    )

# PostgreSQL's official image runs its entrypoint as root and fixes ownership
# to its postgres user before starting the database.
ensure_numeric_directory(f"{data_root}/postgres", 999, 999, "700")
# MinIO and AppFlowy Search run as unprivileged container users. Their data
# directories are deliberately writable without making them world-accessible.
files.directory(
    name="Create AppFlowy MinIO data directory",
    path=f"{data_root}/minio",
    user=username,
    group=usergroup,
    mode="770",
)
files.directory(
    name="Create AppFlowy Search index directory",
    path=f"{data_root}/search",
    user=username,
    group=usergroup,
    mode="770",
)

env_file = files.template(
    name="Configure AppFlowy environment",
    src="templates/docker/appflowy/.env.j2",
    dest=f"{homedir}/appflowy/.env",
    user=username,
    group=usergroup,
    mode="600",
    postgres_password=appflowy_secrets["postgres_password"],
    admin_email=admin_email,
    admin_password=appflowy_secrets["admin_password"],
    jwt_secret=appflowy_secrets["jwt_secret"],
    minio_access_key=appflowy_secrets["minio_access_key"],
    minio_secret_key=appflowy_secrets["minio_secret_key"],
    _sudo=False,
)

nginx_config = files.template(
    name="Configure AppFlowy Nginx reverse proxy",
    src="templates/docker/appflowy/nginx.conf.j2",
    dest=f"{data_root}/nginx.conf",
    user=username,
    group=usergroup,
    mode="640",
    _sudo=False,
)

deploy_docker_service(
    service="appflowy",
    description="AppFlowy Self-Hosted",
    homedir=homedir,
    username=username,
    usergroup=usergroup,
    restart_if=[env_file, nginx_config],
    app_services=appflowy.get("app_services", ["nginx"]),
    port=port,
)
