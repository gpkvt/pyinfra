# pylint: disable=line-too-long, undefined-variable, W0621, C0413
"""
Configure and execute local infrastructure provisioning tasks using pyinfra.

Task execution: Core tasks are always included:
    - apt
    - hosts
    - scripts
    - mc
    - git

Optional tasks are included depending on available software,
host configuration, and configured secrets:
    - flatpak
    - ssh_config
    - wireguard
    - vpn
    - dehydrated
    - caddy
    - zsh
    - tmux
    - powerline
    - ufw
    - docker

Note: Configuration values are accessed through host.data, while shared runtime configuration and secrets are exposed through builtins.
"""

import _socket

"""
Compatibility workaround for pyinfra's custom integer types
when used with gevent's DNS resolver.
"""

_original_getaddrinfo = _socket.getaddrinfo

def _compatible_getaddrinfo(host, port, *args, **kwargs):
    # gevent's resolver expects a native Python int or str.
    # pyinfra may supply its own integer subclass (_CustomInt).
    if port is not None and type(port) not in (int, str):
        port = int(port)

    return _original_getaddrinfo(host, port, *args, **kwargs)

_socket.getaddrinfo = _compatible_getaddrinfo

from pyinfra import host, local
from common import initialize

initialize(host, check_flatpak=True)
local_network_cidr=host.data.get("local_network_cidr")
wireguard_interface=host.data.get("wireguard_interface")

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

if flatpak:
    local.include("tasks/flatpak.py")

if host.data.ssh_config:
    local.include("tasks/ssh_config.py")

if host.data.get("wireguard_config") and secrets.get("wireguard"):
    local.include("tasks/wireguard.py")

if local_network_cidr and wireguard_interface:
    local.include("tasks/vpn.py")

if secrets.get("dehydrated"):
    local.include("tasks/dehydrated.py")

if host.data.get("caddy_config"):
    local.include("tasks/caddy.py")

if host.data.get("zsh"):
    local.include("tasks/zsh.py")

if host.data.get("tmux"):
    local.include("tasks/tmux.py")

if host.data.get("powerline"):
    local.include("tasks/powerline.py")

if host.data.get("ufw"):
    local.include("tasks/ufw.py")

if host.data.get("docker"):
    local.include("tasks/docker.py")
    local.include("tasks/docker_container.py")

if host.data.get("apparmor_profiles"):
    local.include("tasks/apparmor.py")

if host.data.get("cosmic"):
    local.include("tasks/cosmic/deploy.py")

if host.data.get("mullvad_extensions"):
    local.include("tasks/mullvad_extensions.py")

if host.data.get("vscodium"):
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
):
    if workstation.get(feature, {}).get("enabled", False):
        local.include(f"tasks/workstation/{task}")
