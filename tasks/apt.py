"""
Manage APT package updates, upgrades, and installations.

This module provides package management for Debian-based Linux hosts
using pyinfra.

Configuration:
    apt_packages (list[str]): Packages to install, retrieved from
        host.data.apt_packages. Defaults to an empty list.

Execution:
    1. Update APT package sources, using a cache time of four hours.
    2. Upgrade installed packages and automatically remove obsolete
       dependencies, if the package index has changed.
    3. Install each configured package individually.
"""

from pyinfra import host
from pyinfra.operations import apt, files

def update_apt_sources():
    """
    Update the APT package index.

    Refreshes the local package index from configured repositories.
    The update is cached for 14,400 seconds (four hours).

    Returns:
        The pyinfra operation result, used to determine whether
        the package index has changed.
    """
    return apt.update(
        name="Update apt sources",
        cache_time=14400,
    )

def upgrade_apt_packages(update_result):
    """
    Upgrade installed APT packages.

    Upgrades available packages and automatically removes obsolete
    dependencies.

    The operation runs only when the preceding APT index update
    reports changes.

    Args:
        update_result: Result of the APT package index update.
    """
    apt.upgrade(
        name="Update apt packages",
        auto_remove=True,
        _if=update_result.did_change,
    )

def install_apt_package(package_name):
    """
    Install an individual APT package.

    Ensures that the specified package is installed on the target
    host. Each package is handled as a separate pyinfra operation.

    Args:
        package_name (str): Name of the package to install.
    """
    apt.packages(
        name=f"Install {package_name}",
        packages=[package_name],
    )

print(__doc__)

# Ensure keyring directory exists
files.directory(
    name="Ensure APT keyrings directory exists",
    path="/etc/apt/keyrings",
    mode="0755",
)

apt_sources = host.data.get("apt_sources", {})

for name, repo in host.data.apt_sources.items():
    key = repo["key"]
    repository = repo["repository"]

    files.download(
        name=f"Download {name} GPG key",
        src=key["url"],
        dest=key["path"],
        mode="0644",
    )

    architectures = repository.get("architectures", [])
    components = repository.get("components", [])

    options = [f"signed-by={key['path']}"]

    if architectures:
        options.append(f"arch={','.join(architectures)}")

    source_lines = []

    for repo_type in repository.get("types", ["deb"]):
        source = (
            f"{repo_type} "
            f"[{' '.join(options)}] "
            f"{repository['url']} "
            f"{repository['distribution']}"
        )

        if components:
            source += " " + " ".join(components)

        source_lines.append(source)

    files.template(
        name=f"Configure {name} APT repository",
        src="templates/apt_repository.list.j2",
        dest=f"/etc/apt/sources.list.d/{name}.list",
        mode="0644",
        repo_lines=source_lines,
    )

# Retrieve configured packages.
apt_packages = host.data.get("apt_packages", [])

# Execute package management operations.
print("update_apt_sources():")
print(update_apt_sources.__doc__)
apt_update = update_apt_sources()

print("update_apt_packages():")
print(upgrade_apt_packages.__doc__)
upgrade_apt_packages(apt_update)

print("install_apt_package():")
print(install_apt_package.__doc__)
for package in apt_packages:
    install_apt_package(package)
