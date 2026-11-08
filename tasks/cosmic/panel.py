"""Configure COSMIC panel position, size, margins, and autohide behavior."""

from pyinfra import host
from tasks.cosmic.config import deploy_cosmic_values

config = host.data.get("cosmic", {}).get("panel", {})

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
    }

    deploy_cosmic_values("panel", values)
