# pylint: disable=E0401
"""
Provide shared helpers for deploying COSMIC configuration files.
"""

from io import StringIO
from pyinfra import host
from pyinfra.operations import files

def deploy_cosmic_values(component, values):
    """
    Deploy individual COSMIC configuration values.

    values:
        {
            "relative/path/to/key": "value",
        }
    """

    config = host.data.get("workstation", {}).get("cosmic", {})

    if not config.get("enabled", False):
        return

    home = host.data.get("homedir", "/root")
    user = host.data.get("username", "root")
    config_root = f"{home}/.config/cosmic"

    destinations = {
        f"{config_root}/{relative_path}": value
        for relative_path, value in values.items()
    }

    # Several settings commonly share one COSMIC component/version directory.
    # Reconcile each unique parent once before deploying the individual files.
    directories = sorted({
        destination.rsplit("/", 1)[0]
        for destination in destinations
    })
    for directory in directories:
        files.directory(
            name=f"Create COSMIC {component} config directory",
            path=directory,
            user=user,
            mode="0755",
        )

    for destination, value in destinations.items():
        relative_path = destination.removeprefix(f"{config_root}/")
        files.put(
            name=f"Configure COSMIC {component}: {relative_path}",
            src=StringIO(f"{value}\\n"),
            dest=destination,
            user=user,
            mode="0644",
        )
