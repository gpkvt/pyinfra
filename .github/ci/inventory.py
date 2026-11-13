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

    # Exercise the shared deployment path and its tmux plugin manager.
    "tmux": True,

    # Baseline package and host configuration.
    "apt_packages": ["jq"],
    # A disabled fixture validates the repository skip path without adding
    # an external package source to the runner.
    "apt_sources": {
        "ci-disabled": {
            "enabled": False,
            "key": {
                "url": "https://example.invalid/ci.gpg",
                "path": "/etc/apt/keyrings/ci.gpg",
            },
            "repository": {
                "url": "https://example.invalid/apt",
                "distribution": "stable",
                "components": ["main"],
            },
        },
    },
    "hostname": "pyinfra-ci",
    "timezone": "UTC",
    "locale": "C.UTF-8",
    "editor": "vi",
    "visual_editor": "vi",
    "keyboard": {
        "layout": "us",
        "model": "pc105",
        "variant": "",
        "options": "",
    },
    "hostnames": {
        "127.0.0.1": ["localhost", "pyinfra-ci.local"],
    },
    "sudoers_rules": [
        f"{username} ALL=(root) NOPASSWD: /usr/bin/true",
    ],
    "ssh_config": {
        "Host ci-test.invalid": (
            "    HostName ci-test.invalid\n"
            "    User ci\n"
            "    BatchMode yes"
        ),
    },
    "ssh_keys": [
        {
            "name": "pyinfra_ci",
            "type": "ed25519",
            "comment": "pyinfra-ci",
        },
    ],
    # The task replaces the complete authorized_keys file. Keep the fixture
    # populated but do not alter the runner account's existing login keys.
    "ssh_authorized_keys": {
        username: [
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINLXd8InkqcQRvTK+HEKTMEkEWEYHyIcVpX+PcNzFwz2 pyinfra-ci-fixture",
        ],
    },
    "ssh_authorized_keys_enabled": False,
    "sysctl": {
        "vm.swappiness": 60,
    },
    "udev": {
        "99-pyinfra-ci.rules": (
            'ACTION=="add", SUBSYSTEM=="tty", '
            'ENV{ID_VENDOR_ID}=="ffff", TAG+="uaccess"'
        ),
    },
    "usbguard": {
        "enabled": False,
        "implicit_policy": "block",
        "present_device_policy": "keep",
        "rules": ["allow id 0000:0000"],
    },

    # These optional features have explicit configuration but are gated off
    # where they would affect networking, services, or desktop applications.
    "flatpak": False,
    "wireguard_config": {
        "ci-test": {
            "interface": {
                "Address": "192.0.2.2/32",
            },
        },
    },
    "wireguard_enabled": False,
    "local_network_cidr": "192.0.2.0/24",
    "wireguard_interface": "ci-test",
    "vpn_enabled": False,
    "syncthing": {
        "enabled": False,
        "gui_address": "127.0.0.1:8384",
    },
    "zsh": False,
    "powerline": True,
    "powerline_fonts": False,
    "ufw": {
        "enabled": False,
        "ssh": "Allow",
    },

    # GitHub-hosted Ubuntu runners already provide Docker Engine and Compose.
    "docker_install": False,
    "docker": {
        "ci-smoke": {
            "image": "alpine:3.21",
            "app_services": ["smoke"],
        },
    },
    "docker_sablier": {
        "enabled": False,
        "default_duration": "15m",
        "blocking_timeout": "2m",
    },
    "docker_power_monitor": False,

    "caddy_enabled": False,
    "caddy_config": {
        "ci.invalid": {
            "respond": "CI fixture",
        },
    },
    "apparmor_enabled": False,
    "apparmor_profiles": [
        {
            "path": "/etc/apparmor.d/ci-test",
            "names": ["pyinfra-ci-test"],
        },
    ],
    "cosmic": {
        "enabled": False,
    },
    "mullvad_browser_enabled": False,
    "mullvad_extensions": {
        "ci-test": {
            "id": "pyinfra-ci-test@example.invalid",
            "url": "https://example.invalid/ci-test.xpi",
        },
    },
    "vscodium_enabled": False,
    "vscodium": {
        "extensions": ["example.ci-test"],
    },
    "proton": {
        "mail": False,
        "bridge": False,
        "vpn": False,
        "pass": False,
        "flatpak": False,
        "drive_cli": False,
    },
    "cron_jobs": [
        {
            "name": "pyinfra-ci-test",
            "command": "/usr/bin/true",
            "scope": "user",
            "minute": "0",
            "hour": "0",
        },
    ],

    # These four tasks only install inspection/integration packages.
    "workstation": {
        "backup": {"enabled": False},
        "power": {"enabled": False},
        "hardware": {"enabled": True},
        "storage": {"enabled": True},
        "peripherals": {"enabled": False},
        "desktop": {
            "enabled": True,
            "packages": ["xdg-utils", "xdg-user-dirs"],
        },
        "maintenance": {"enabled": True},
    },
})]
