# pylint: disable=C0301, E0401
"""
Configure the user's SSH client using a Jinja2 template and pyinfra.

The generated ~/.ssh/config starts with a hardened Host * baseline:
known-host hashing, accept-new host-key verification, host-key updates,
public-key authentication, restricted agent/forwarding behavior, and
connection timeouts/keepalives. Per-host entries from ssh_config are
rendered afterwards for additional host-specific settings.

OpenSSH keeps the first value obtained for each option. The baseline
therefore intentionally takes precedence over later host entries for
the hardened options.

Configuration:
    ssh_config (dict): Mapping of OpenSSH Host patterns to configuration
        lines.
    homedir (str): Home directory used to locate ~/.ssh/config.

The configuration is deployed without sudo with mode 0600.
"""

from pyinfra import host
from pyinfra.operations import files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

ssh_dir = f"{host.data.homedir}/.ssh"

files.template(
    name="Configure hardened ssh client",
    src="templates/ssh_config.j2",
    dest=f"{ssh_dir}/config", # pylint: disable=undefined-variable
    mode="600",
    _sudo=False,
)
