"""
Deploy host-specific COSMIC desktop configuration using pyinfra.

Applies the desired COSMIC desktop settings defined in inventory data files,
such as @local.py.

Configuration is controlled through the 'cosmic.enabled' setting and
allows each host to maintain its own desktop preferences.

Only explicitly managed COSMIC settings are deployed, preserving
unmanaged user configuration.

Run this deployment using:

    pyinfra inventory.py tasks/cosmic/deploy.py
"""

from pyinfra import host, local

cosmic = host.data.get("cosmic", {})

if cosmic.get("enabled", False):
    local.include("tasks/cosmic/appearance.py")
    local.include("tasks/cosmic/panel.py")
    local.include("tasks/cosmic/dock.py")
    local.include("tasks/cosmic/workspaces.py")
