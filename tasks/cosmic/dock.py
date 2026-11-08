"""Configure COSMIC dock position, size, margins, and autohide behavior."""

from pyinfra import host
from tasks.cosmic.config import deploy_cosmic_values

config = host.data.get("cosmic", {}).get("dock", {})

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
    }

    deploy_cosmic_values("dock", values)
