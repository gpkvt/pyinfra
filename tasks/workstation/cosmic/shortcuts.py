# pylint: disable=E0401
"""
Configure COSMIC custom keyboard shortcuts.

The custom shortcut map is supplied as a RON value to preserve COSMIC's
native key/action syntax and avoid imposing a generic shortcut layout.
"""

from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get("shortcuts", {})

if config.get("enabled", False):
    ron_config = config.get("ron")

    if ron_config:
        deploy_cosmic_values(
            "shortcuts",
            {
                "com.system76.CosmicSettings.Shortcuts/v1/custom": ron_config,
            },
        )
