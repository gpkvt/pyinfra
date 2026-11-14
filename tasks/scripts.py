# pylint: disable=C0301, E0401
"""
Deploy custom scripts and create system-wide symbolic links using pyinfra.

This module synchronizes scripts from the local files/scripts/ directory to the user's home directory and creates symbolic links in /usr/local/bin/ so the scripts can be executed from anywhere.

Configuration: homedir (str): User's home directory, used as the destination for deployed scripts.

username (str): Owner of deployed scripts.
    Retrieved from `host.data.username`. Defaults to "root".

usergroup (str): Group ownership of deployed scripts.
    Retrieved from `host.data.usergroup`. Defaults to "root".

Operations:

1. Synchronize scripts from `files/scripts/` to `~/scripts/`.
2. Preserve existing destination files that are not present in
   the source directory by disabling deletion.
3. Recursively discover all files in the local scripts directory.
4. Create symbolic links in `/usr/local/bin/` pointing to their
   corresponding deployed files.

File permissions:

- Deployed scripts: 0750.
- Symbolic links retain the permissions of their target files.

Notes:

- Script deployment runs without sudo.
- System-wide symbolic links are created with sudo.
- Symlink names use the original filename.
- Existing destination files are not automatically deleted.

"""

from pathlib import Path
from pyinfra.operations import files
from pyinfra import host

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

src = Path("files/scripts/")

files.sync(
    name="Install scripts",
    src="files/scripts/",
    dest=f"{homedir}/scripts/", # pylint: disable=undefined-variable
    delete=False,
    user=host.data.get("username", "root"),
    group=host.data.get("usergroup", "root"),
    mode="750",
    _sudo=False,
)

for file in src.rglob("*"):
    if file.is_file():
        files.link(
            name=f"Symlink {file.name}",
            path=f"/usr/local/bin/{file.name}",
            target=f"{homedir}/scripts/{file.relative_to(src)}", # pylint: disable=undefined-variable
            _sudo=True,
        )
