"""
Install and manage Flatpak applications and updates using pyinfra.

This module ensures Flatpak is installed, installs configured Flatpak applications, and checks for available application and runtime updates. Updates are applied conditionally to avoid unnecessary operations and prevent concurrent update processes.

Configuration: flatpak_packages (list[str]): Flatpak application IDs to install, retrieved from host.data.flatpak_packages. Defaults to an empty list.

Facts:

FlatpakUpdates: Checks for available user-level Flatpak application updates using flatpak remote-ls --updates.

    Returns:
        list[str]: Application IDs with available updates.

FlatpakSystemUpdates:
    Checks for available system-level Flatpak updates using
    `flatpak remote-ls --system --updates`.

    Returns:
        list[str]: Application IDs with available system updates.

Operations:

1. Install the Flatpak package through APT.
2. Install all applications specified in `flatpak_packages`
   without sudo.
3. Check for available system-level updates and update runtimes
   when necessary.
4. Check for available user-level updates and update applications
   when necessary.

Update management:

- System updates run with sudo.
- User-level updates run without sudo.
- Updates are executed only when the corresponding fact detects
  available updates.
- Both update operations use `flock` with the shared lock file
  `/tmp/flatpak-update.lock` to prevent concurrent execution.
- If another update process holds the lock, the operation is
  skipped.

Notes:

- Flatpak applications are installed individually.
- Update checks are performed separately for system and user
  installations.
- The update commands automatically confirm prompts using `-y`.

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
    flatpak.packages (
        name=f"Install {package}",
        packages=[
            package
        ],
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

server.shell(
    name="Remove unused",
    commands=[
        "flatpak uninstall --unused --noninteractive"
    ],
)
