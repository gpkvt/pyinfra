# pylint: disable=C0301, E0401
"""
Manage Mullvad Browser extensions and user preferences using pyinfra.

Configures the Mullvad Browser distribution directory, downloads and deploys configured browser extensions, and installs a managed user.js file containing browser preferences.

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
3. Download configured extensions, naming each XPI file after
   its extension ID.
4. Deploy the managed user.js file to the Mullvad Browser
   distribution directory.

Restart Mullvad Browser after deployment for changes to take effect.
"""

from pyinfra import host
from pyinfra.operations import files

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

profile_dir=host.data.get("mullvad_browser_dir", "/usr/lib/mullvad-browser/distribution")
extensions=host.data.get("mullvad_extensions", {})
extensions_dir = f"{profile_dir}/extensions"

user=host.data.get("username", "root")
group=host.data.get("usergroup", "root")

# Create extensions directory
files.directory(
    name="Create Mullvad Browser extensions directory",
    path=extensions_dir,
    user=user,
    group=group,
    mode="0700",
)

# Download and deploy extensions only if they don't already exist
for name, extension in extensions.items():
    extension_path = f"{extensions_dir}/{extension['id']}.xpi"

    if not host.get_fact(
        __import__("pyinfra").facts.files.File,
        path=extension_path,
    ):
        files.download(
            name=f"Download {name}",
            src=extension["url"],
            dest=extension_path,
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
