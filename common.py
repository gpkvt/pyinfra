"""
Shared initialization utilities for pyinfra deployments.

Provides common configuration and secrets initialization for pyinfra
hosts. Configuration variables and decrypted secrets are made globally
accessible through the builtins module.

The initialize() function can optionally detect Flatpak when required
by individual deployment tasks.

# Decrypt secrets
# encrypt manually:
gpg --symmetric --cipher-algo AES256 secrets.json && rm secrets.json
# decrpyt manually:
gpg --decrypt secrets.json.gpg > secrets.json
"""

import builtins
import json
import subprocess

from pyinfra.facts.files import File
from pyinfra.facts.server import Which

def initialize(host, check_flatpak=False):
    """
    Initialize shared configuration and secrets for a pyinfra host.

    Loads and decrypts secrets from secrets.json.gpg (if available),
    and makes configuration variables globally accessible through
    the builtins module.

    Optionally checks whether Flatpak is installed and stores the
    result in builtins.flatpak.

    Args:
        host: The pyinfra host object used to retrieve host data and facts.
        check_flatpak (bool, optional): Whether to check if Flatpak is
            installed. Defaults to False.

    Sets:
        builtins.secrets: Decrypted secrets dictionary, or an empty
            dictionary if no secrets file exists.
        builtins.homedir: User's home directory.
        builtins.flatpak: Flatpak executable path/fact, only when
            check_flatpak is True.

    Raises:
        subprocess.CalledProcessError: If GPG decryption fails.
        json.JSONDecodeError: If the decrypted secrets are invalid JSON.
    """

    # Load secrets
    secrets_file = host.get_fact(File, path="secrets.json.gpg")

    if secrets_file:
        result = subprocess.run(
            ["gpg", "--decrypt", "secrets.json.gpg"],
            check=True,
            capture_output=True,
            text=True,
        )
        builtins.secrets = json.loads(result.stdout)
        print("    Loading Secrets: Decrypted successfully")
    else:
        builtins.secrets = {}
        print("    Loading Secrets: None, skipping...")

    # Configuration
    builtins.homedir = host.data.get("homedir", "/root/")

    # Optional facts
    if check_flatpak:
        builtins.flatpak = host.get_fact(Which, command="flatpak")
