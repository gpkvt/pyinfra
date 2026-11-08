"""Configure COSMIC appearance settings such as dark and light mode."""

from pyinfra import host
from tasks.cosmic.config import deploy_cosmic_values

config = host.data.get("cosmic", {}).get("appearance", {})

if config.get("enabled", False):
    mode = config.get("mode", "dark").lower()

    if mode not in ("dark", "light"):
        raise ValueError(
            f"Invalid COSMIC appearance mode: {mode}"
        )

    deploy_cosmic_values(
        "appearance",
        {
            "com.system76.CosmicTheme.Mode/v1/is_dark":
                "true" if mode == "dark" else "false",
        },
    )
