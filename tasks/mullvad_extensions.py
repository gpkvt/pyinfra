# pylint: disable=C0301, E0401
"""
Manage Mullvad Browser extensions and user preferences using pyinfra.

Configures the Mullvad Browser distribution directory, reconciles configured browser extensions, and installs a managed user.js file containing browser preferences.

Host configuration:

mullvad_browser_dir:
    Mullvad Browser distribution directory.
    Defaults to /usr/lib/mullvad-browser/distribution.

mullvad_extensions:
    Dictionary of extensions to download and deploy. Each entry
    must contain:
        url: Download URL of the extension XPI file.
        id: Firefox extension/add-on ID used as the XPI filename.

username:
    Owner of the extensions directory and downloaded extensions.
    Defaults to root.

usergroup:
    Group owner of the extensions directory and downloaded
    extensions. Defaults to root.

Operations:

1. Initialize common host configuration if necessary.
2. Create the Mullvad Browser extensions directory.
3. Declaratively download configured extensions, naming each XPI file
   after its extension ID and refreshing it when the configured URL changes.
4. Deploy the managed user.js file to the Mullvad Browser
   distribution directory.

Restart Mullvad Browser after deployment for changes to take effect.
"""

import hashlib
import re
import shlex
from io import StringIO
from urllib.parse import urlsplit

from common import command_output, initialize
from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files

if not hasattr(__import__('builtins'), 'homedir'):
    initialize(host)

profile_dir = host.data.get(
    "mullvad_browser_dir",
    "/usr/lib/mullvad-browser/distribution",
)
extensions = host.data.get("mullvad_extensions", {})
if not isinstance(extensions, dict):
    raise ValueError("mullvad_extensions must be a dictionary")
extensions_dir = f"{profile_dir}/extensions"

user = host.data.get("username", "root")
group = host.data.get("usergroup", "root")

# Create extensions directory
files.directory(
    name="Create Mullvad Browser extensions directory",
    path=extensions_dir,
    user=user,
    group=group,
    mode="0700",
)

# Reconcile each configured extension and its source URL
for name, extension in extensions.items():
    if not isinstance(extension, dict):
        raise ValueError(f"Invalid Mullvad extension configuration: {name}")
    extension_id = extension.get("id")
    url = extension.get("url")
    if (
        not isinstance(extension_id, str)
        or not re.fullmatch(
            r"(?:[A-Za-z0-9._@+-]+|\{[0-9A-Fa-f-]{36}\})",
            extension_id,
        )
    ):
        raise ValueError(f"Invalid Mullvad extension ID: {extension_id!r}")

    try:
        parsed_url = urlsplit(url) if isinstance(url, str) else None
        valid_url = (
            parsed_url is not None
            and parsed_url.scheme == "https"
            and bool(parsed_url.hostname)
            and not parsed_url.username
            and not parsed_url.password
        )
    except ValueError:
        valid_url = False

    if not valid_url:
        raise ValueError(f"Invalid Mullvad extension URL for {name!r}")

    extension_path = f"{extensions_dir}/{extension_id}.xpi"

    # files.download does not re-fetch an existing file by default. Keep a
    # marker for the configured URL so URL changes trigger one forced download
    # without downloading every time pyinfra runs.
    source_marker = f"{extension_path}.source-sha256"
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    installed_source_hash = command_output(
        host,
        f"cat {shlex.quote(source_marker)} 2>/dev/null || true",
    ).strip()
    extension_exists = host.get_fact(File, path=extension_path)

    if installed_source_hash != source_hash or not extension_exists:
        files.download(
            name=f"Download {name}",
            src=url,
            dest=extension_path,
            user=user,
            group=group,
            mode="0600",
            force=True,
        )
        files.put(
            name=f"Record {name} source URL",
            src=StringIO(f"{source_hash}\n"),
            dest=source_marker,
            user=user,
            group=group,
            mode="0600",
        )

files.put(
    name="Manage Mullvad Browser preferences",
    src="files/mullvad-user.js",
    dest=f"{profile_dir}/user.js",
    mode="600",
)
