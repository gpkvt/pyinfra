"""
Manage system hostname mappings in /etc/hosts using pyinfra.

This module configures hostname-to-IP address mappings based on the current host's configuration. Each mapping is applied individually using pyinfra's server.etc_hosts operation.

Configuration: hostnames (dict[str, str | list[str]]): Mapping of IP addresses to one or more hostnames, retrieved from host.data.hostnames.

    Defaults to:
        {"127.0.0.1": "localhost"}

Operations:

1. Iterate over all configured IP address and hostname mappings.
2. Ensure each mapping is present in `/etc/hosts`.
3. Apply changes with sudo privileges.

Notes:

- Existing `/etc/hosts` entries are managed by pyinfra.
- Multiple hostnames can be associated with a single IP address.
- If no custom hostname mappings are configured, localhost
  is configured as the default entry.

"""

from pyinfra.operations import server
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

hostnames = host.data.get("hostnames", {"127.0.0.1": "localhost"})

for key, value in hostnames.items():
    server.etc_hosts(
        name=f"Set hostnames for {key}",
        ip=key,
        hostnames=value,
        _sudo=True,
    )
