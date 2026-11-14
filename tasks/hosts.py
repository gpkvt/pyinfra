# pylint: disable=C0301, E0401
"""
Manage system hostname mappings in /etc/hosts using pyinfra.

Configuration: hostnames (dict[str, list[str]]): Mapping of IP addresses to
lists of hostnames, retrieved from host.data.hostnames.

    Defaults to:
        {"127.0.0.1": ["localhost"]}

Operations:

1. Validate that each IP address maps to a list of non-empty hostnames.
2. Ensure each non-empty mapping is present in `/etc/hosts`.
3. Remove an IP address entry when its configured hostname list is empty.

Notes:

- Existing `/etc/hosts` entries are managed by pyinfra.
- Multiple hostnames are represented as individual list items.
- An empty list removes all `/etc/hosts` entries for that IP address.
- If no custom hostname mappings are configured, localhost is configured as
  the default entry.
"""

from pyinfra.operations import server
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

hostnames = host.data.get("hostnames", {"127.0.0.1": ["localhost"]})
if not isinstance(hostnames, dict):
    raise ValueError("hostnames must be a mapping of IP addresses to lists of hostnames")

for ip, names in hostnames.items():
    if not isinstance(names, list) or any(
        not isinstance(name, str) or not name.strip() for name in names
    ):
        raise ValueError(
            f"Invalid hostnames for {ip}: expected a list of non-empty strings"
        )

    if not names:
        server.etc_hosts(
            name=f"Remove hostnames for {ip}",
            ip=ip,
            present=False,
            _sudo=True,
        )
        continue

    server.etc_hosts(
        name=f"Set hostnames for {ip}",
        ip=ip,
        hostnames=names,
        _sudo=True,
    )
