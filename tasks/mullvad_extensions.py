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
from urllib.parse import urlsplit

from common import command_output, initialize
from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import files, server

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

    # Track the configured URL so downloads happen only when the source changes.
    # The temporary file and marker are promoted only after a complete download.
    source_marker = f"{extension_path}.source-sha256"
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    installed_source_hash = command_output(
        host,
        f"cat {shlex.quote(source_marker)} 2>/dev/null || true",
    ).strip()
    extension_exists = host.get_fact(File, path=extension_path)

    if installed_source_hash != source_hash or not extension_exists:
        temporary_path = f"{extension_path}.download"
        temporary_marker = f"{source_marker}.tmp"
        download_command = (
            f"rm -f {shlex.quote(temporary_path)} "
            f"{shlex.quote(temporary_marker)}; "
            f"if curl --fail --location --silent --show-error "
            f"--retry 3 --retry-all-errors --retry-delay 2 "
            f"--connect-timeout 20 --max-time 300 "
            f"--output {shlex.quote(temporary_path)} "
            f"{shlex.quote(url)} "
            f"&& test -s {shlex.quote(temporary_path)} "
            f"&& chown {shlex.quote(f'{user}:{group}')} "
            f"{shlex.quote(temporary_path)} "
            f"&& chmod 0600 {shlex.quote(temporary_path)} "
            f"&& mv {shlex.quote(temporary_path)} {shlex.quote(extension_path)} "
            f"&& printf '%s\\n' {shlex.quote(source_hash)} "
            f"> {shlex.quote(temporary_marker)} "
            f"&& chown {shlex.quote(f'{user}:{group}')} "
            f"{shlex.quote(temporary_marker)} "
            f"&& chmod 0600 {shlex.quote(temporary_marker)} "
            f"&& mv {shlex.quote(temporary_marker)} {shlex.quote(source_marker)}; "
            f"then echo 'Downloaded {name}'; "
            f"else rm -f {shlex.quote(temporary_path)} "
            f"{shlex.quote(temporary_marker)}; "
            f"echo 'WARNING: Could not download {name}; keeping the existing extension and retrying on the next deployment'; "
            f"fi"
        )
        server.shell(
            name=f"Download {name}",
            commands=[download_command],
        )

files.put(
    name="Manage Mullvad Browser preferences",
    src="files/mullvad-user.js",
    dest=f"{profile_dir}/user.js",
    mode="600",
)
