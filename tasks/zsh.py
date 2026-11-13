# pylint: disable=C0301, E0401
"""
Deploy and configure Zsh dotfiles, shell configuration, and plugins using pyinfra.

This module synchronizes custom Zsh dotfiles, deploys application configuration files,
generates the user's Zsh startup configuration, configures zplug plugins, installs
the MPRIS command-line client and deploys a LiMusic-specific HyFetch helper, and ensures that Zsh is the user's
default shell.

Configuration: homedir (str): User's home directory, used as the destination for
Zsh configuration and dotfiles.

username (str): User account to configure.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of deployed files and directories.
    Retrieved from `host.data.usergroup`. Defaults to "root".

zshrc_imports (list[str]): Additional Zsh configuration files or imports to include
    in `.zshrc`. Retrieved from `host.data.zshrc_imports`. Defaults to an empty list.

zplug_plugins (list[str]): Zsh plugins to configure through zplug.
    Retrieved from `host.data.zplug_plugins`. Defaults to an empty list.

Operations:
1. Synchronize Zsh dotfiles from `files/dotfiles/zsh/` to `~/.dotfiles/zsh/`.
2. Install playerctl for Hyfetch's MPRIS-based now-playing information.
3. Deploy the LiMusic now-playing helper to `~/.local/bin/hyfetch-song`.
4. Deploy the Hyfetch configuration to `~/.config/neowofetch/config.conf`.
5. Generate `.zshrc` and the zplug configuration from Jinja2 templates.
6. Set `/bin/zsh` as the user's default login shell.

File permissions:
- Zsh dotfiles: 0750; directories: 0755.
- Hyfetch configuration, `.zshrc`, and zplug configuration: 0640.
- Hyfetch LiMusic helper: 0750.

Notes:
- File deployment runs without sudo.
- Existing dotfiles not present in the source directory are preserved.
- APT manages playerctl idempotently; the helper displays only a playing LiMusic MPRIS session and exits silently otherwise.
"""

from pyinfra import host
from pyinfra.operations import apt, files, server

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

files.sync(
    name="Ensure that zsh .dotfiles are in the expected state",
    src="files/dotfiles/zsh/",
    dest=f"{homedir}/.dotfiles/zsh/", # pylint: disable=undefined-variable
    delete=False,
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="750",
    dir_mode="755",
    _sudo=False,
)

apt.packages(
    name="Ensure playerctl is installed for Hyfetch music metadata",
    packages=["playerctl"],
)

files.directory(
    name="Create Hyfetch helper directory",
    path=f"{homedir}/.local/bin/", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="755",
    _sudo=False,
)

files.put(
    name="Deploy HyFetch LiMusic now-playing helper",
    src="files/hyfetch-song",
    dest=f"{homedir}/.local/bin/hyfetch-song", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="750",
    _sudo=False,
)

files.put(
    name="Configure hyfetch",
    src="files/hyfetch.conf",
    dest=f"{homedir}/.config/neowofetch/config.conf", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    _sudo=False,
)

files.template(
    name="Ensure that .zshrc has the proper state",
    src="templates/dotfiles/zshrc.j2",
    dest=f"{homedir}/.zshrc", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    zshrc_imports=host.data.get("zshrc_imports", []),
    _sudo=False,
)

files.template(
    name="Ensure that zplug has the proper configuration",
    src="templates/dotfiles/zplug.zsh.j2",
    dest=f"{homedir}/.dotfiles/zsh/zplug.zsh", # pylint: disable=undefined-variable
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="640",
    zplug_plugins=host.data.get("zplug_plugins", []),
    _sudo=False,
)

server.user(
    name="Ensure that the default shell is set to zsh",
    user=host.data.get("username", "root"),
    shell="/bin/zsh",
)
