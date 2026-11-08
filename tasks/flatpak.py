"""
Install and manage Flatpak applications and updates using pyinfra.

This module ensures Flatpak is installed, installs configured
applications and checks for updates.
"""

from pyinfra.operations import flatpak, server, apt
from pyinfra import host
from pyinfra.api import FactBase

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host, check_flatpak=True)

flatpak_packages = host.data.get("flatpak_packages", [])

class FlatpakUpdates(FactBase):
    command = "flatpak remote-ls --updates --columns=application"

    def process(self, output):
        return [line for line in output if line.strip()]


class FlatpakSystemUpdates(FactBase):
    command = "flatpak remote-ls --system --updates --columns=application"

    def process(self, output):
        return [line for line in output if line.strip()]

apt.packages(
    name="Install flatpak",
    packages=["flatpak"],
)

for package in flatpak_packages:
    flatpak.packages(
        name=f"Install {package}",
        packages=[package],
        _sudo=False,
    )

server.shell(
    name="Update runtimes",
    commands=[
        """
        flock -n /tmp/flatpak-update.lock \
            flatpak update --system -y \
            || echo "Flatpak update already running. Skipping."
        """
    ],
    _sudo=True,
    _if=lambda: bool(host.get_fact(FlatpakSystemUpdates, _sudo=False)),
)

server.shell(
    name="Update packages",
    commands=[
        """
        flock -n /tmp/flatpak-update.lock \
            flatpak update -y \
            || echo "Flatpak update already running. Skipping."
        """
    ],
    _sudo=False,
    _if=lambda: bool(host.get_fact(FlatpakUpdates, _sudo=False)),
)
