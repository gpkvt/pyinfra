# pylint: disable=C0301, E0401
"""
Install WireGuard and deploy VPN interface configurations using pyinfra.

This module installs the WireGuard package and generates configuration files for each VPN interface defined in the host configuration. Private keys are retrieved from the decrypted secrets dictionary and passed securely to the Jinja2 configuration template.

Configuration: vpn (dict): VPN-related settings retrieved from host.data.vpn. Defaults to an empty dictionary.

wireguard_config (dict): WireGuard interface configurations retrieved
    from `host.data.wireguard_config`. Each key represents an interface
    name and each value contains its corresponding configuration.

wireguard_secrets (dict): Decrypted WireGuard secrets retrieved from
    `secrets.wireguard`. Contains private keys indexed by interface name.

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
- Each interface is configured independently.
- This module deploys WireGuard configurations but does not
  start or enable the corresponding VPN services.
"""

from pyinfra.operations import apt, files
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

vpns = host.data.get("vpn", {})

wireguard_secrets = secrets.get("wireguard", {}) # pylint: disable=undefined-variable
wireguard_config = host.data.get("wireguard_config", {})

apt.packages(
    name="Install wireguard",
    packages=[ "wireguard" ],
)

for key, vpn in wireguard_config.items():
    files.template(
        name=f"Configure wireguard for {key}",
        src="templates/wireguard.conf.j2",
        dest=f"/etc/wireguard/{key}.conf",
        user="root",
        group="root",
        mode="640",
        _sudo=True,
        config=vpn,
        secrets=secrets.get("wireguard").get(key) # pylint: disable=undefined-variable
    )
