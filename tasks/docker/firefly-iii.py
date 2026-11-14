# pylint: disable=E0401
"""Deploy Firefly III, MariaDB, cron and the FinTS importer.

All persistent state is stored in host directories below ~/.docker/firefly-iii/.
Secrets are read from secrets.docker.firefly-iii in the encrypted secrets file.
"""

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service, ensure_numeric_directory

firefly = host.data.get("docker", {}).get("firefly-iii", {})
firefly_secrets = secrets.get("docker", {}).get("firefly-iii", {})  # pylint: disable=undefined-variable

required_secrets = ("database_password", "mysql_root_password", "app_key", "cron_token")
missing_secrets = [key for key in required_secrets if not firefly_secrets.get(key)]
if missing_secrets:
    raise ValueError(
        "Firefly III requires these encrypted secrets under docker.firefly-iii: "
        + ", ".join(missing_secrets)
    )
if len(firefly_secrets["cron_token"]) != 32:
    raise ValueError("Firefly III cron_token must be exactly 32 characters")

username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# MariaDB's official image runs its database process as mysql (UID/GID 999).
ensure_numeric_directory(
    f"{homedir}/.docker/firefly-iii/database", 999, 999, "750" # pylint: disable=E0602
)

# Firefly III's upload storage is writable by its www-data user (UID/GID 33).
ensure_numeric_directory(
    f"{homedir}/.docker/firefly-iii/upload", 33, 33, "750" # pylint: disable=E0602
)

# The FinTS importer persists bank connection configurations here.
files.directory(
    name="Ensure Firefly III FinTS configuration directory",
    path=f"{homedir}/.docker/firefly-iii/fints",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

deploy_docker_service(
    service="firefly-iii",
    description="Firefly III Personal Finance",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["db","app","cron","fints"],
    username=username,
    usergroup=usergroup,
    image=firefly.get("image", "fireflyiii/core:latest"),
    port=firefly.get("port", 8023),
    domain=firefly.get("domain", "firefly.21x9.org"),
    fints_port=firefly.get("fints_port", 8024),
    fints_domain=firefly.get("fints_domain", "fints.21x9.org"),
    timezone=host.data.get("timezone", "UTC"),
    private_env={
        "DATABASE_PASSWORD": firefly_secrets["database_password"],
        "MYSQL_ROOT_PASSWORD": firefly_secrets["mysql_root_password"],
        "APP_KEY": firefly_secrets["app_key"],
        "STATIC_CRON_TOKEN": firefly_secrets["cron_token"],
    },
)
