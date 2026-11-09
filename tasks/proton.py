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
from pyinfra.operations import apt, server

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
    flathub_remotes = host.get_fact(
        Command,
        command="flatpak remote-list --user --columns=name",
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

    # Check installed applications.
    installed_apps = host.get_fact(
        Command,
        command="flatpak list --user --app --columns=application",
        _sudo=False
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
