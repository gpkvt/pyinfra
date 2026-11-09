# pylint: disable=C0301, E0401
"""
Deploy and configure Zsh dotfiles, shell configuration, and plugins using pyinfra.

This module synchronizes custom Zsh dotfiles, deploys application configuration files, generates the user's Zsh startup configuration, configures zplug plugins, and ensures that Zsh is the user's default shell.

Configuration: homedir (str): User's home directory, used as the destination for Zsh configuration and dotfiles.

username (str): User account to configure.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of deployed files and directories.
    Retrieved from `host.data.usergroup`. Defaults to "root".

zshrc_imports (list[str]): Additional Zsh configuration files
    or imports to include in `.zshrc`.
    Retrieved from `host.data.zshrc_imports`.
    Defaults to an empty list.

zplug_plugins (list[str]): Zsh plugins to configure through zplug.
    Retrieved from `host.data.zplug_plugins`.
    Defaults to an empty list.

Operations:

1. Synchronize Zsh dotfiles from `files/dotfiles/zsh/` to
   `~/.dotfiles/zsh/`, preserving existing destination files
   that are not present in the source.

2. Deploy the Hyfetch configuration from `files/hyfetch.conf`
   to `~/.config/neowofetch/config.conf`.

3. Generate the user's `.zshrc` from
   `templates/dotfiles/zshrc.j2`, including configured imports.

4. Generate the zplug configuration from
   `templates/dotfiles/zplug.zsh.j2`, using the configured
   plugin list.

5. Set `/bin/zsh` as the default login shell for the configured user.

File permissions:

- Zsh dotfiles: 0750.
- Zsh dotfile directories: 0755.
- Hyfetch configuration: 0640.
- `.zshrc`: 0640.
- zplug configuration: 0640.

Notes:

- File deployment runs without sudo.
- The default shell is managed through pyinfra's user operation.
- Existing dotfiles not present in the source directory are preserved.
- Zsh configuration and plugin definitions are generated dynamically
  using Jinja2 templates.
- The default shell is configured independently of the dotfile
  deployment operations.
"""

from pyinfra.operations import files, server
from pyinfra import host

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
