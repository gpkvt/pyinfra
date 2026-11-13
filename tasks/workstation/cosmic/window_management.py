# pylint: disable=E0401
"""
Configure COSMIC window-management behavior.

This module deliberately excludes output/display configuration.
"""

from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get(
    "window_management", {}
)

if config.get("enabled", False):
    values = {}

    boolean_options = (
        "autotile",
        "focus_follows_cursor",
        "cursor_follows_focus",
    )

    for option in boolean_options:
        if option in config:
            setting = config[option]
            if not isinstance(setting, bool):
                raise ValueError(f"COSMIC {option} must be a boolean")
            values[f"com.system76.CosmicComp/v1/{option}"] = str(
                setting
            ).lower()

    if "autotile_behavior" in config:
        behavior = config["autotile_behavior"]
        if behavior not in ("PerWorkspace", "Global"):
            raise ValueError(
                f"Invalid COSMIC autotile behavior: {behavior}"
            )
        values["com.system76.CosmicComp/v1/autotile_behavior"] = behavior

    if "edge_snap_threshold" in config:
        threshold = config["edge_snap_threshold"]
        if not isinstance(threshold, int) or threshold < 0:
            raise ValueError(
                "COSMIC edge_snap_threshold must be a non-negative integer"
            )
        values["com.system76.CosmicComp/v1/edge_snap_threshold"] = str(
            threshold
        )

    if values:
        deploy_cosmic_values("window management", values)
