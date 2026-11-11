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
from pyinfra.operations import files

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
    mode="750",
)

files.directory(
    name="Create Homepage public image directory",
    path=f"{homedir}/.docker/homepage/public/images/",  # pylint: disable=undefined-variable
    user=username,
    group=usergroup,
    mode="750",
)

files.sync(
    name="Deploy Homepage service icons",
    src="files/homepage/icons/",
    dest=f"{homedir}/.docker/homepage/public/icons/",  # pylint: disable=undefined-variable
    delete=False,
    user=username,
    group=usergroup,
    mode="644",
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
