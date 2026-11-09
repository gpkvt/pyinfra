# pylint: disable=C0116
"""
Manage VSCodium extensions.

Configuration:
    vscodium:
        extensions: List of extension IDs to install.

Features:
    - Detect installed extensions for the configured user.
    - Schedule installation only for missing extensions.
    - Skip already installed extensions entirely.
    - Preserve manually installed extensions.
"""

import re
import shlex

from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.operations import server

class VSCodiumExtensions(FactBase):
    """
    Return installed VSCodium extension IDs.
    """

    def command(self, target_user):
        return (
            f"sudo -H -u {shlex.quote(target_user)} -- "
            "sh -lc 'codium --list-extensions'"
        )

    def process(self, output):
        installed = set()

        for line in output:
            installed_id = line.strip().lower()

            if not installed_id:
                continue

            installed_id = installed_id.split("@", 1)[0]
            installed.add(installed_id)

        return installed

# Load configuration
vscodium_config = host.data.get("vscodium", {})

if not isinstance(vscodium_config, dict):
    raise ValueError(
        "vscodium configuration must be a dictionary"
    )

if vscodium_config:
    username = host.data.get("username")

    if not username:
        raise ValueError(
            "username must be configured for VSCodium"
        )

    if not re.fullmatch(r"[a-zA-Z0-9_.-]+", username):
        raise ValueError(
            f"Invalid VSCodium username: {username}"
        )

    extension_list = vscodium_config.get("extensions", [])

    if not isinstance(extension_list, list):
        raise ValueError(
            "VSCodium extensions must be a list"
        )

    # Validate extension IDs
    for extension_id in extension_list:
        if not isinstance(extension_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+"
            r"(?:@[a-zA-Z0-9.+_-]+)?",
            extension_id,
        ):
            raise ValueError(
                f"Invalid VSCodium extension ID: {extension_id}"
            )

    # Remove duplicate entries
    extension_list = list(dict.fromkeys(extension_list))

    # Retrieve installed extensions
    installed_extensions = host.get_fact(
        VSCodiumExtensions,
        target_user=username,
    )

    # Schedule installation only for missing extensions
    for extension_id in extension_list:
        normalized_id = extension_id.split("@", 1)[0].lower()

        if normalized_id in installed_extensions:
            continue

        server.shell(
            name=f"Install VSCodium extension: {extension_id}",
            commands=[
                (
                    "codium --install-extension "
                    f"{shlex.quote(extension_id)}"
                )
            ],
            _sudo=True,
            _sudo_user=username,
        )
