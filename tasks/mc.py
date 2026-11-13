# pylint: disable=C0301, E0401
"""
Install and configure Midnight Commander (mc) using pyinfra.

This module installs Midnight Commander, deploys a custom Solarized skin, and configures mc to use the deployed skin in the user's configuration.

Configuration: homedir (str): User's home directory, used for mc configuration files.

username (str): Owner of the deployed skin file.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of the deployed skin file.
    Retrieved from `host.data.usergroup`. Defaults to "root".

Operations:

1. Install Midnight Commander using APT.
2. Deploy the Solarized skin from `files/mc/solarized.ini` to
   `~/.config/mc/solarized.ini`.
3. Set the skin file ownership and permissions.
4. Update the mc configuration file at `~/.config/mc/ini`
   to use the deployed Solarized skin.

File permissions:

- Solarized skin: 0640.

Notes:

- Package installation requires sudo.
- User configuration files are managed without sudo.
- Existing `skin` entries are replaced with the configured skin path.
- The configured skin path is explicitly set to the user's home directory.

"""

from pyinfra import host
from pyinfra.operations import apt, files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

apt.packages(
    name="Install mc",
    packages=[ "mc" ],
    _sudo=True,
)

files.put(
    name="Add mc skin",
    src="files/mc/solarized.ini",
    dest=f"{homedir}/.config/mc/solarized.ini", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.line(
    name="Configure mc skin",
    path=f"{homedir}/.config/mc/ini", # pylint: disable=undefined-variable
    line=r"^skin[[:space:]]*=.*$",
    replace=f"skin = {homedir}/.config/mc/solarized.ini", # pylint: disable=undefined-variable
    _sudo=False,
)
