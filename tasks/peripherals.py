"""
Install optional desktop peripheral support.

Printer/scanner support is opt-in because not every workstation needs it.
"""

from pyinfra import host
from pyinfra.operations import apt, server

config = host.data.get("workstation", {}).get("peripherals", {})
if config.get("enabled", False):
    packages = []
    if config.get("printing", False):
        packages.extend(["cups", "cups-client", "system-config-printer"])
    if config.get("scanning", False):
        packages.extend(["sane-utils", "simple-scan"])

    if packages:
        apt.packages(
            name="Install desktop peripheral support",
            packages=packages,
            present=True,
            _sudo=True,
        )

    if config.get("printing", False):
        server.service(
            name="Enable local printing service",
            service="cups",
            running=True,
            enabled=True,
            _sudo=True,
        )
