# pylint: disable=C0103
"""
Manage custom sudoers configuration.

Configuration:
    sudoers_rules:
        List of complete sudoers rules.

Managed file:
    /etc/sudoers.d/99-local

Requirements:
    - sudo
    - visudo
"""

import shlex

from io import StringIO

from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

# Custom fact: retrieve current sudoers configuration
class SudoersFile(FactBase):
    """
    Return the contents of the managed sudoers file.
    """

    command = "cat /etc/sudoers.d/99-local 2>/dev/null || true"

    def process(self, output):
        if not output:
            return ""

        return "\n".join(output) + "\n"

# Load configuration
sudoers_rules = host.data.get("sudoers_rules", [])

sudoers_dir = "/etc/sudoers.d"
sudoers_file = f"{sudoers_dir}/99-local"

# Validate configuration
if not isinstance(sudoers_rules, list):
    raise ValueError("sudoers_rules must be a list")

for rule in sudoers_rules:
    if not isinstance(rule, str) or not rule.strip():
        raise ValueError("Invalid sudoers rule")

    if "\n" in rule or "\r" in rule:
        raise ValueError(
            "Multiline sudoers rules are not allowed"
        )

if sudoers_rules:
    # Ensure sudoers directory exists
    files.directory(
        name="Ensure sudoers directory exists",
        path=sudoers_dir,
        user="root",
        group="root",
        mode="755",
        _sudo=True,
        _if=lambda: host.get_fact(
            Command,
            "stat -c '%U:%G:%a' /etc/sudoers.d 2>/dev/null || true",
        ) != "root:root:755",
    )

    # Build sudoers configuration
    content = (
        "# Managed by pyinfra - do not edit manually\n"
        + "\n".join(rule.strip() for rule in sudoers_rules)
        + "\n"
    )

    # Retrieve current configuration
    current_content = host.get_fact(SudoersFile)

    # Only validate and install when configuration differs
    if current_content != content:

        # Validate configuration before installation
        validation_command = (
            f"printf '%s' {shlex.quote(content)} "
            "| visudo -cf -"
        )

        server.shell(
            name="Validate custom sudoers configuration",
            commands=[validation_command],
            _sudo=True,
        )

        # Install sudoers configuration
        files.put(
            name="Manage custom sudoers configuration",
            src=StringIO(content),
            dest=sudoers_file,
            user="root",
            group="root",
            mode="440",
            _sudo=True,
        )
