"""
Install workstation backup tools.

This task deliberately does not create or run a backup job: repository
locations, credentials, retention and source paths must be chosen explicitly.
"""

from pyinfra import host
from pyinfra.operations import apt, files

config = host.data.get("workstation", {}).get("backup", {})
if config.get("enabled", False):
    apt.packages(
        name="Install workstation backup tools",
        packages=["restic", "borgbackup", "rsync", "borgmatic"],
        present=True,
        _sudo=True,
    )

    files.template(
        name="Create borgmatic config",
        src="templates/workstation/borgmatic.yml.j2",
        dest="/etc/borgmatic/config.yaml",
        mode="600",
        user="root",
        group="root",
        _sudo=True,
    )
