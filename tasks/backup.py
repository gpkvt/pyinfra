"""
Install workstation backup tools.

This task deliberately does not create or run a backup job: repository
locations, credentials, retention and source paths must be chosen explicitly.
"""

from pyinfra import host
from pyinfra.operations import apt

config = host.data.get("workstation", {}).get("backup", {})
if config.get("enabled", False):
    apt.packages(
        name="Install workstation backup tools",
        packages=["restic", "borgbackup", "rsync"],
        present=True,
        _sudo=True,
    )
