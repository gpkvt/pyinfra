# pylint: disable=C0301, E0401
"""
Install WireGuard and deploy VPN interface configurations using pyinfra.

This module installs the WireGuard package and generates configuration files for each VPN interface defined in the host configuration. Private keys are retrieved from the decrypted secrets dictionary and passed securely to the Jinja2 configuration template.

Configuration:

wireguard_config (dict): Mapping of Linux interface names (1-15 characters)
    to interface settings. Each entry must contain an `interface` mapping.

wireguard_secrets (dict): Decrypted values from `secrets.wireguard`, keyed
    by interface name. Each entry requires a non-empty `privatekey` and a
    `peers` list containing peer configuration mappings.

Operations:

1. Install the WireGuard package using APT.
2. Iterate over all configured WireGuard interfaces.
3. Render a configuration file for each interface using
   `templates/wireguard.conf.j2`.
4. Deploy each generated configuration to
   `/etc/wireguard/<interface>.conf`.
5. Pass the interface configuration and corresponding private key
   to the Jinja2 template.

File permissions:

- Configuration files: root:root, mode 0640.

Notes:

- Package installation uses the system package manager.
- Configuration deployment requires sudo.
- Private keys are retrieved from decrypted secrets rather than
  being stored directly in host configuration.
- Interface names are validated before being used in destination paths.
- Each interface is configured independently and must have matching secrets.
- This module deploys WireGuard configurations but does not
  start or enable the corresponding VPN services.
"""

import re

from pyinfra.operations import apt, files
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

wireguard_secrets = secrets.get("wireguard", {})  # pylint: disable=undefined-variable
wireguard_config = host.data.get("wireguard_config", {})

if not isinstance(wireguard_config, dict):
    raise ValueError("wireguard_config must be a mapping")
if not isinstance(wireguard_secrets, dict):
    raise ValueError("secrets.wireguard must be a mapping")

validated_interfaces = []
for interface, config in wireguard_config.items():
    if (
        not isinstance(interface, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", interface)
        or interface in {".", ".."}
    ):
        raise ValueError(
            f"Invalid WireGuard interface name: {interface!r}; "
            "names must be 1-15 characters and contain only letters, digits, '.', '_' or '-'"
        )
    if not isinstance(config, dict) or not isinstance(config.get("interface"), dict):
        raise ValueError(
            f"WireGuard interface {interface!r} requires an 'interface' mapping"
        )

    interface_secrets = wireguard_secrets.get(interface)
    if not isinstance(interface_secrets, dict):
        raise ValueError(
            f"Missing WireGuard secrets for interface {interface!r}"
        )
    if not isinstance(interface_secrets.get("privatekey"), str) or not interface_secrets["privatekey"]:
        raise ValueError(
            f"WireGuard interface {interface!r} requires a privatekey secret"
        )
    peers = interface_secrets.get("peers")
    if not isinstance(peers, list) or any(not isinstance(peer, dict) for peer in peers):
        raise ValueError(
            f"WireGuard interface {interface!r} requires peers to be a list of mappings"
        )

    validated_interfaces.append((interface, config, interface_secrets))

apt.packages(
    name="Install wireguard",
    packages=[ "wireguard" ],
)

for key, vpn, interface_secrets in validated_interfaces:
    files.template(
        name=f"Configure wireguard for {key}",
        src="templates/wireguard.conf.j2",
        dest=f"/etc/wireguard/{key}.conf",
        user="root",
        group="root",
        mode="640",
        _sudo=True,
        config=vpn,
        secrets=interface_secrets
    )
