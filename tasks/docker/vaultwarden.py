# pylint: disable=E0401
"""
Deploy and manage Vaultwarden using Docker Compose.

Configuration:
    docker.vaultwarden (dict):
        image (str): Container image. Defaults to vaultwarden/server:latest.
        port (int): Host loopback port. Defaults to 8018.
        domain (str): Public HTTPS URL.

Secrets:
    secrets.docker.vaultwarden.admin_token (str): Optional Argon2 PHC hash
        protecting the administrative interface. Generate it with the
        upstream container's /vaultwarden hash command.

Persistent data:
    The Vaultwarden data directory is bind-mounted from
    ~/.docker/vaultwarden/; no Docker-managed volume is used.

Security:
    Public signups and invitations are disabled by default. The HTTP
    interface is bound to loopback and should be exposed only through
    a trusted HTTPS reverse proxy.
"""

from pyinfra import host

from tasks.docker import deploy_docker_service

vaultwarden = host.data.get("docker", {}).get("vaultwarden", {})
vaultwarden_secrets = secrets.get("docker", {}).get("vaultwarden", {})  # pylint: disable=undefined-variable
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

deploy_docker_service(
    service="vaultwarden",
    description="Vaultwarden Password Manager",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=vaultwarden.get("image", "vaultwarden/server:latest"),
    port=vaultwarden.get("port", 8018),
    domain=vaultwarden.get("domain", "https://vaultwarden.21x9.org"),
    admin_token=vaultwarden_secrets.get("admin_token", ""),
)
