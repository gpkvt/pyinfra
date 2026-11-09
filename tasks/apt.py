"""
Manage APT package updates, upgrades, and installations.

This module provides package management for Debian-based Linux hosts
using pyinfra.

Configuration:
    apt_packages (list[str]): Packages to install, retrieved from
        host.data.apt_packages. Defaults to an empty list.

    apt_sources (dict): Third-party APT repositories to configure,
        including their signing keys and repository definitions.

Execution:
    1. Ensure the APT keyrings directory exists.
    2. Download repository signing keys and configure repositories.
    3. Force an APT update when repositories have changed.
    4. Otherwise, update APT sources using a four-hour cache.
    5. Upgrade installed packages and remove obsolete dependencies
       when the package index has changed.
    6. Install each configured package individually.
"""

from pyinfra import host
from pyinfra.operations import apt, files
from pyinfra.operations.util import any_changed

def update_apt_sources(repository_operations):
    """
    Update the APT package index.

    Forces an update when any repository configuration has changed.
    Otherwise, uses a four-hour cache.

    Args:
        repository_operations: Repository configuration operations.

    Returns:
        A tuple containing the forced and cached update operations.
    """
    repositories_changed = any_changed(*repository_operations)

    forced_update = apt.update(
        name="Force APT update (repositories changed)",
        _if=repositories_changed,
    )

    cached_update = apt.update(
        name="Update APT sources",
        cache_time=14400,
        _if=lambda: not repositories_changed(),
    )

    return forced_update, cached_update

def upgrade_apt_packages(update_operations):
    """
    Upgrade installed APT packages.

    Upgrades available packages and automatically removes obsolete
    dependencies.

    Runs only when an APT index update has changed the package index.

    Args:
        update_operations: APT update operation results.
    """
    apt.upgrade(
        name="Update apt packages",
        auto_remove=True,
        _if=any_changed(*update_operations),
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

# Ensure keyring directory exists.
files.directory(
    name="Ensure APT keyrings directory exists",
    path="/etc/apt/keyrings",
    mode="0755",
)

# Retrieve configured APT repositories.
apt_sources = host.data.get("apt_sources", {})

# Track repository configuration operations.
apt_repository_operations = []

for name, repo in apt_sources.items():
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

    repository_operation = files.template(
        name=f"Configure {name} APT repository",
        src="templates/apt_repository.list.j2",
        dest=f"/etc/apt/sources.list.d/{name}.list",
        mode="0644",
        repo_lines=source_lines,
    )

    apt_repository_operations.append(repository_operation)

# Retrieve configured packages.
apt_packages = host.data.get("apt_packages", [])

# Execute package management operations.
print("update_apt_sources():")
print(update_apt_sources.__doc__)

apt_update = update_apt_sources(apt_repository_operations)

print("upgrade_apt_packages():")
print(upgrade_apt_packages.__doc__)

upgrade_apt_packages(apt_update)

print("install_apt_package():")
print(install_apt_package.__doc__)

for package in apt_packages:
    install_apt_package(package)
