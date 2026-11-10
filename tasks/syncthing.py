"""Install and configure a per-user Syncthing service.

Configuration:
    syncthing (dict): Optional settings. Supported keys:
        gui_address (str): GUI listen address. Defaults to 127.0.0.1:8384.
    username (str): Account that owns the Syncthing instance.

The task installs the distribution package, enables the packaged
syncthing@.service instance for the configured user, and sets the GUI
listen address through Syncthing's CLI. Device and folder sharing remains
managed through Syncthing's GUI or REST/CLI interface.
"""

import shlex

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, server, systemd

if not hasattr(__import__("builtins"), "homedir"):
    from common import initialize

    initialize(host)

syncthing_config = host.data.get("syncthing", {})
username = host.data.get("username", "root")
gui_address = syncthing_config.get("gui_address", "127.0.0.1:8384")

apt.packages(
    name="Install Syncthing",
    packages=["syncthing"],
    _sudo=True,
)

systemd.service(
    name=f"Enable and start Syncthing for {username}",
    service=f"syncthing@{username}",
    enabled=True,
    running=True,
    _sudo=True,
)

# Configure the running instance as its owning user. Keeping the GUI bound
# to loopback by default avoids exposing the unauthenticated setup wizard.
# Read the current value as a fact so the operation is skipped when already
# configured; this keeps repeated deployments idempotent.
cli_prefix = f"runuser --user {shlex.quote(username)} -- syncthing cli config gui raw-address"
current_gui_address = host.get_fact(
    Command,
    command=f"{cli_prefix} get",
)

server.shell(
    name="Configure Syncthing GUI listen address",
    commands=[
        f"{cli_prefix} set {shlex.quote(gui_address)}"
    ],
    _sudo=True,
    _if=lambda: current_gui_address.strip() != gui_address,
)
