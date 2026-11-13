# pylint: disable=E0401
"""
Configure COSMIC panel position, size, margins, autohide behavior, and applets.
"""

import json
from pyinfra import host
from tasks.workstation.cosmic.config import deploy_cosmic_values

config = host.data.get("workstation", {}).get("cosmic", {}).get("panel", {})

if config.get("enabled", False):

    positions = {
        "top": "Top",
        "bottom": "Bottom",
        "left": "Left",
        "right": "Right",
    }

    sizes = {
        "xs": "XS",
        "s": "S",
        "m": "M",
        "l": "L",
        "xl": "XL",
        "extra_small": "XS",
        "small": "S",
        "normal": "M",
        "large": "L",
        "extra_large": "XL",
    }

    position = config.get("position", "top").lower()
    size = config.get("size", "normal").lower()

    if position not in positions:
        raise ValueError(f"Invalid panel position: {position}")

    if size not in sizes:
        raise ValueError(f"Invalid panel size: {size}")

    # Default applet configuration.
    default_applets = {
        "left": [
            "com.system76.CosmicAppletQuickSettings",
        ],
        "center": [],
        "right": [
            "com.system76.CosmicAppletNotifications",
            "com.system76.CosmicAppletTime",
            "com.system76.CosmicAppletTempest",
            "com.system76.CosmicAppletUserSession",
        ],
    }

    # Allow applet configuration to be overridden through host data.
    applets = config.get("applets", {})

    left_applets = applets.get("left", [])
    center_applets = applets.get("center", [])
    right_applets = applets.get("right", [])

    # JSON string/list syntax is compatible with the corresponding
    # RON string/list syntax used by COSMIC.

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
        "com.system76.CosmicPanel.Panel/v1/anchor":
            positions[position],

        "com.system76.CosmicPanel.Panel/v1/autohide":
            "OnOverlap" if config.get("autohide") else "Never",

        "com.system76.CosmicPanel.Panel/v1/expand_to_edges":
            str(config.get("extend", True)).lower(),

        "com.system76.CosmicPanel.Panel/v1/size":
            sizes[size],

        "com.system76.CosmicPanel.Panel/v1/anchor_gap":
            str(config.get("anchor_gap", 0) > 0).lower(),

        "com.system76.CosmicPanel.Panel/v1/plugins_wings":
            plugins_wings,

        "com.system76.CosmicPanel.Panel/v1/plugins_center":
            plugins_center,
    }

    deploy_cosmic_values("panel", values)
