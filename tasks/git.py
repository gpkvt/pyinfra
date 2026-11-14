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
- File contents are deployed without sudo; immutable attributes are managed declaratively with sudo.
- The credentials file is managed only when `git_credentials`
  exists in the secrets dictionary and is not None; an existing unmanaged file is left untouched.
- The Linux immutable attribute is cleared only when credentials change and is always ensured afterwards.
- Credentials are managed through a Jinja2 template to support
  dynamic secret values.

"""
from pyinfra import host
from pyinfra.facts.files import File, FileContents
from pyinfra.operations import apt, files

from common import initialize

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
if git_credentials is not None:
    desired_content = "".join(f"{credential}\n" for credential in git_credentials)
    desired_lines = desired_content.splitlines()
    credentials_exists = host.get_fact(File, path=credentials_path, _sudo=False)
    current_content = (
        host.get_fact(FileContents, path=credentials_path, _sudo=False)
        if credentials_exists else None
    )

    # Clear the immutable flag only when an existing file needs new content.
    files.flags(
        name="Make git-credentials writable before updating",
        path=credentials_path,
        flags=["i"],
        present=False,
        _sudo=True,
        _if=lambda: credentials_exists and current_content != desired_lines,
    )

    files.template(
        name="Create git-credentials",
        src="templates/git/git-credentials.j2",
        dest=credentials_path,
        mode="600",
        git_credentials=git_credentials,
        _sudo=False,
    )

    # The built-in operation checks the post-template state and is a no-op
    # when the immutable flag is already set.
    files.flags(
        name="Protect git-credentials from modification",
        path=credentials_path,
        flags=["i"],
        present=True,
        _sudo=True,
    )
