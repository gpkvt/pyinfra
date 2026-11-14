# pylint: disable=E0401
"""
Deploy TimeTagger with credentials supplied exclusively through encrypted secrets.

Required secret:
    secrets.docker.timetagger.credentials: username:bcrypt-hash.
"""

from pyinfra import host
from tasks.docker import deploy_docker_service

timetagger = host.data.get("docker", {}).get("timetagger", {})
timetagger_secrets = secrets.get("docker", {}).get("timetagger", {})  # pylint: disable=undefined-variable
credentials = timetagger_secrets.get("credentials")

if (
    not isinstance(credentials, str)
    or ":" not in credentials
    or not credentials.split(":", 1)[0]
    or not credentials.split(":", 1)[1]
    or any(character in credentials for character in ("\n", "\r", "\x00", '"', "'"))
):
    raise ValueError(
        "secrets.docker.timetagger.credentials must be a single-line "
        "username:bcrypt-hash value"
    )

deploy_docker_service(
    service="timetagger",
    description="TimeTagger Docker Service",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["timetagger"],
    username=host.data.get("username", "root"),
    usergroup=host.data.get("usergroup", "root"),
    port=timetagger.get("port", 8080),
    credentials=credentials.replace("$", "$$"),
)
