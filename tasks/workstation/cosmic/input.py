# pylint: disable=E0401
"""
Configure COSMIC mouse and touchpad input settings.

RON values are supplied explicitly so hardware-specific acceleration and
scrolling preferences are never guessed by the deployment.
"""

from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get("input", {})

if config.get("enabled", False):
    values = {}

    for option in ("default", "touchpad"):
        ron_value = config.get(option)
        if ron_value:
            values[f"com.system76.CosmicComp/v1/input_{option}"] = ron_value

    if values:
        deploy_cosmic_values("input", values)
