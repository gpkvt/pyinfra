# pylint: disable=E0401
"""
Deploy and manage Homepage using Docker Compose.

Configuration:
    docker.homepage (dict):
        image, port and domain configure the container and allowed hostname.
        settings, services, bookmarks, widgets, docker, kubernetes and proxmox
        are optional dictionaries/lists rendered as separate YAML files.

Persistent configuration:
    ~/.docker/homepage/config/

Security:
    Homepage can display sensitive information through service widgets. Keep it
    behind a trusted reverse proxy, VPN, or Homepage's built-in authentication.
    Docker socket access is intentionally not enabled by this task.
"""

import shlex

from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.operations import files, server, systemd

from tasks.docker import deploy_docker_service


class HomepageDockerSubnet(FactBase):
    """Return the IPv4 subnet of Homepage's Compose-managed default network."""

    command = (
        "docker network inspect homepage_default "
        "--format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || true"
    )

    def process(self, output):
        return next((line.strip() for line in output if line.strip()), None)


class HomepageUfwRules(FactBase):
    """Return UFW status lines, or an empty result when UFW is unavailable."""

    command = (
        "sudo sh -c 'command -v ufw >/dev/null 2>&1 && ufw status || true'"
    )

    def process(self, output):
        return output


def homepage_glances_ufw_rule_exists(subnet, bind_address, port):
    """Check for the exact source, destination and port allow rule."""
    expected = (subnet, bind_address, f"{port}/tcp", "ALLOW")
    return any(
        all(token in line.split() for token in expected)
        for line in host.get_fact(HomepageUfwRules)
    )


homepage = host.data.get("docker", {}).get("homepage", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")

# Deploy version-controlled service icons. Synchronization is additive so local-only
# icons are preserved when the task is run again.
files.directory(
    name="Create Homepage public icon directory",
    path=f"{homedir}/.docker/homepage/public/icons/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="755",
)

files.directory(
    name="Create Homepage public image directory",
    path=f"{homedir}/.docker/homepage/public/images/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="755",
)

files.sync(
    name="Deploy Homepage service icons",
    src="files/homepage/icons/",
    dest=f"{homedir}/.docker/homepage/public/icons/",  # pylint: disable=undefined-variable
    delete=False,
    _sudo=True,
)

# Homepage reads each configuration area from its own YAML file. Only render
# files explicitly present in host data, preserving Homepage defaults for the
# other areas and avoiding empty files that could override built-in behavior.
config_files = {
    "settings": "settings.yaml",
    "services": "services.yaml",
    "bookmarks": "bookmarks.yaml",
    "widgets": "widgets.yaml",
    "docker": "docker.yaml",
    "kubernetes": "kubernetes.yaml",
    "proxmox": "proxmox.yaml",
}

# Homepage requires a writable configuration directory. Creating it before
# rendering files is idempotent and keeps ownership predictable.
files.directory(
    name="Create Homepage configuration directory",
    path=f"{homedir}/.docker/homepage/config/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

for config_name, filename in config_files.items():
    config = homepage.get(config_name)

    if config is not None:
        files.template(
            name=f"Configure Homepage {config_name}",
            src=f"templates/docker/homepage/{filename}.j2",
            dest=f"{homedir}/.docker/homepage/config/{filename}",  # pylint: disable=undefined-variable
            user=username,
            group=usergroup,
            mode="640",
            config=config,
        )

# Run Glances as a system service so deployment does not depend on an
# interactive user's systemd session or D-Bus being available.
# host.docker.internal resolves to Docker's host-gateway address (172.17.0.1
# by default), not to the gateway address of Homepage's own Compose network.
glances = homepage.get("glances", {})
if glances:
    bind_address = glances.get("bind_address", "172.17.0.1")
    port = glances.get("port", 61208)

    glances_unit = files.template(
        name="Configure Glances web service",
        src="templates/docker/homepage/glances.service.j2",
        dest="/etc/systemd/system/glances-web.service",
        user="root",
        group="root",
        mode="644",
        username=username,
        usergroup=usergroup,
        homedir=homedir,  # pylint: disable=undefined-variable
        bind_address=bind_address,
        port=port,
        _sudo=True,
    )

    systemd.daemon_reload(
        name="Reload system systemd configuration",
        _if=glances_unit.did_change,
    )

    systemd.service(
        name="Ensure Glances web service is enabled and running",
        service="glances-web.service",
        running=True,
        enabled=True,
    )

    # The container reaches Glances through host.docker.internal. Permit only
    # the Homepage Compose subnet to access the host-gateway listener; do not
    # expose the metrics API on every interface or publish it through Compose.
    homepage_subnet = host.get_fact(HomepageDockerSubnet)
    if homepage_subnet:
        server.shell(
            name="Allow Homepage network to access Glances",
            commands=[
                "ufw allow from "
                f"{shlex.quote(homepage_subnet)} to "
                f"{shlex.quote(str(bind_address))} port "
                f"{shlex.quote(str(port))} proto tcp"
            ],
            _sudo=True,
            _if=lambda: not homepage_glances_ufw_rule_exists(
                homepage_subnet, str(bind_address), port
            ),
        )

    # Restart once when the unit changes so ExecStartPre can clean up a
    # manually started instance that would otherwise keep the port occupied.
    systemd.service(
        name="Restart Glances web service after unit changes",
        service="glances-web.service",
        restarted=True,
        _if=glances_unit.did_change,
    )

homepage_environment = homepage.get("environment", {}).copy()
homepage_environment.update(
    secrets.get("docker", {}).get("homepage", {}).get("environment", {})  # pylint: disable=undefined-variable
)

deploy_docker_service(
    service="homepage",
    description="Homepage Dashboard",
    homedir=homedir,  # pylint: disable=undefined-variable
    username=username,
    usergroup=usergroup,
    image=homepage.get("image", "ghcr.io/gethomepage/homepage:latest"),
    port=homepage.get("port", 8020),
    domain=homepage.get("domain", "homepage.21x9.org"),
    environment=homepage_environment,
)
