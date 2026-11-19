# pylint: disable=E0401
"""Deploy Huginn's web, worker and PostgreSQL services with private credentials.

Enable by adding docker.huginn with a public hostname to host/group data.
Required encrypted secrets: postgres_password, app_secret_token, seed_password
and invitation_code in secrets.docker.huginn. Never put them in group data.
The PostgreSQL database persists under homedir/.docker/huginn/postgres/.
"""

import builtins
import re

from pyinfra import host

from tasks.docker import deploy_docker_service, ensure_numeric_directory

huginn = host.data.get("docker", {}).get("huginn", {})
huginn_secrets = secrets.get("docker", {}).get("huginn", {})  # pylint: disable=undefined-variable

domain = huginn.get("domain")
if (
    not isinstance(domain, str)
    or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?", domain)
    or ".." in domain
):
    raise ValueError("docker.huginn.domain must be a hostname, optionally with a port")

port = huginn.get("port", 8028)
if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
    raise ValueError("docker.huginn.port must be an integer between 1 and 65535")

seed_username = huginn.get("seed_username", "admin")
if not isinstance(seed_username, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", seed_username):
    raise ValueError("docker.huginn.seed_username must be 1-64 letters, digits, _ or -")

enable_smokescreen = huginn.get("enable_smokescreen", True)
if not isinstance(enable_smokescreen, bool):
    raise ValueError("docker.huginn.enable_smokescreen must be a boolean")

required_secrets = ("postgres_password", "app_secret_token", "seed_password", "invitation_code")
missing = [
    name for name in required_secrets
    if not isinstance(huginn_secrets.get(name), str) or not huginn_secrets[name]
]
if missing:
    raise ValueError(
        "Huginn requires encrypted secrets under docker.huginn: " + ", ".join(missing)
    )

for name in required_secrets:
    value = huginn_secrets[name]
    if (
        len(value) < (32 if name == "app_secret_token" else 16)
        or not re.fullmatch(r"[A-Za-z0-9_-]+", value)
    ):
        raise ValueError(
            f"secrets.docker.huginn.{name} must be a URL-safe single-line "
            "random value (at least 32 chars for app_secret_token, 16 otherwise)"
        )

username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
homedir = host.data.get("homedir", getattr(builtins, "homedir", "/root"))

# PostgreSQL Alpine runs as UID/GID 70:70. The helper checks before changing
# directory ownership/mode; unchanged deployments do not report a change.
ensure_numeric_directory(f"{homedir}/.docker/huginn/postgres", 70, 70, "700")

deploy_docker_service(
    service="huginn",
    description="Huginn Automation Agents",
    homedir=homedir,
    compose_services=["db", "web", "threaded"],
    app_services=["web", "threaded"],
    username=username,
    usergroup=usergroup,
    image=huginn.get("image", "ghcr.io/huginn/huginn-single-process:latest"),
    postgres_image=huginn.get("postgres_image", "postgres:16-alpine"),
    port=port,
    domain=domain,
    seed_username=seed_username,
    enable_smokescreen="true" if enable_smokescreen else "false",
    private_env={
        "HUGINN_POSTGRES_PASSWORD": huginn_secrets["postgres_password"],
        "HUGINN_APP_SECRET_TOKEN": huginn_secrets["app_secret_token"],
        "HUGINN_SEED_PASSWORD": huginn_secrets["seed_password"],
        "HUGINN_INVITATION_CODE": huginn_secrets["invitation_code"],
    },
)
