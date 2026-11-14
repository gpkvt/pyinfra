"""
Install Proton applications.

Installation priority:
1. Official APT repository
2. Flathub
3. Official Proton DEB downloads (fallback)

APT repository configuration is managed by tasks/apt.py.
"""

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server
import shlex
from common import command_output_text

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

    # Facts are evaluated inside _if callbacks, after the preceding APT
    # operation has installed Flatpak on a first deployment.
    def installed_flatpak_apps():
        return command_output_text(host.get_fact(
            Command,
            command="flatpak list --user --app --columns=application",
            _sudo=False,
        )).splitlines()

    server.shell(
        name="Configure Flathub",
        commands=[
            "flatpak remote-add --user --if-not-exists flathub "
            "https://flathub.org/repo/flathub.flatpakrepo",
        ],
        _if=lambda: "flathub" not in command_output_text(host.get_fact(
            Command,
            command="flatpak remote-list --user --columns=name",
            _sudo=False,
        )).splitlines(),
        _sudo=False,
    )

    for app in flatpak_apps:
        server.shell(
            name=f"Install Proton Flatpak application {app}",
            commands=[
                "flatpak install --user --noninteractive --assumeyes "
                f"flathub {app}",
            ],
            _if=lambda app=app: app not in installed_flatpak_apps(),
            _sudo=False,
        )

# Proton Drive CLI
install_drive_cli = proton.get("drive_cli", True)

if install_drive_cli:
    drive_cli_version = proton.get(
        "drive_cli_version",
        proton.get("drive_cll_version", "0.9.0"),
    )
    drive_cli_platform = "linux-x64"
    version_marker = "/usr/local/share/pyinfra/proton-drive-version"

    if not isinstance(drive_cli_version, str) or not drive_cli_version:
        raise ValueError("proton.drive_cli_version must be a non-empty string")

    drive_cli_url = (
        f"https://proton.me/download/drive/cli/"
        f"{drive_cli_version}/{drive_cli_platform}/proton-drive"
    )

    apt.packages(
        name="Install Proton Drive CLI dependencies",
        packages=["curl", "libsecret-1-0"],
    )
    files.directory(
        name="Create Proton Drive version marker directory",
        path="/usr/local/share/pyinfra",
        user="root",
        group="root",
        mode="755",
        _sudo=True,
    )

    # The marker tracks the selected release, not just binary existence.
    installed_drive_cli_version = command_output_text(host.get_fact(
        Command,
        command=(
            "test -x /usr/local/bin/proton-drive "
            f"&& cat {version_marker} 2>/dev/null || true"
        ),
    )).strip()

    if installed_drive_cli_version != drive_cli_version:
        server.shell(
            name="Install or update Proton Drive CLI",
            commands=[
                f"curl -fsSL {shlex.quote(drive_cli_url)} -o /tmp/proton-drive",
                "install -m 0755 /tmp/proton-drive /usr/local/bin/proton-drive",
                "rm -f /tmp/proton-drive",
                f"printf '%s\\n' {shlex.quote(drive_cli_version)} > {version_marker}",
            ],
            _sudo=True,
        )
