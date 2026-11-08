"""
Configure the user's SSH client using a Jinja2 template and pyinfra.

This module deploys the SSH client configuration file from templates/ssh_config.j2 to the user's SSH configuration directory.

Configuration: ssh_dir (str): Path to the user's SSH directory, typically ~/.ssh, used as the destination for the SSH configuration.

Operations:

1. Render the SSH configuration template.
2. Deploy the generated configuration to `~/.ssh/config`.
3. Set restrictive file permissions.

File permissions:

- SSH configuration: 0600.

Notes:

- Configuration deployment runs without sudo.
- The SSH configuration is dynamically generated using Jinja2.
- Restrictive permissions help protect sensitive SSH client
  configuration settings.

"""

from pyinfra import host
from pyinfra.operations import files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

files.template(
    name="Configure ssh client",
    src="templates/ssh_config.j2",
    dest=f"{ssh_dir}/config",
    mode="600",
    _sudo=False,
)
