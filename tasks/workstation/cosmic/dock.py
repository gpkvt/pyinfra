# pylint: disable=E0401
"""
Configure COSMIC dock position, size, margins, autohide behavior, and applets.
"""

import json

from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get("dock", {})

if config.get("enabled", False):

    positions = {
        "top": "Top",
        "bottom": "Bottom",
        "left": "Left",
        "right": "Right",
    }

    sizes = {
        "small": "S",
        "normal": "M",
        "large": "L",
    }

    position = config.get("position", "bottom").lower()
    size = config.get("size", "normal").lower()

    if position not in positions:
        raise ValueError(f"Invalid dock position: {position}")

    if size not in sizes:
        raise ValueError(f"Invalid dock size: {size}")

    # Default applet placement.
    default_applets = {
        "left": ["com.system76.CosmicAppletWorkspaces"],
        "center": [
            "com.system76.CosmicPanelAppLibraryButton",
            "com.system76.CosmicPanelLauncherButton",
            "com.system76.CosmicAppList",
            "com.system76.CosmicAppletMinimize",
        ],
        "right": [],
    }

    # Allow host-specific overrides.
    applets = config.get("applets", default_applets)

    left_applets = applets.get("left", [])
    center_applets = applets.get("center", [])
    right_applets = applets.get("right", [])

    # COSMIC uses RON syntax. JSON arrays and strings are
    # compatible with the corresponding RON representations.

    plugins_wings = (
        "Some((\n"
        f"    {json.dumps(left_applets, ensure_ascii=False)},\n"
        f"    {json.dumps(right_applets, ensure_ascii=False)},\n"
        "))"
    )

    plugins_center = (
        "Some(\n"
        f"    {json.dumps(center_applets, ensure_ascii=False)}\n"
        ")"
    )

    values = {
        "com.system76.CosmicPanel.Dock/v1/anchor":
            positions[position],

        "com.system76.CosmicPanel.Dock/v1/autohide":
            "OnOverlap" if config.get("autohide") else "Never",

        "com.system76.CosmicPanel.Dock/v1/expand_to_edges":
            str(config.get("extend", False)).lower(),

        "com.system76.CosmicPanel.Dock/v1/size":
            sizes[size],

        "com.system76.CosmicPanel.Dock/v1/anchor_gap":
            str(config.get("anchor_gap", 0) > 0).lower(),

        "com.system76.CosmicPanel.Dock/v1/plugins_wings":
            plugins_wings,

        "com.system76.CosmicPanel.Dock/v1/plugins_center":
            plugins_center,
    }

    deploy_cosmic_values("dock", values)
