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
from pyinfra.operations import apt

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
