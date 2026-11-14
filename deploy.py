# pylint: disable=line-too-long, undefined-variable

"""
Configure and execute local infrastructure provisioning tasks using pyinfra.

Task execution: Core tasks are always included:
    - apt
    - hosts
    - scripts
    - mc
    - git

Optional tasks are included depending on available software,
host configuration, and configured secrets.
"""

from common import initialize
from pyinfra import host, local

initialize(host, check_flatpak=True)
local_network_cidr = host.data.get("local_network_cidr")
wireguard_interface = host.data.get("wireguard_interface")

# Tasks
local.include("tasks/apt.py")
local.include("tasks/hosts.py")
local.include("tasks/sudo.py")
local.include("tasks/system.py")
local.include("tasks/ssh_keys.py")
local.include("tasks/git.py")
local.include("tasks/fonts.py")
local.include("tasks/scripts.py")
local.include("tasks/mc.py")

if host.data.get("cron_jobs"):
    local.include("tasks/cron.py")

if flatpak:
    local.include("tasks/flatpak.py")

if host.data.ssh_config:
    local.include("tasks/ssh_config.py")

if (
    host.data.get("wireguard_config")
    and secrets.get("wireguard")
    and host.data.get("wireguard_enabled", True)
):
    local.include("tasks/wireguard.py")

if (
    local_network_cidr
    and wireguard_interface
    and host.data.get("vpn_enabled", True)
):
    local.include("tasks/vpn.py")

syncthing_config = host.data.get("syncthing", {})
if syncthing_config and syncthing_config.get("enabled", True):
    local.include("tasks/syncthing.py")

if host.data.get("zsh"):
    local.include("tasks/zsh.py")

if host.data.get("tmux"):
    local.include("tasks/tmux.py")

if host.data.get("powerline"):
    local.include("tasks/powerline.py")

samba_config = host.data.get("samba", {})
if samba_config and samba_config.get("enabled", False):
    local.include("tasks/samba.py")

ufw_config = host.data.get("ufw", {})
if ufw_config and ufw_config.get("enabled", True):
    local.include("tasks/ufw.py")

if host.data.get("docker"):
    local.include("tasks/docker.py")
    # Sablier must be available before app containers are created for on-demand
    # startup. The battery saver is mutually exclusive with Sablier.
    if host.data.get("docker_power_monitor", True):
        local.include("tasks/docker_power.py")
    if host.data.get("docker_sablier", {}).get("enabled", False):
        local.include("tasks/docker_sablier.py")
    local.include("tasks/docker_container.py")
    if host.data.get("caddy_config") and host.data.get("caddy_enabled", True):
        local.include("tasks/caddy.py")

if host.data.get("apparmor_profiles") and host.data.get("apparmor_enabled", True):
    local.include("tasks/apparmor.py")

if host.data.get("mullvad_extensions") and host.data.get("mullvad_browser_enabled", True):
    local.include("tasks/mullvad_extensions.py")

if host.data.get("vscodium") and host.data.get("vscodium_enabled", True):
    local.include("tasks/vscodium.py")

if host.data.get("proton"):
    local.include("tasks/proton.py")

# Optional workstation features. All are disabled unless explicitly enabled
# in group_data/workstation.py.
workstation = host.data.get("workstation", {})
for feature, task in (
    ("backup", "backup.py"),
    ("power", "power.py"),
    ("hardware", "hardware.py"),
    ("storage", "storage.py"),
    ("peripherals", "peripherals.py"),
    ("desktop", "desktop.py"),
    ("maintenance", "maintenance.py"),
    ("limusic", "limusic.py"),
    ("cosmic", "cosmic/deploy.py"),
):
    if workstation.get(feature, {}).get("enabled", False):
        local.include(f"tasks/workstation/{task}")
