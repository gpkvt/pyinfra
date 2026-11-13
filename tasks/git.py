# pylint: disable=C0301, E0401, C0116
"""
Install Git and configure user-level Git settings and credentials using pyinfra.

This module ensures Git is installed, deploys the user's Git configuration file, and optionally creates a Git credentials file from decrypted secrets.

Configuration: homedir (str): User's home directory, used as the destination for Git configuration and credentials files.

secrets (dict): Decrypted secrets dictionary.
    Expected structure:
        git_credentials (list): Git credentials to be rendered
            into the credentials file. Defaults to an empty list.

Operations:

1. Install Git using APT.
2. Deploy the Git configuration file from `files/git/gitconfig`
   to `~/.gitconfig`.
3. If Git credentials are configured, render the credentials
   template from `templates/git/git-credentials.j2` to
   `~/.git-credentials`.

File permissions:

- ~/.gitconfig: 0640.
- ~/.git-credentials: 0600.

Notes:

- Git installation uses the system package manager.
- Configuration files are deployed without sudo.
- The credentials file is only created when `git_credentials`
  exists in the secrets dictionary and is not None.
- Credentials are managed through a Jinja2 template to support
  dynamic secret values.

"""
from pyinfra import host
from pyinfra.operations import apt, files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

def set_immutable(path, immutable=True):
    """Ensure the immutable filesystem flag is present or absent."""
    files.flags(
        name=f"{'Set' if immutable else 'Clear'} immutable flag for {path}",
        path=path,
        flags=["i"],
        present=immutable,
        _sudo=True,
    )

# Install git
apt.packages(
    name="Install git",
    packages=["git"],
)

# Create gitconfig
files.put(
    name="Create gitconfig",
    src="files/git/gitconfig",
    dest=f"{homedir}/.gitconfig", # pylint: disable=undefined-variable
    mode="640",
    _sudo=False,
)

# Manage credentials only when the encrypted secret key is configured.
# An existing file remains untouched (and keeps its immutable flag) otherwise.
if secrets.get("git_credentials") is not None: # pylint: disable=undefined-variable
    set_immutable(f"{homedir}/.git-credentials", False) # pylint: disable=undefined-variable

    files.template(
        name="Create git-credentials",
        src="templates/git/git-credentials.j2",
        dest=f"{homedir}/.git-credentials", # pylint: disable=undefined-variable
        mode="600",
        git_credentials=secrets.get("git_credentials", []), # pylint: disable=undefined-variable
        _sudo=False,
    )

    set_immutable(f"{homedir}/.git-credentials", True) # pylint: disable=undefined-variable
