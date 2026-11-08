"""
Install, configure, and manage the Caddy web server using pyinfra.

This module installs the Caddy package, deploys its configuration file from a Jinja2 template, and ensures that the Caddy systemd service is enabled and running.

Configuration: caddy_config (dict): Caddy configuration values retrieved from host.data.caddy_config. Defaults to an empty dictionary.

Operations:

1. Install the Caddy package using APT.
2. Deploy the Caddyfile from `templates/Caddyfile.j2` to
   `/etc/caddy/Caddyfile`.
3. Set the configuration file ownership to `caddy:root`
   with permissions `0640`.
4. Ensure the Caddy service is enabled and running.
5. Reload Caddy when the configuration file has changed.

Deployment: configure_caddy: Groups Caddy configuration operations into a named pyinfra deployment.

Notes:

- Package installation and configuration deployment require sudo.
- The configuration file is managed through a Jinja2 template.
- Caddy is reloaded only when the deployed configuration changes.
- The service is configured to start automatically and remain running.
"""

from pyinfra.operations import apt, files, systemd, server
from pyinfra.api import deploy
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

apt.packages(
    name="Install Caddy",
    packages=["caddy"],
    _sudo=True,
)

@deploy("Configure Caddy")
def configure_caddy():

    caddy_config = files.template(
        name="Deploy configuration file",
        src="templates/Caddyfile.j2",
        dest="/etc/caddy/Caddyfile",
        user="caddy",
        group="root",
        mode="640",
        caddy_conf=host.data.get("caddy_config", {}),
        _sudo=True,
    )

    systemd.service(
        name="Ensure Caddy is enabled and running",
        service="caddy",
        enabled=True,
        running=True,
    )

    server.shell(
        name="Reload Caddy configuration",
        commands=["systemctl reload caddy"],
        _if=caddy_config.did_change,
        _sudo=True,
    )

configure_caddy()
