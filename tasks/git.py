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
- File contents are deployed without sudo; immutable attributes are changed with sudo only when needed.
- The credentials file is only created when `git_credentials`
  exists in the secrets dictionary and is not None.
- The Linux immutable attribute is removed only when credentials change and restored only when absent.
- Credentials are managed through a Jinja2 template to support
  dynamic secret values.

"""
import shlex

from pyinfra import host
from pyinfra.facts.files import File, FileContents
from pyinfra.operations import apt, files, server

from common import file_has_flag, initialize

if not hasattr(__import__('builtins'), 'homedir'):
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
quoted_credentials_path = shlex.quote(credentials_path)

if git_credentials is not None:
    desired_content = "".join(f"{credential}\n" for credential in git_credentials)
    desired_lines = desired_content.splitlines()
    credentials_exists = host.get_fact(File, path=credentials_path)
    current_content = (
        host.get_fact(FileContents, path=credentials_path)
        if credentials_exists else None
    )

    # Unlock only when the rendered credentials actually need updating.
    if credentials_exists and current_content != desired_lines:
        server.shell(
            name="Make git-credentials writable before updating",
            commands=[f"chattr -i {quoted_credentials_path}"],
            _if=lambda: file_has_flag(host, credentials_path, "i"),
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

    server.shell(
        name="Protect git-credentials from modification",
        commands=[f"chattr +i {quoted_credentials_path}"],
        # File existence was checked before template deployment; avoid reusing
        # that cached fact after the template creates or updates the file.
        _if=lambda: not file_has_flag(
            host, credentials_path, "i", refresh=True
        ),
        _sudo=True,
    )
else:
    # No earlier operation creates this file in the no-secrets branch.
    if host.get_fact(File, path=credentials_path):
        server.shell(
            name="Protect existing git-credentials from modification",
            commands=[f"chattr +i {quoted_credentials_path}"],
            _if=lambda: not file_has_flag(
                host, credentials_path, "i", refresh=True
            ),
            _sudo=True,
        )
