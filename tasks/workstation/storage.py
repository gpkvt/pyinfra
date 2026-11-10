"""
Install local storage health inspection tools.

Monitoring schedules and alert delivery are intentionally left to the user;
the task does not assume a server monitoring stack.
"""

from pyinfra import host
from pyinfra.operations import apt

config = host.data.get("workstation", {}).get("storage", {})
if config.get("enabled", False):
    apt.packages(
        name="Install storage health tools",
        packages=["smartmontools", "nvme-cli"],
        present=True,
        _sudo=True,
    )
