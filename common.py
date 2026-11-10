# pylint: disable=W1514, C0411
"""
Shared initialization utilities for pyinfra deployments.

Provides common configuration and secrets initialization for pyinfra
hosts. Configuration variables and decrypted secrets are made globally
accessible through the builtins module.

The initialize() function can optionally detect Flatpak when required
by individual deployment tasks.

Decrypt secrets manually (GPG):
    gpg --symmetric --cipher-algo AES256 secrets.json
    rm secrets.json

Decrypt secrets manually (Ansible Vault):
    ansible-vault encrypt secrets.json
"""

import builtins
import json
import os
import stat
import subprocess

from pathlib import Path

from pyinfra.facts.files import File
from pyinfra.facts.server import Which

from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.module_utils.common.text.converters import to_bytes


def read_vault_password(path="~/.config/pyinfra/vault_pass"):
    """
    Read the Ansible Vault password.

    Requires restrictive file permissions (600 or stricter).
    """
    password_file = Path(os.path.expanduser(path))

    mode = password_file.stat().st_mode

    if stat.S_IMODE(mode) & 0o077:
        raise PermissionError(
            f"{password_file} has unsafe permissions "
            f"{oct(stat.S_IMODE(mode))} — run: chmod 600 {password_file}"
        )

    return password_file.read_text().rstrip("\r\n")


def load_vaulted(
    vault_path="secrets.json.vault",
    vault_pass_file="~/.config/pyinfra/vault_pass",
):
    """
    Decrypt an Ansible Vault encrypted file and return its JSON content.
    """
    password = read_vault_password(vault_pass_file)

    vault = VaultLib([
        (None, VaultSecret(to_bytes(password)))
    ])

    with open(vault_path, encoding="utf-8") as file:
        decrypted = vault.decrypt(file.read())

    return json.loads(decrypted)

def initialize(host, check_flatpak=False):
    """
    Initialize shared configuration and secrets for a pyinfra host.

    Loads and decrypts secrets from either:
      - secrets.json.vault (Ansible Vault)
      - secrets.json.gpg (GPG)

    Makes configuration variables globally accessible through builtins.

    Args:
        host: The pyinfra host object used to retrieve host data and facts.
        check_flatpak (bool): Whether to check if Flatpak is installed.

    Sets:
        builtins.secrets: Decrypted secrets dictionary.
        builtins.homedir: User's home directory.
        builtins.flatpak: Flatpak executable path/fact, if requested.
    """

    # Load secrets
    if host.data.get("secrets_handler") == "ansible-vault":
        builtins.secrets = load_vaulted("secrets.json.vault")

        print(
            "    Loading Secrets: "
            "Ansible Vault decrypted successfully"
        )

    else:
        secrets_file = host.get_fact(
            File,
            path="secrets.json.gpg",
        )

        if secrets_file:
            result = subprocess.run(
                ["gpg", "--decrypt", "secrets.json.gpg"],
                check=True,
                capture_output=True,
                text=True,
            )

            builtins.secrets = json.loads(result.stdout)

            print(
                "    Loading Secrets: "
                "GPG decrypted successfully"
            )

        else:
            builtins.secrets = {}

            print(
                "    Loading Secrets: "
                "None, skipping..."
            )

    # Configuration
    builtins.homedir = host.data.get(
        "homedir",
        "/root/",
    )

    # Optional facts
    if check_flatpak:
        builtins.flatpak = host.get_fact(
            Which,
            command="flatpak",
        )
