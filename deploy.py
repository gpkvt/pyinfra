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
    - caddy    if     if pyinfra @local tasks/apt.py --sudo --diff -y; then
        sudo touch "$TIMESTAMP"
        echo "PyInfra completed successfully."
    else
        echo "PyInfra failed."
    fi
pyinfra @local tasks/apt.py --sudo --diff -y; then
        sudo touch "$TIMESTAMP"
        echo "PyInfra completed successfully."
    else
        echo "PyInfra failed."
    fi

    - zsh
    - tmux
    - powerline
    - ufw
    - docker

Note: Configuration values are accessed through host.data, while shared runtime configuration and secrets are exposed through builtins.
"""

from common import initialize
from pyinfra import host, local

initialize(host, check_flatpak=True)

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

if host.data.get("apparmor_profiles"):
    local.include("tasks/apparmor.py")

if host.data.get("cosmic"):
    local.include("tasks/cosmic/deploy.py")

if host.data.get("mullvad_extensions"):
    local.include("tasks/mullvad_extensions.py")

if host.data.get("vscodium"):
    local.include("tasks/vscodium.py")
