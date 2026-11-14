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
from pathlib import Path

from jinja2 import Template
from pyinfra import host
from pyinfra.facts.files import File, FileContents
from pyinfra.operations import apt, files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)


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

# Create git-credentials
credentials_path = f"{homedir}/.git-credentials"  # pylint: disable=undefined-variable
git_credentials = secrets.get("git_credentials")  # pylint: disable=undefined-variable

if git_credentials is not None:
    template_source = Path("templates/git/git-credentials.j2").read_text()
    desired_content = Template(template_source).render(
        git_credentials=git_credentials
    )
    credentials_exists = host.get_fact(File, path=credentials_path)
    current_content = (
        host.get_fact(FileContents, path=credentials_path)
        if credentials_exists else None
    )
    desired_lines = desired_content.splitlines()

    # Immutable files must only be unlocked when the rendered content differs.
    if credentials_exists and current_content != desired_lines:
        files.flags(
            name="Make git-credentials writable before updating",
            path=credentials_path,
            flags=["i"],
            present=False,
            _sudo=True,
        )

    files.template(
        name="Create git-credentials",
        src="templates/git/git-credentials.j2",
        dest=credentials_path,
        mode="600",
        git_credentials=git_credentials,
        _sudo=False,
    )
    files.flags(
        name="Protect git-credentials from modification",
        path=credentials_path,
        flags=["i"],
        present=True,
        _sudo=True,
    )
else:
    files.flags(
        name="Protect existing git-credentials from modification",
        path=credentials_path,
        flags=["i"],
        present=True,
        _sudo=True,
        _if=lambda: bool(host.get_fact(File, path=credentials_path)),
    )
