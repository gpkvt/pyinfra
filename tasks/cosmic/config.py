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

    config = host.data.get("cosmic", {})

    if not config.get("enabled", False):
        return

    home = host.data.get("homedir", "/root")
    user = host.data.get("username", "root")
    config_root = f"{home}/.config/cosmic"

    for relative_path, value in values.items():
        destination = f"{config_root}/{relative_path}"

        files.directory(
            name=f"Create COSMIC {component} config directory",
            path="/".join(destination.split("/")[:-1]),
            user=user,
            mode="0755",
        )

        files.put(
            name=f"Configure COSMIC {component}: {relative_path}",
            src=StringIO(f"{value}\n"),
            dest=destination,
            user=user,
            mode="0644",
        )
