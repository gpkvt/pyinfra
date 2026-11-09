# pylint: disable=C0301, E0401
"""
Manage the WireGuard VPN connection based on local network detection using pyinfra.

This module detects whether the host is connected to a configured local network and conditionally starts the WireGuard VPN service when the host is outside that network.

Configuration: local_network_cidr (str): CIDR range identifying the local network. Used to determine whether the host is connected to the home network.

wireguard_interface (str): Name of the WireGuard interface to manage.
    Used to identify the corresponding `wg-quick` systemd service.

Operations:

1. Retrieve IPv4 addresses assigned to globally scoped network
   interfaces using `ip -j -4 addr show scope global`.
2. Parse the JSON output to inspect assigned IPv4 addresses.
3. Determine whether any assigned address belongs to the configured
   local network using Python's `ipaddress` module.
4. Start and enable the corresponding WireGuard systemd service
   when the host is outside the local network.

Service: wg-quick@<wireguard_interface>

- Running: True.
- Enabled: True.
- Requires sudo.

Notes:

- VPN activation is skipped when an address belongs to the configured
  local network.
- Network detection considers globally scoped IPv4 interfaces only.
- If network interface discovery fails, a RuntimeError is raised.
- IPv6 addresses are not considered.
- The VPN service is managed through systemd.
- The network membership check is performed before the service
  operation is evaluated.
"""

import ipaddress
import json
from pyinfra.operations import server
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

success, output = host.run_shell_command("ip -j -4 addr show scope global")

if not success:
    raise RuntimeError("Unable to retrieve network interfaces")

interfaces = json.loads("\n".join(output.stdout_lines))
network = ipaddress.ip_network(local_network_cidr) # pylint: disable=undefined-variable

on_local_network = any(
    ipaddress.ip_address(addr["local"]) in network
    for iface in interfaces
    for addr in iface.get("addr_info", [])
    if addr["family"] == "inet"
)

server.service(
    name="Connect to home VPN via WireGuard",
    service=f"wg-quick@{wireguard_interface}", # pylint: disable=undefined-variable
    running=True,
    enabled=True,
    _sudo=True,
    _if=lambda: not on_local_network,
)
