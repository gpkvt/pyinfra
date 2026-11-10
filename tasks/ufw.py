# pylint: disable=C0301, E0401, C0115, C0116, W0621

"""
Install, configure, and manage the UFW firewall using pyinfra.

This module installs UFW, configures default firewall policies,
manages application-specific firewall profiles and port-based
rules, and ensures the firewall is enabled.

Firewall rules are configured generically based on host.data.ufw.
Supported applications and services are mapped to their respective
UFW application profiles or network ports.

Configuration:

    host.data.ufw (dict):
        Defines which applications and services are allowed or
        denied by the firewall.

        Supported applications:
            chromecast-dlna (str): Chromecast/DLNA traffic.
            kdeconnect (str): KDE Connect traffic.
            localsend (str): LocalSend traffic.

        Supported services:
            ssh (str): SSH access on TCP port 22.

        Values:
            "Allow": Create an allow rule.
            "Deny": Create an explicit deny rule.

        Example:
            ufw = {
                "kdeconnect": "Allow",
                "localsend": "Allow",
                "chromecast-dlna": "Deny",
                "ssh": "Allow",
            }

Facts:

    UfwActive:
        Checks whether UFW is currently active using
        `ufw status`.

        Returns:
            bool: True if the firewall is active, otherwise False.

    UfwRules:
        Retrieves the currently configured UFW rules using
        `sudo ufw status` and filters out status and header lines.

        Returns:
            set[str]: Existing firewall rules.

    UfwDefaults:
        Retrieves the default incoming and outgoing firewall
        policies using `sudo ufw status verbose`.

        Returns:
            dict: Default firewall policies, such as incoming and
            outgoing actions.

Helper functions:

    ufw_rule_exists(rule, action="ALLOW", scope="Anywhere"):
        Checks whether a firewall rule matching the specified
        rule, action, and scope exists.

        Returns:
            bool: True if a matching rule exists, otherwise False.

Operations:

    1. Install UFW:
       - Install UFW using APT.

    2. Configure default firewall policies:
       - Deny incoming connections.
       - Allow outgoing connections.
       - Apply changes only when the current policies differ.

    3. Configure application profiles and port-based rules:
       - Iterate over the entries in host.data.ufw.
       - Ignore unsupported configuration keys and invalid values.
       - Deploy application profiles for configured applications.
       - Configure allow or deny rules according to the specified
         action.
       - Support both UFW application profiles and explicit
         network port definitions.
       - Check existing rules before applying changes to avoid
         unnecessary operations.

    4. Enable firewall:
       - Enable UFW when it is not already active.
       - Configure all application and port-based rules before
         activating the firewall to prevent accidental loss of
         remote access.

Application profiles:

    Chromecast/DLNA:
        Profile: /etc/ufw/applications.d/chromecast-dlna
        UFW name: cast

    KDE Connect:
        Profile: /etc/ufw/applications.d/kdeconnect
        UFW name: kdeconnect

    LocalSend:
        Profile: /etc/ufw/applications.d/localsend
        UFW name: localsend

Port-based rules:

    SSH:
        Protocol: TCP
        Port: 22

File permissions:

    Application profiles:
        Owner: root
        Group: root
        Mode: 0640

Notes:

    - Firewall configuration commands require sudo.
    - Application profiles are deployed only when their
      corresponding configuration keys are present.
    - Port-based rules do not require application profiles.
    - Only explicitly supported applications and services are
      configured.
    - Unsupported configuration keys and values are ignored.
    - Existing rules are checked before adding new rules to avoid
      unnecessary changes.
    - Allow and deny rules are managed independently.
    - Default incoming traffic is denied and outgoing traffic
      is allowed.
    - All configured rules are applied before firewall activation.
    - UFW is enabled non-interactively using `--force`.
"""

from pyinfra.operations import apt, server, files
from pyinfra import host
from pyinfra.api import FactBase

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

class UfwActive(FactBase):
    command = "ufw statusAllow"

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

# Configure application profiles and port rules
ufw = host.data.get("ufw", {})

ufw_applications = {
    "chromecast-dlna": "cast",
    "kdeconnect": "kdeconnect",
    "localsend": "localsend",
}

ufw_ports = {
    "ssh": "22/tcp",
}

for app, action in ufw.items():
    if action not in ("Allow", "Deny"):
        continue

    if app in ufw_applications:
        application = ufw_applications[app]

        # Deploy application profile
        files.put(
            name=f"Configure {app}",
            src=f"files/ufw/{app}",
            dest=f"/etc/ufw/applications.d/{app}",
            user="root",
            group="root",
            mode="640",
            _sudo=True,
        )

        rule = application

    elif app in ufw_ports:
        rule = ufw_ports[app]

    else:
        continue

    if action == "Allow":
        server.shell(
            name=f"Allow {app}",
            commands=[f"ufw allow {rule}"],
            _sudo=True,
            _if=lambda rule=rule: not ufw_rule_exists(rule),
        )

    else:
        server.shell(
            name=f"Deny {app}",
            commands=[f"ufw deny {rule}"],
            _sudo=True,
            _if=lambda rule=rule: not ufw_rule_exists(
                rule, action="DENY"
            ),
        )

# Enable firewall
server.shell(
    name="Enable UFW",
    commands=["ufw --force enable"],
    _sudo=True,
    _if=lambda: not host.get_fact(UfwActive),
)
