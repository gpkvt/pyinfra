# pylint: disable=E0401
"""
Synchronize optional, user-supplied COSMIC configuration directories.

Each workstation.cosmic.config_files entry has a repository-relative "src"
directory and a destination "dest" relative to the configured user's home.
"""

from pathlib import PurePosixPath

from pyinfra import host
from pyinfra.operations import files

cosmic = host.data.get("workstation", {}).get("cosmic", {})

if cosmic.get("enabled", False):
    entries = cosmic.get("config_files", {})
    if not isinstance(entries, dict):
        raise ValueError("workstation.cosmic.config_files must be a mapping")

    home = host.data.get("homedir", "/root").rstrip("/")
    user = host.data.get("username", "root")
    group = host.data.get("usergroup", "root")

    for component, entry in entries.items():
        if not isinstance(entry, dict):
            raise ValueError(
                f"COSMIC config_files entry {component!r} must be a mapping"
            )

        source = entry.get("src")
        destination = entry.get("dest")
        if not source or not destination:
            raise ValueError(
                f"COSMIC config_files entry {component!r} requires src and dest"
            )

        source_path = PurePosixPath(source)
        destination_path = PurePosixPath(destination)

        if source_path.is_absolute() or ".." in source_path.parts:
            raise ValueError(
                f"COSMIC config source must be repository-relative: {source}"
            )
        if destination_path.is_absolute() or ".." in destination_path.parts:
            raise ValueError(
                f"COSMIC config destination must be home-relative: {destination}"
            )

        files.sync(
            name=f"Synchronize custom COSMIC {component} configuration",
            src=str(source_path),
            dest=f"{home}/{destination_path}",
            user=user,
            group=group,
            mode="0644",
            dir_mode="0755",
            _sudo=False,
        )
