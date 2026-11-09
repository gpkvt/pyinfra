# pylint: disable=C0301, E0401, C0115, C0116
"""
Install, configure, and manage the UFW firewall using pyinfra.

This module installs UFW, configures default firewall policies, manages application-specific firewall rules, and ensures the firewall is enabled. Firewall rules are applied conditionally based on the host configuration and the current firewall state.

Configuration: host.data.ufw (dict): Firewall configuration defining which applications and services are allowed or denied.

    Supported keys:
        chromecast-dlna (str): Allow or deny Chromecast/DLNA traffic.
        kdeconnect (str): Allow or deny KDE Connect traffic.
        localsend (str): Allow or deny LocalSend traffic.
        ssh (str): Allow or deny SSH traffic on TCP port 22.

    Values:
        "Allow": Add an allow rule.
        Any other configured value: Remove the corresponding
        allow rule or add a deny rule for SSH.

Facts: UfwActive: Checks whether UFW is currently active using ufw status.

    Returns:
        bool: True if the firewall is active, otherwise False.

UfwRules:
    Retrieves the currently configured UFW rules using
    `sudo ufw status` and filters out status and header lines.

    Returns:
        set[str]: Existing firewall rules.

UfwDefaults:
    Retrieves the default incoming and outgoing firewall policies
    using `sudo ufw status verbose`.

    Returns:
        dict: Default firewall policies, such as incoming and
        outgoing actions.

Helper functions: ufw_rule_exists(rule, action="ALLOW", scope="Anywhere"): Checks whether a firewall rule matching the specified rule, action, and scope exists.

    Returns:
        bool: True if a matching rule exists, otherwise False.

Operations:

1. Install UFW using APT.

2. Configure default firewall policies:
    - Deny incoming connections.
    - Allow outgoing connections.
   Changes are applied only when the current policies differ.

3. Configure application profiles when enabled in host configuration:
    - Chromecast/DLNA: Deploy the application profile and
      allow or remove its firewall rule.
    - KDE Connect: Deploy the application profile and
      allow or remove its firewall rule.
    - LocalSend: Deploy the application profile and
      allow or remove its firewall rule.

4. Configure SSH access:
    - Allow TCP port 22 when SSH is configured as "Allow".
    - Deny TCP port 22 otherwise.
   SSH rules are configured before enabling the firewall to
   help prevent accidental loss of remote access.

5. Enable UFW when it is not already active.

Application profiles:

- Chromecast/DLNA: `/etc/ufw/applications.d/chromecast-dlna`
- KDE Connect: `/etc/ufw/applications.d/kdeconnect`
- LocalSend: `/etc/ufw/applications.d/localsend`

File permissions:

- Application profiles: root:root, mode 0640.

Notes:

- Firewall configuration commands require sudo.
- Application profiles are deployed only when their corresponding
  configuration keys are present.
- Existing rules are checked before adding or removing rules
  to avoid unnecessary changes.
- UFW is enabled non-interactively using `--force`.
- Default incoming traffic is denied and outgoing traffic is allowed.
- SSH access is explicitly configured before firewall activation.
"""

from pyinfra.operations import apt, server, files
from pyinfra import host
from pyinfra.api import FactBase

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

class UfwActive(FactBase):
    command = "ufw status"

    def process(self, output):
        return bool(output and output[0] == "Status: active")

class UfwRules(FactBase):
    command = "sudo ufw status"

    def process(self, output):
        return {
            line.strip()
            for line in output
            if line.strip()
            and not line.strip().startswith(("Status:", "To ", "--"))
        }

def ufw_rule_exists(rule, action="ALLOW", scope="Anywhere"):
    return any(
        line.split()[0] == rule
        and action in line.split()
        and scope in line.split()
        for line in host.get_fact(UfwRules)
    )

class UfwDefaults(FactBase):
    command = "sudo ufw status verbose"

    def process(self, output):
        for line in output:
            if line.strip().startswith("Default:"):
                parts = line.split(":", 1)[1].split(",")
                return {
                    item.strip().split()[1].strip("()"):
                    item.strip().split()[0]
                    for item in parts
                }

        return {}

# Install UFW
apt.packages(
    name="Install UFW",
    packages=["ufw"],
)

# Configure default policies
server.shell(
    name="Configure UFW defaults",
    commands=[
        "ufw default deny incoming",
        "ufw default allow outgoing",
    ],
    _sudo=True,
    _if=lambda: (
        (defaults := host.get_fact(UfwDefaults)).get("incoming") != "deny"
        or defaults.get("outgoing") != "allow"
    )
)

if host.data.ufw.get("chromecast-dlna"):
    files.put(
        name="Configure chromecast dlna",
        src="files/ufw/chromecast-dlna",
        dest="/etc/ufw/applications.d/chromecast-dlna",
        user="root",
        group="root",
        mode="640"
    )

    if host.data.ufw.get("chromecast-dlna") == "Allow":
        server.shell(
            name="Allow chromecast dlna",
            commands=[
                "ufw allow cast",
            ],
            _sudo=True,
            _if=lambda: not ufw_rule_exists("cast"),
        )
    else:
        server.shell(
            name="Remove chromecast dlna rules",
            commands=[
                "ufw delete allow cast",
            ],
            _sudo=True,
            _if=lambda: ufw_rule_exists("cast"),
        )

if host.data.ufw.get("kdeconnect"):
    files.put(
        name="Configure kdeconnect",
        src="files/ufw/kdeconnect",
        dest="/etc/ufw/applications.d/kdeconnect",
        user="root",
        group="root",
        mode="640"
    )

    if host.data.ufw.get("kdeconnect") == "Allow":
        server.shell(
            name="Allow kdeconnect",
            commands=[
                "ufw allow kdeconnect",
            ],
            _sudo=True,
            _if=lambda: not ufw_rule_exists("kdeconnect"),
        )
    else:
        server.shell(
            name="Remove kdeconnect rules",
            commands=[
                "ufw delete allow kdeconnect",
            ],
            _sudo=True,
            _if=lambda: ufw_rule_exists("kdeconnect"),
        )

if host.data.ufw.get("localsend"):
    files.put(
        name="Configure localsend",
        src="files/ufw/localsend",
        dest="/etc/ufw/applications.d/localsend",
        user="root",
        group="root",
        mode="640"
    )

    if host.data.ufw.get("localsend") == "Allow":
        server.shell(
            name="Allow localsend",
            commands=[
                "ufw allow localsend",
            ],
            _sudo=True,
            _if=lambda: not ufw_rule_exists("localsend"),
        )
    else:
        server.shell(
            name="Remove localsend rules",
            commands=[
                "ufw delete allow localsend",
            ],
            _sudo=True,
            _if=lambda: ufw_rule_exists("localsend"),
        )

if host.data.ufw.get("ssh"):
    if host.data.ufw.get("ssh") == "Allow":
        # Allow SSH before enabling the firewall!
        server.shell(
            name="Allow SSH",
            commands=["ufw allow 22/tcp"],
            _sudo=True,
            _if=lambda: not ufw_rule_exists("22/tcp"),
        )
    else:
        server.shell(
            name="Deny SSH",
            commands=["ufw deny 22/tcp"],
            _sudo=True,
            _if=lambda: ufw_rule_exists("22/tcp"),
        )

# Enable firewall
server.shell(
    name="Enable UFW",
    commands=["ufw --force enable"],
    _sudo=True,
    _if=lambda: not host.get_fact(UfwActive),
)
