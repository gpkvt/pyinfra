"""
Deploy host-specific COSMIC desktop configuration using pyinfra.

Only explicitly managed COSMIC settings are deployed. Display/output settings
are intentionally excluded because they vary between workstation setups.
"""

from pyinfra import host, local

cosmic = host.data.get("workstation", {}).get("cosmic", {})

if cosmic.get("enabled", False):
    local.include("tasks/workstation/cosmic/appearance.py")
    local.include("tasks/workstation/cosmic/window_management.py")
    local.include("tasks/workstation/cosmic/input.py")
    local.include("tasks/workstation/cosmic/shortcuts.py")
    local.include("tasks/workstation/cosmic/panel.py")
    local.include("tasks/workstation/cosmic/dock.py")
    local.include("tasks/workstation/cosmic/workspaces.py")
    local.include("tasks/workstation/cosmic/config_files.py")
