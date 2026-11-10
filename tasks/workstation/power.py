"""
Configure a conservative laptop power-management baseline.

Power Profiles Daemon and TLP are alternatives. This task installs only the
selected manager; it does not guess lid, suspend or battery-charge policies.
"""

from pyinfra import host
from pyinfra.operations import apt, server

config = host.data.get("workstation", {}).get("power", {})
if config.get("enabled", False):
    manager = config.get("manager", "power-profiles-daemon")
    if manager not in ("power-profiles-daemon", "tlp"):
        raise ValueError(
            "workstation.power.manager must be "
            "'power-profiles-daemon' or 'tlp'"
        )

    package = "power-profiles-daemon" if manager == "power-profiles-daemon" else "tlp"
    conflicting = "tlp" if manager == "power-profiles-daemon" else "power-profiles-daemon"

    apt.packages(
        name=f"Install {manager}",
        packages=[package],
        present=True,
        _sudo=True,
    )
    apt.packages(
        name=f"Remove conflicting power manager: {conflicting}",
        packages=[conflicting],
        present=False,
        _sudo=True,
    )
    server.service(
        name=f"Enable {manager}",
        service=manager,
        running=True,
        enabled=True,
        _sudo=True,
    )
