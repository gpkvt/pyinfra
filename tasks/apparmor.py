
"""
AppArmor hardening for Pop!_OS 24.04 LTS.

Installs AppArmor utilities, enables the service, enforces
configured profiles and reloads policies only when enforcement
changes are required.
"""

import json
from pyinfra import host
from pyinfra.api import FactBase, QuoteString, StringCommand, operation
from pyinfra.operations import apt, server
from pyinfra.operations.util import any_changed

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

APPARMOR_PROFILES = host.data.get("apparmor_profiles", [])

class AppArmorStatus(FactBase):
    command = "sudo aa-status --json"

    def process(self, output):
        data = json.loads("\n".join(output))
        return data.get("profiles", {})

@operation()
def enforce_apparmor_profile(profile_path, profile_names):
    profiles = host.get_fact(AppArmorStatus)

    if all(
        profiles.get(name) == "enforce"
        for name in profile_names
    ):
        return

    yield StringCommand(
        "aa-enforce",
        QuoteString(profile_path),
        _sudo=True,
    )

apt.packages(
    name="Install AppArmor",
    packages=[
        "apparmor",
        "apparmor-utils",
        "apparmor-profiles",
    ],
    _sudo=True,
)

server.service(
    name="Enable AppArmor",
    service="apparmor",
    running=True,
    enabled=True,
    _sudo=True,
)

# Schedule enforcement operations.
profile_operations = []

for profile in APPARMOR_PROFILES:
    path = profile["path"]
    names = profile["names"]

    profile_operations.append(
        enforce_apparmor_profile(
            name=f"Enforce AppArmor profiles: {', '.join(names)}",
            profile_path=path,
            profile_names=names,
            _sudo=True,
        )
    )

# Reload only if at least one enforcement operation changed something.
if profile_operations:
    server.shell(
        name="Reload AppArmor profiles",
        commands=[
            "systemctl reload apparmor",
        ],
        _if=any_changed(*profile_operations),
        _sudo=True,
    )
