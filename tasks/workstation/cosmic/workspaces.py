# pylint: disable=E0401
"""
Configure COSMIC workspace settings.
"""

from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get("workspaces", {})

if config.get("enabled", False):
    ron_config = config.get("ron")

    if ron_config:
        deploy_cosmic_values(
            "workspaces",
            {
                "com.system76.CosmicComp/v1/workspaces":
                    ron_config,
            },
        )
