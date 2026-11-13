# pylint: disable=E0401, C0115, C0116
"""
Install and manage Flatpak applications and updates using pyinfra.

This module ensures Flatpak is installed, installs configured
applications and checks for updates.
"""

import shlex

from pyinfra.operations import flatpak, server, apt
from pyinfra import host, logger
from pyinfra.api import FactBase, operation
from pyinfra.facts.server import Command

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host, check_flatpak=True)

flatpak_packages = host.data.get("flatpak_packages", [])


class FlatpakRemotes(FactBase):
    """Return configured user Flatpak remotes."""
    command = "flatpak remotes --user --columns=name"

    def process(self, output):
        return [line.strip() for line in output if line.strip()]


class FlatpakUpdates(FactBase):
    command = "flatpak remote-ls --user --updates --columns=application"

    def process(self, output):
        return [line for line in output if line.strip()]


def _command_lines(output):
    """Convert pyinfra Command fact output into normalized non-empty lines."""
    if output is None:
        return []
    if isinstance(output, str):
        return [line.strip() for line in output.splitlines() if line.strip()]
    return [str(line).strip() for line in output if str(line).strip()]


def select_flatpak_remote(package_id, remote_applications):
    """Prefer Flathub, otherwise require exactly one matching remote."""
    matches = sorted(
        remote for remote, applications in remote_applications.items()
        if package_id in applications
    )
    if "flathub" in matches:
        return "flathub"
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(
            f"Flatpak application {package_id!r} is unavailable from configured remotes"
        )
    raise ValueError(
        f"Flatpak application {package_id!r} is available from multiple non-Flathub "
        f"remotes: {', '.join(matches)}"
    )


# Ensure Flatpak is installed.
apt.packages(
    name="Install flatpak",
    packages=["flatpak"],
)

# Resolve each application to one explicit remote. This prevents Flatpak from
# prompting when duplicate refs exist and makes Flathub the consistent default.
if flatpak_packages:
    remotes = host.get_fact(FlatpakRemotes, _sudo=False)
    installed = set(_command_lines(host.get_fact(
        Command,
        command="flatpak list --user --app --columns=application",
        _sudo=False,
    )))
    available_by_remote = {}
    for remote in remotes:
        available_by_remote[remote] = set(_command_lines(host.get_fact(
            Command,
            command=(
                "flatpak remote-ls --user --app --columns=application "
                f"{shlex.quote(remote)}"
            ),
            _sudo=False,
        )))

    packages_by_remote = {}
    for package in dict.fromkeys(flatpak_packages):
        if package in installed:
            continue
        remote = select_flatpak_remote(package, available_by_remote)
        packages_by_remote.setdefault(remote, []).append(package)

    for remote, packages in sorted(packages_by_remote.items()):
        flatpak.packages(
            name=f"Install Flatpak applications from {remote}",
            packages=packages,
            remote=remote,
            user=True,
            _sudo=False,
        )


# Update user Flatpak applications and runtimes only.
server.shell(
    name="Update user Flatpak packages",
    commands=[
        """
        flock -n /tmp/flatpak-update.lock \\
            flatpak update --user -y \\
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
        before=$(flatpak list --user --all --columns=application,arch,branch,installation | sort)
        flatpak uninstall --user --unused --noninteractive --assumeyes
        after=$(flatpak list --user --all --columns=application,arch,branch,installation | sort)
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


# Remove unused user packages and runtimes only.
uninstall_unused_packages(
    name="Remove unused user Flatpak packages and runtimes",
    _sudo=False,
)
