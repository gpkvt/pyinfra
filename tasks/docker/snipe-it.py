# pylint: disable=E0401
"""Deploy Snipe-IT asset management with MariaDB using Docker Compose."""

from pyinfra import host

from tasks.docker import deploy_docker_service, ensure_numeric_directory

snipe = host.data.get("docker", {}).get("snipe-it", {})
snipe_secrets = secrets.get("docker", {}).get("snipe-it", {})  # pylint: disable=undefined-variable

required_secrets = ("database_password", "mysql_root_password", "app_key")
missing_secrets = [key for key in required_secrets if not snipe_secrets.get(key)]
if missing_secrets:
    raise ValueError(
        "Snipe-IT requires these encrypted secrets under docker.snipe-it: "
        + ", ".join(missing_secrets)
    )

username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# MariaDB's official image runs its database process as UID/GID 999:999.
ensure_numeric_directory(
    f"{homedir}/.docker/snipe-it/database", 999, 999, "750"  # pylint: disable=E0602
)

# The official Snipe-IT image runs its application as UID 10000, GID 50.
ensure_numeric_directory(
    f"{homedir}/.docker/snipe-it/storage", 10000, 50, "750"  # pylint: disable=E0602
)

deploy_docker_service(
    service="snipe-it",
    description="Snipe-IT Asset Management",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["db","app"],
    username=username,
    usergroup=usergroup,
    image=snipe.get("image", "snipe/snipe-it:latest"),
    port=snipe.get("port", 8025),
    domain=snipe.get("domain", "snipeit.21x9.org"),
    timezone=host.data.get("timezone", "UTC"),
    database_password=snipe_secrets["database_password"],
    mysql_root_password=snipe_secrets["mysql_root_password"],
    app_key=snipe_secrets["app_key"],
)
