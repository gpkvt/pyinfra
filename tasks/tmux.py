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

Plugin management: Commands are executed without sudo: - install_plugins all - update_plugins all

Execution results are checked individually. If a command fails,
a RuntimeError is raised containing the failed command and its
combined output.

Notes:

- Package installation requires sudo.
- User configuration and resource deployment run without sudo.
- Plugin installation and updates are executed sequentially.
- Custom segments and themes are deployed independently of the
  tmux package installation.

"""

from pyinfra.operations import apt, files
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

apt.packages(
    name="Install tmux",
    packages=[
        "tmux",
        "tmux-plugin-manager",
        "python3-libtmux",
        "urlview",
    ],
    _sudo=True,
)

files.put(
    name="Confgure tmux",
    src="files/tmux/tmux.conf",
    dest=f"{homedir}/.tmux.conf",
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.put(
    name="Confgure tmux-powerline",
    src="files/tmux/tmux-powerline-config.sh",
    dest=f"{homedir}/.config/tmux-powerline/config.sh",
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.sync(
    name="Patching tmux-powerline",
    src="files/tmux/segments/",
    dest=f"{homedir}/.tmux/tmux-powerline/segments/",
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False,
)

files.sync(
    name="Deploy tmux-powerline themes",
    src="files/tmux/themes/",
    dest=f"{homedir}/.tmux/tmux-powerline/themes/",
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False,
)

commands = [
    "/usr/share/tmux-plugin-manager/bin/install_plugins all",
    "/usr/share/tmux-plugin-manager/bin/update_plugins all",
]

for command in commands:
    success, output = host.run_shell_command(
        command=command,
        _sudo=False,
    )

    if not success:
        lines = "\n".join(
            line.line for line in output.combined_lines
        )
        raise RuntimeError(f"Failed: {command}\n{lines}")
