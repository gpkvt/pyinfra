"""
Manage APT package updates and installation using pyinfra.

This module updates the APT package index, upgrades installed packages, and installs additional packages defined in the host configuration.

Configuration: apt_packages (list[str]): Packages to install, retrieved from host.data.apt_packages. Defaults to an empty list.

Operations:

1. Update APT package sources, using a cache time of 4 hours.
2. Upgrade installed packages and automatically remove obsolete
   dependencies, only when the package index has changed.
3. Install each package specified in `apt_packages`.

Notes:

- Package index updates are cached for 14,400 seconds (4 hours).
- Package upgrades are conditional on the APT update operation
  reporting changes.
- Packages are installed individually using separate pyinfra
  operations.
"""

from pyinfra.operations import apt
from pyinfra import host

apt_packages = host.data.get("apt_packages", [])

apt_update = apt.update(
    name="Update apt sources",
    cache_time=14400
)

apt.upgrade(
    name="Update apt packages",
    auto_remove=True,
    _if=apt_update.did_change
)

for package in apt_packages:
    apt.packages (
        name=f"Install {package}",
        packages=[
            package
        ],
    )
