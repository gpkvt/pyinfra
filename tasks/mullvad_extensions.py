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
import json
import math
from io import StringIO
import re
import shlex
from urllib.parse import urlsplit

from common import command_output, initialize
from pyinfra import host
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

# Validate configuration before querying the host or scheduling downloads.
# Collect metadata locally, then inspect all installed XPIs in a single fact
# query rather than issuing two separate remote checks per extension.
extension_specs = []
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

    if any(existing_id == extension_id for _, existing_id, *_ in extension_specs):
        raise ValueError(f"Duplicate Mullvad extension ID: {extension_id!r}")

    extension_path = f"{extensions_dir}/{extension_id}.xpi"
    source_marker = f"{extension_path}.source-sha256"
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    extension_specs.append(
        (name, extension_id, url, extension_path, source_marker, source_hash)
    )

# Each successful check prints its extension ID. Missing files, empty XPIs,
# unreadable or outdated source markers print nothing. This works correctly in
# root-owned distribution directories and takes one remote round trip.
check_commands = [
    f"if test -s {shlex.quote(path)} "
    f"&& test \"$(cat {shlex.quote(marker)} 2>/dev/null)\" "
    f"= {shlex.quote(source_hash)}; then "
    f"printf '%s\\n' {shlex.quote(extension_id)}; fi"
    for _, extension_id, _, path, marker, source_hash in extension_specs
]
current_extensions = set()
if check_commands:
    current_extensions = set(
        command_output(host, "\n".join(check_commands), _sudo=True).splitlines()
    )

# Only stale or missing extensions need a download. Failed downloads preserve
# the old XPI and source marker, and remain retryable on the next deployment.
for name, extension_id, url, extension_path, source_marker, source_hash in extension_specs:
    if extension_id in current_extensions:
        continue
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
        f"&& printf '%s\\\\n' {shlex.quote(source_hash)} "
        f"> {shlex.quote(temporary_marker)} "
        f"&& chown {shlex.quote(f'{user}:{group}')} "
        f"{shlex.quote(temporary_marker)} "
        f"&& chmod 0600 {shlex.quote(temporary_marker)} "
        f"&& mv {shlex.quote(temporary_marker)} {shlex.quote(source_marker)}; "
        f"then echo 'Downloaded {name}'; "
        f"else rm -f {shlex.quote(temporary_path)} "
        f"{shlex.quote(temporary_marker)}; "
        f"echo 'WARNING: Could not download {name}; keeping the existing extension and retrying on the next deployment' >&2; "
        f"false; fi"
    )
    server.shell(
        name=f"Download {name}",
        commands=[download_command],
        _sudo=True,
        _ignore_errors=True,
    )

# Prefer explicit inventory-managed preferences when present. The default
# tracked user.js remains in use for inventories without this mapping.
prefs = host.data.get("mullvad_browser_prefs")
if prefs is None:
    preference_source = "files/mullvad-user.js"
else:
    if not isinstance(prefs, dict):
        raise ValueError("mullvad_browser_prefs must be a dictionary")
    managed_prefs = {"extensions.installDistroAddons": True, **prefs}
    lines = ["// Managed Mullvad Browser user.js (pyinfra)"]
    for key, value in sorted(managed_prefs.items()):
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", key):
            raise ValueError(f"Invalid Mullvad Browser preference name: {key!r}")
        if (
            not isinstance(value, (str, int, float, bool))
            or isinstance(value, float) and not math.isfinite(value)
        ):
            raise ValueError(f"Unsupported Mullvad Browser preference value: {key!r}")
        lines.append(f"user_pref({json.dumps(key)}, {json.dumps(value)});")
    preference_source = StringIO("\n".join(lines) + "\n")

files.put(
    name="Manage Mullvad Browser preferences",
    src=preference_source,
    dest=f"{profile_dir}/user.js",
    mode="600",
)
