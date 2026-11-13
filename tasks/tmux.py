# pylint: disable=C0301, E0401
"""
Install and configure tmux, its plugins, and tmux-powerline resources using pyinfra.

This module installs tmux and supporting utilities, deploys the user's tmux configuration, synchronizes custom tmux-powerline segments and themes, and installs or updates all configured tmux plugins.

Configuration: homedir (str): User's home directory, used for tmux configuration and plugin resources.

username (str): Owner of deployed files and directories.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of deployed files and directories.
    Retrieved from `host.data.usergroup`. Defaults to "root".

Operations:

1. Install the following APT packages:
    - tmux
    - tmux-plugin-manager
    - python3-libtmux
    - urlview

2. Deploy the tmux configuration from `files/tmux/tmux.conf`
   to `~/.tmux.conf`.

3. Deploy the tmux-powerline configuration from
   `files/tmux/tmux-powerline-config.sh` to
   `~/.config/tmux-powerline/config.sh`.

4. Synchronize custom tmux-powerline segments to
   `~/.tmux/tmux-powerline/segments/`.

5. Synchronize custom tmux-powerline themes to
   `~/.tmux/tmux-powerline/themes/`.

6. Install all available tmux plugins using the tmux plugin manager.

7. Update all installed tmux plugins.

File permissions:

- Configuration files: 0640.
- Segment and theme files: 0640.
- Segment and theme directories: 0750.

Plugin management:
- Plugin commands run as the configured user without sudo.
- Both scripts are checked for executability before they are invoked.
- Plugin installation and updates run only when the package or tmux
  configuration changes.
- Plugin commands are scheduled after package installation, not executed
  during deployment preparation.

Notes:

- Package installation requires sudo.
- User configuration and resource deployment run without sudo.
- Plugin installation and updates are executed sequentially.
- Unchanged deployments do not rerun plugin management.
- Custom segments and themes are deployed independently of the
  tmux package installation.
"""

from pyinfra.operations import apt, files, server
from pyinfra.operations.util import any_changed
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

tmux_packages = apt.packages(
    name="Install tmux",
    packages=[
        "tmux",
        "tmux-plugin-manager",
        "python3-libtmux",
        "urlview",
    ],
    _sudo=True,
)

tmux_config = files.put(
    name="Confgure tmux",
    src="files/tmux/tmux.conf",
    dest=f"{homedir}/.tmux.conf", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.put(
    name="Confgure tmux-powerline",
    src="files/tmux/tmux-powerline-config.sh",
    dest=f"{homedir}/.config/tmux-powerline/config.sh", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.sync(
    name="Patching tmux-powerline",
    src="files/tmux/segments/",
    dest=f"{homedir}/.tmux/tmux-powerline/segments/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False,
)

files.sync(
    name="Deploy tmux-powerline themes",
    src="files/tmux/themes/",
    dest=f"{homedir}/.tmux/tmux-powerline/themes/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False,
)

plugin_manager_install = (
    "/usr/share/tmux-plugin-manager/bin/install_plugins"
)
plugin_manager_update = (
    "/usr/share/tmux-plugin-manager/bin/update_plugins"
)

# These commands must run as scheduled operations, not through
# host.run_shell_command: package installation is only executed after
# pyinfra has finished preparing the deployment.
server.shell(
    name="Install and update tmux plugins",
    commands=[
        "if [ ! -x "
        + plugin_manager_install
        + " ] || [ ! -x "
        + plugin_manager_update
        + " ]; then "
        + "echo 'tmux-plugin-manager did not provide its plugin scripts' >&2; "
        + "exit 1; "
        + "fi; "
        + plugin_manager_install
        + " all && "
        + plugin_manager_update
        + " all",
    ],
    _sudo=False,
    _if=any_changed(tmux_packages, tmux_config),
)
