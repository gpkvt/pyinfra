"""
Install Proton applications.

Installation priority:
1. Official APT repository
2. Flathub
3. Official Proton DEB downloads (fallback)

APT repository configuration is managed by tasks/apt.py.
"""

import re

from pyinfra import host
from pyinfra.operations import apt, files, server

from common import command_output

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
    flathub_remotes = command_output(
        host, "flatpak remote-list --user --columns=name", _sudo=False
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

    # Check installed applications.
    installed_apps = command_output(
        host, "flatpak list --user --app --columns=application", _sudo=False
    )

    missing_apps = [
        app
        for app in flatpak_apps
        if app not in installed_apps.splitlines()
    ]

    if missing_apps:
        server.shell(
            name="Install Proton Flatpak applications",
            commands=[
                "flatpak install --user "
                "--noninteractive --assumeyes "
                "flathub "
                + " ".join(missing_apps),
            ],
            _sudo=False
        )

# Proton Drive CLI
install_drive_cli = proton.get("drive_cli", True)

if install_drive_cli:
    drive_cli_version = proton.get("drive_cli_version", "0.9.0")
    if not isinstance(drive_cli_version, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9._+-]*",
        drive_cli_version,
    ):
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

    version_file = "/usr/local/share/proton-drive/version"
    installed_drive_cli_version = command_output(
        host,
        "if [ -x /usr/local/bin/proton-drive ] && "
        f"[ -f {version_file} ]; then cat {version_file}; else printf missing; fi",
    ).strip()

    # Track the version installed by this task. A missing binary or a changed
    # requested version triggers one download; matching versions are untouched.
    files.directory(
        name="Create Proton Drive CLI version directory",
        path="/usr/local/share/proton-drive",
        user="root",
        group="root",
        mode="755",
        _sudo=True,
    )
    server.shell(
        name="Install Proton Drive CLI",
        commands=[
            "set -eu; "
            f"curl -fsSL '{drive_cli_url}' -o /tmp/proton-drive; "
            "install -m 0755 /tmp/proton-drive /usr/local/bin/proton-drive; "
            f"printf '%s\\n' '{drive_cli_version}' > {version_file}; "
            "rm -f /tmp/proton-drive"
        ],
        _sudo=True,
        _if=lambda: installed_drive_cli_version != drive_cli_version,
    )
