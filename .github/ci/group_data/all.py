"""Minimal, isolated data for the deployment idempotency CI job."""

import getpass
import grp
import os

username = getpass.getuser()
usergroup = grp.getgrgid(os.getgid()).gr_name
homedir = os.path.expanduser("~")

# Keep the standard deploy entry point focused on its baseline tasks.
apt_packages = []
apt_sources = {}
hostnames = {}
sudoers_rules = []
ssh_config = {}
ssh_keys = []
ssh_authorized_keys = []

# Do not apply workstation-specific system settings on the CI runner.
hostname = None
timezone = None
locale = ""
editor = None
visual_editor = None
keyboard = {}
sysctl = {}
udev = {}
usbguard = {}

# Optional host features are intentionally disabled for CI.
flatpak = False
wireguard_config = {}
local_network_cidr = None
wireguard_interface = None
syncthing = False
zsh = False
# tmux is enabled explicitly by .github/ci/inventory.py.
powerline = False
powerline_fonts = False
ufw = False
docker = {}
docker_sablier = {"enabled": False}
caddy_config = {}
apparmor_profiles = {}
cosmic = {}
mullvad_extensions = []
vscodium = {}
proton = {}

workstation = {
    "backup": {"enabled": False},
    "power": {"enabled": False},
    "hardware": {"enabled": False},
    "storage": {"enabled": False},
    "peripherals": {"enabled": False},
    "desktop": {"enabled": False},
    "maintenance": {"enabled": False},
}
