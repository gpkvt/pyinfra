"""Deploy a minimal Docker container for CI integration testing."""

from pyinfra import host

from tasks.docker import deploy_docker_service

config = host.data.get("docker", {}).get("ci-smoke", {})

deploy_docker_service(
    service="ci-smoke",
    description="CI Docker smoke test",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["smoke"],
    username=host.data.get("username", "root"),
    usergroup=host.data.get("usergroup", "root"),
    image=config.get("image", "alpine:3.21"),
    app_services=config.get("app_services", ["smoke"]),
)
