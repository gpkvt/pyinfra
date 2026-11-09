# pylint: disable=E0401, C0115, C0116
"""
Install and manage Flatpak applications and updates using pyinfra.

This module ensures Flatpak is installed, installs configured
applications and checks for updates.
"""

from pyinfra.operations import flatpak, server, apt
from pyinfra import host, logger
from pyinfra.api import FactBase, operation

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


# Ensure Flatpak is installed.
apt.packages(
    name="Install flatpak",
    packages=["flatpak"],
)

# Install all configured Flatpak applications in a single operation.
if flatpak_packages:
    flatpak.packages(
        name="Install Flatpak applications",
        packages=flatpak_packages,
        _sudo=False,
    )


# Update system-wide Flatpak runtimes.
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


# Update user Flatpak applications.
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


def _output_as_text(result) -> str:
    """Normalize whatever run_shell_command returns into plain text."""
    logger.debug("raw run_shell_command result: %r", result)

    if isinstance(result, str):
        return result

    if isinstance(result, (tuple, list)):
        return "\n".join(
            part for part in (_output_as_text(item) for item in result) if part
        )

    for attr in ("stdout", "stderr", "combined", "output", "text"):
        val = getattr(result, attr, None)
        if val is None:
            continue
        if isinstance(val, str):
            return val
        if isinstance(val, (list, tuple)):
            return "\n".join(str(line) for line in val)

    return repr(result)


@operation()
def uninstall_unused_packages():
    result = host.run_shell_command(
        """
        before=$(flatpak list --all --columns=application,arch,branch,installation | sort)
        flatpak uninstall --unused --noninteractive --assumeyes
        after=$(flatpak list --all --columns=application,arch,branch,installation | sort)
        if [ "$before" = "$after" ]; then
            echo UNCHANGED
        else
            echo REMOVED
        fi
        """
    )
    output = _output_as_text(result)

    removed = "REMOVED" in output
    nothing = "UNCHANGED" in output

    if not removed and not nothing:
        logger.warning("Unexpected flatpak output:\n%s", output)

    if not removed:
        return  # zero commands -> pyinfra reports "No Change"

    logger.info("Unused flatpak refs removed")
    yield "true"  # change already happened via run_shell_command; record it


# Remove unused user packages.
uninstall_unused_packages(
    name="Remove unused packages",
    _sudo=False,
)

# Remove unused system runtimes.
uninstall_unused_packages(
    name="Remove unused runtimes",
    _sudo=True,
)
