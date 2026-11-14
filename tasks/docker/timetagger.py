# pylint: disable=E0401
"""
Deploy TimeTagger with credentials stored in a private environment file.

Required secret:
    secrets.docker.timetagger.credentials: username:bcrypt-hash.

The secret is written to ~/.docker/timetagger/.env with mode 0600.
It is deliberately excluded from the Compose template so pyinfra diffs
never print the credential hash.
"""

import builtins
from io import StringIO

from pyinfra import host
from pyinfra.operations import files

from tasks.docker import deploy_docker_service

timetagger = host.data.get("docker", {}).get("timetagger", {})
timetagger_secrets = secrets.get("docker", {}).get("timetagger", {})  # pylint: disable=undefined-variable
credentials = timetagger_secrets.get("credentials")

if (
    not isinstance(credentials, str)
    or ":" not in credentials
    or not credentials.split(":", 1)[0]
    or not credentials.split(":", 1)[1]
    or any(character in credentials for character in ("\n", "\r", "\x00", '"', "'", "\\"))
):
    raise ValueError(
        "secrets.docker.timetagger.credentials must be a single-line "
        "username:bcrypt-hash value without quotes or backslashes"
    )

homedir = host.data.get("homedir", getattr(builtins, "homedir", "/root"))
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
service_dir = f"{homedir}/.docker/timetagger"

files.directory(
    name="Create TimeTagger Docker directory",
    path=service_dir,
    user=username,
    group=usergroup,
    mode="750",
    _sudo=False,
)

# Single quotes preserve bcrypt '$' characters as literal env-file content.
credentials_file = files.put(
    name="Configure private TimeTagger credentials",
    src=StringIO(f"TIMETAGGER_CREDENTIALS='{credentials}'\n"),
    dest=f"{service_dir}/.env",
    user=username,
    group=usergroup,
    mode="600",
    _sudo=False,
)

deploy_docker_service(
    service="timetagger",
    description="TimeTagger Docker Service",
    homedir=homedir,
    compose_services=["timetagger"],
    username=username,
    usergroup=usergroup,
    port=timetagger.get("port", 8080),
    restart_if=[credentials_file],
)
