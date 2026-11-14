# pylint: disable=C0301, E0401
"""
Manage the WireGuard VPN connection based on local network detection using pyinfra.

This module detects whether the host is connected to a configured local network and conditionally starts the WireGuard VPN service when the host is outside that network.

Configuration: local_network_cidr (str): CIDR range identifying the local network. Used to determine whether the host is connected to the home network.

wireguard_interface (str): Name of the WireGuard interface to manage.
    Used to identify the corresponding `wg-quick` systemd service.

Operations:

1. Retrieve IPv4 addresses with pyinfra's built-in `hardware.Ipv4Addrs` fact.
2. Exclude loopback, link-local and unspecified addresses to match global-scope detection.
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
- If no eligible IPv4 address is found, the host is treated as outside the local network.
- IPv6 addresses are not considered.
- The VPN service is managed through systemd.
- The network membership check is performed before the service
  operation is evaluated.
"""

import ipaddress
from pyinfra import host
from pyinfra.facts.hardware import Ipv4Addrs
from pyinfra.operations import server

from common import initialize

if not hasattr(__import__("builtins"), "homedir"):
    initialize(host)

ipv4_addresses = host.get_fact(Ipv4Addrs) or {}
local_network_cidr = host.data.get("local_network_cidr") or "10.0.0.0/24"
wireguard_interface = host.data.get("wireguard_interface", False)
network = ipaddress.ip_network(local_network_cidr) # pylint: disable=undefined-variable

on_local_network = any(
    address in network
    for interface_addresses in ipv4_addresses.values()
    for address in map(ipaddress.ip_address, interface_addresses)
    if not address.is_loopback and not address.is_link_local and not address.is_unspecified
)

server.service(
    name="Connect to home VPN via WireGuard",
    service=f"wg-quick@{wireguard_interface}", # pylint: disable=undefined-variable
    running=True,
    enabled=True,
    _sudo=True,
    _if=lambda: not on_local_network,
)
