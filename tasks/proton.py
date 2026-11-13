"""
Install Proton applications.

Installation priority:
1. Official APT repository
2. Flathub
3. Official Proton DEB downloads (fallback)

APT repository configuration is managed by tasks/apt.py.
"""

import re

from common import command_output
from pyinfra import host

from pyinfra.operations import apt, flatpak, server

proton = host.data.get("proton", {})

install_mail = proton.get("mail", True)
install_bridge = proton.get("bridge", True)
install_vpn = proton.get("vpn", True)
install_pass = proton.get("pass", True)

use_flatpak = proton.get("flatpak", True)

if install_vpn:
    apt.packages(
        name="Install Proton VPN",
        packages=[
            "proton-vpn-cli",
            "proton-vpn-gnome-desktop"
        ],
    )

flatpak_apps = []

if install_mail:
    flatpak_apps.append("me.proton.Mail")

if install_bridge:
    flatpak_apps.append("ch.protonmail.protonmail-bridge")

if install_pass:
    flatpak_apps.append("me.proton.Pass")


if use_flatpak and flatpak_apps:
    apt.packages(
        name="Install Flatpak",
        packages=["flatpak"],
    )

    # Check configured Flatpak remotes.
    flathub_remotes = command_output(host, command="flatpak remote-list --user --columns=name",
        _sudo=False
    )

    server.shell(
        name="Configure Flathub",
        commands=[
            "flatpak remote-add --user flathub "
            "https://flathub.org/repo/flathub.flatpakrepo",
        ],
        _if=lambda: "flathub" not in flathub_remotes.splitlines(),
        _sudo=False
    )

    # Let pyinfra's Flatpak operation compare installed application IDs and
    # install only the missing user-scoped applications from Flathub.
    flatpak.packages(
        name="Install Proton Flatpak applications",
        packages=flatpak_apps,
        remote="flathub",
        user=True,
    )

# Proton Drive CLI
install_drive_cli = proton.get("drive_cli", True)

if install_drive_cli:
    drive_cli_version = proton.get("drive_cli_version", "0.9.0")
    if not isinstance(drive_cli_version, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", drive_cli_version):
        raise ValueError(f"Invalid Proton Drive CLI version: {drive_cli_version!r}")
    drive_cli_platform = "linux-x64"

    drive_cli_url = (
        f"https://proton.me/download/drive/cli/"
        f"{drive_cli_version}/{drive_cli_platform}/proton-drive"
    )

    apt.packages(
        name="Install Proton Drive CLI dependencies",
        packages=[
            "curl",
            "libsecret-1-0",
        ],
    )

    # Track the installed release explicitly: checking only for the binary
    # would prevent a configured version change from ever being applied.
    installed_drive_cli_version = command_output(
        host,
        "cat /usr/local/bin/proton-drive.version 2>/dev/null || true",
    ).strip()

    if installed_drive_cli_version != drive_cli_version:
        server.shell(
            name="Install Proton Drive CLI",
            commands=[
                f"curl -fsSL '{drive_cli_url}' -o /tmp/proton-drive",
                "install -m 0755 /tmp/proton-drive /usr/local/bin/proton-drive",
                f"printf '%s\\n' '{drive_cli_version}' > /usr/local/bin/proton-drive.version",
                "rm -f /tmp/proton-drive",
            ],
        )
