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

from pyinfra import host
from pyinfra.operations import files, systemd

from tasks.docker import deploy_docker_service

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
    mode="775",
)

files.directory(
    name="Create Homepage public image directory",
    path=f"{homedir}/.docker/homepage/public/images/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="755",
)

homepage_icons = files.sync(
    name="Deploy Homepage service icons",
    src="files/homepage/icons/",
    dest=f"{homedir}/.docker/homepage/public/icons/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="664",
    dir_mode="775",
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

# Homepage loads custom.css directly from its config directory. Keep the
# bookmark-group sizing in CSS because settings.layout does not control it.
homepage_custom_css = files.put(
    name="Deploy Homepage custom CSS",
    src="files/homepage/custom.css",
    dest=f"{homedir}/.docker/homepage/config/custom.css",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="640",
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

    # Firewall access for this listener is managed centrally by tasks/ufw.py.

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
    compose_services=["homepage"],
    username=username,
    usergroup=usergroup,
    restart_if=[homepage_icons, homepage_custom_css],
    image=homepage.get("image", "ghcr.io/gethomepage/homepage:latest"),
    port=homepage.get("port", 8020),
    domain=homepage.get("domain", "homepage.21x9.org"),
    private_env=homepage_environment,
    environment_keys=sorted(homepage_environment),
)
