"""
Shared initialization utilities for pyinfra deployments.

Decrypts the shared GPG secrets document and resolves the secrets for
the current inventory host. Shared values are recursively merged with
host-specific values, which take precedence.
"""

import builtins
import json
import shlex
import subprocess

from pyinfra.facts.files import File
from pyinfra.facts.server import Command, Which


def command_output_text(output: str | list[str] | None) -> str:
    """Normalize pyinfra Command fact output (a list of lines) to text."""
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    return "\n".join(str(line) for line in output)


def command_output(host, command: str, **kwargs) -> str:
    """Run a Command fact and normalize its output to text."""
    return command_output_text(host.get_fact(Command, command, **kwargs))


def merge_secrets(shared, host_secrets):
    """Recursively merge host secrets over shared secrets."""
    result = dict(shared)

    for key, value in host_secrets.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_secrets(result[key], value)
        else:
            # Lists and scalar values are replaced, never concatenated.
            result[key] = value

    return result


def select_host_secrets(data, hostname):
    """
    Resolve secrets for one inventory host.

    The legacy flat structure remains supported. In the multi-host
    structure, shared values are inherited by every host and values
    under hosts[hostname] override matching shared values.
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid secrets.json structure: expected a JSON object")

    # Preserve compatibility with existing flat secrets.json files.
    if "shared" not in data and "hosts" not in data:
        return data

    shared = data.get("shared", {})
    hosts = data.get("hosts", {})

    if not isinstance(shared, dict):
        raise ValueError("Invalid secrets.json structure: 'shared' must be an object")
    if not isinstance(hosts, dict):
        raise ValueError("Invalid secrets.json structure: 'hosts' must be an object")

    host_secrets = hosts.get(hostname, {})
    if not isinstance(host_secrets, dict):
        raise ValueError(f"Invalid secrets for host: {hostname}")

    return merge_secrets(shared, host_secrets)


def initialize(host, check_flatpak=False):
    """
    Initialize shared configuration and secrets for a pyinfra host.

    Decrypts secrets.json.gpg when present, resolves shared and
    host-specific secrets, and exposes the result through builtins.

    Args:
        host: The pyinfra host object.
        check_flatpak: Whether to detect the Flatpak executable.

    Raises:
        subprocess.CalledProcessError: If GPG decryption fails.
        json.JSONDecodeError: If decrypted content is invalid JSON.
        ValueError: If the secrets document has an invalid structure.
    """
    secrets_file = host.get_fact(File, path="secrets.json.gpg")

    if secrets_file:
        result = subprocess.run(
            ["gpg", "--decrypt", "secrets.json.gpg"],
            check=True,
            capture_output=True,
            text=True,
        )
        decrypted_secrets = json.loads(result.stdout)
        builtins.secrets = select_host_secrets(decrypted_secrets, host.name)
        print(f"    Loading Secrets: Decrypted successfully for {host.name}")
    else:
        builtins.secrets = {}
        print("    Loading Secrets: None, skipping...")

    builtins.homedir = host.data.get("homedir", "/root/")

    if check_flatpak:
        builtins.flatpak = host.get_fact(Which, command="flatpak")



def compose_configuration_matches(host, compose_command, services=None):
    """Return whether every configured Compose service matches its runtime hash.

    Compose stores a config hash on each created container. Comparing that
    label with the hash generated from the deployed Compose files detects
    drift even when containers are still running and pyinfra file operations
    report no changes.
    """
    expected_output = command_output(
        host, f"{compose_command} config --hash='*'"
    )
    expected = {}
    for line in expected_output.splitlines():
        fields = line.split()
        if len(fields) == 2:
            expected[fields[0]] = fields[1]

    if services is None:
        services_output = command_output(
            host, f"{compose_command} config --services"
        )
        services = services_output.splitlines()

    services = tuple(services)
    if not services or any(service not in expected for service in services):
        return False

    for service in services:
        container_ids = command_output(
            host,
            f"{compose_command} ps -a -q {shlex.quote(service)}",
        ).split()
        if not container_ids:
            return False

        actual_output = command_output(
            host,
            "docker inspect --format "
            "'{{ index .Config.Labels \"com.docker.compose.config-hash\" }}' "
            + " ".join(shlex.quote(container_id) for container_id in container_ids),
        )
        actual_hashes = actual_output.splitlines()
        if (
            len(actual_hashes) != len(container_ids)
            or any(value != expected[service] for value in actual_hashes)
        ):
            return False

    return True
