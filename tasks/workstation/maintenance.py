"""
Install opt-in workstation maintenance utilities.

This task does not enable unattended upgrades or schedule automatic reboots.
Update policy remains an explicit workstation-owner decision.
"""

from pyinfra import host
from pyinfra.operations import apt

config = host.data.get("workstation", {}).get("maintenance", {})
if config.get("enabled", False):
    apt.packages(
        name="Install workstation maintenance utilities",
        packages=["needrestart", "debian-goodies", "apt-file"],
        present=True,
        _sudo=True,
    )
