# pylint: disable=C0301, E0401
"""
Deploy and configure Powerlevel10k and Powerline resources using pyinfra.

This module deploys the Powerlevel10k Zsh configuration file, synchronizes custom Powerline themes, and installs the associated fonts into the user's home directory.

Configuration: homedir (str): User's home directory, used as the destination for configuration files, themes, and fonts.

username (str): Owner of deployed files and directories.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of deployed files and directories.
    Retrieved from `host.data.usergroup`. Defaults to "root".

Operations:

1. Deploy the Powerlevel10k configuration from
   `files/powerline/p10k.zsh` to `~/.p10k.zsh`.
2. Synchronize custom Powerline themes from
   `files/powerline/themes/` to `~/.config/powerline/themes/`.
3. Synchronize Powerline fonts from `files/powerline/fonts/`
   to `~/.fonts/`.

File permissions:

- Powerlevel10k configuration: 0750.
- Theme and font files: 0640.
- Theme and font directories: 0750.

Notes:

- All files and directories are deployed without sudo.
- Ownership is assigned to the configured username and user group.
- Directory synchronization ensures the destination contains
  the configured themes and fonts.
- This module deploys configuration and resources but does not
  install the Powerline or Powerlevel10k packages themselves.

"""

from pyinfra.operations import files
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

files.put(
    name="Configure powerline",
    src="files/powerline/p10k.zsh",
    dest=f"{homedir}/.p10k.zsh", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="750",
    _sudo=False,
)
files.sync(
    name="Install theme",
    src="files/powerline/themes/",
    dest=f"{homedir}/.config/powerline/themes/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False
)
files.sync(
    name="Install fonts",
    src="files/powerline/fonts/",
    dest=f"{homedir}/.fonts/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    dir_mode="750",
    _sudo=False
)
