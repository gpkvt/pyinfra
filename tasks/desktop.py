"""
Install common desktop integration utilities.

This task avoids changing desktop-environment-specific settings. COSMIC,
GNOME, KDE and other desktop preferences should be configured by their
respective dedicated modules.
"""

from pyinfra import host
from pyinfra.operations import apt

config = host.data.get("workstation", {}).get("desktop", {})
if config.get("enabled", False):
    packages = config.get(
        "packages",
        ["xdg-utils", "xdg-user-dirs", "xdg-user-dirs-gtk"],
    )
    if not isinstance(packages, list) or not all(
        isinstance(package, str) and package for package in packages
    ):
        raise ValueError("workstation.desktop.packages must be a list of package names")

    if packages:
        apt.packages(
            name="Install desktop integration utilities",
            packages=packages,
            present=True,
            _sudo=True,
        )
