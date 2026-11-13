"""Isolated local inventory for deployment integration checks."""

import getpass
import grp
import os

username = getpass.getuser()
usergroup = grp.getgrgid(os.getgid()).gr_name
homedir = os.path.expanduser("~")

ci = [("@local", {
    "_sudo": True,
    "username": username,
    "usergroup": usergroup,
    "homedir": homedir,

    # Exercise tmux end-to-end, including installing its plugin manager.
    "tmux": True,

    # Disable unrelated personal workstation features.
    "apt_packages": [],
    "apt_sources": {},
    "hostname": None,
    "timezone": None,
    "locale": "",
    "editor": None,
    "visual_editor": None,
    "keyboard": {},
    "hostnames": {},
    "sudoers_rules": [],
    "ssh_config": {},
    "ssh_keys": [],
    "ssh_authorized_keys": {},
    "sysctl": {},
    "udev": {},
    "usbguard": {},
    "flatpak": False,
    "wireguard_config": {},
    "local_network_cidr": None,
    "wireguard_interface": None,
    "syncthing": False,
    "zsh": False,
    "powerline": False,
    "powerline_fonts": False,
    "ufw": False,
    # GitHub-hosted Ubuntu runners already provide Docker Engine and Compose.
    # Reuse the runner installation instead of attempting to install docker-ce.
    "docker_install": False,
    "docker": {
        "ci-smoke": {
            "image": "alpine:3.21",
            "app_services": ["smoke"],
        },
    },
    "docker_sablier": {"enabled": False},
    "caddy_config": {},
    "apparmor_profiles": {},
    "cosmic": {},
    "mullvad_extensions": [],
    "vscodium": {},
    "proton": {},
    "cron_jobs": [],
    "workstation": {
        "backup": {"enabled": False},
        "power": {"enabled": False},
        "hardware": {"enabled": False},
        "storage": {"enabled": False},
        "peripherals": {"enabled": False},
        "desktop": {"enabled": False},
        "maintenance": {"enabled": False},
    },
})]
