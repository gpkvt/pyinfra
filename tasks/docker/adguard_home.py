# pylint: disable=E0401
"""
Deploy AdGuard Home as a Docker container.

Configuration:
    docker.adguard_home (dict):
        image (str): AdGuard Home image. Defaults to adguard/adguardhome:v0.107.80.
    web_port (int): Top-level @local.py setting for the loopback-only web UI port.
        Defaults to 3000.

Persistent data:
    ~/.docker/adguard_home/conf/
    ~/.docker/adguard_home/work/

The container uses host networking so DNS can listen directly on port 53.
The web UI is reconciled to 127.0.0.1:<web_port> after initial setup.
Restrict DNS access with the host firewall.
"""

import shlex

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from common import command_output_text
from tasks.docker import deploy_docker_service


# Keep this script dependency-free: the target only needs Python's standard
# library. It edits only the direct "http.address" key and preserves all other
# AdGuard settings. A missing config file is expected during first-run setup.
_ADGUARD_CONFIG_SCRIPT = """
import re
import sys
from pathlib import Path

config = Path(sys.argv[1])
address = sys.argv[2]
mode = sys.argv[3]

if not config.is_file():
    print("missing")
    raise SystemExit(0)

original = config.read_text(encoding="utf-8")
lines = original.splitlines(keepends=True)
http_index = next(
    (
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r"http:\\s*(?:#.*)?(?:\\r?\\n)?", line)
    ),
    None,
)

if http_index is None:
    separator = "" if not original or original.endswith("\\n") else "\\n"
    updated = original + separator + f"http:\\n  address: {address}\\n"
else:
    section_end = len(lines)
    for index in range(http_index + 1, len(lines)):
        line = lines[index]
        if line.strip() and not line[0].isspace() and not line.lstrip().startswith("#"):
            section_end = index
            break

    address_index = next(
        (
            index
            for index in range(http_index + 1, section_end)
            if re.match(r"^  address\\s*:", lines[index])
        ),
        None,
    )
    if address_index is None:
        lines.insert(http_index + 1, f"  address: {address}\\n")
    else:
        line = lines[address_index]
        newline = "\\r\\n" if line.endswith("\\r\\n") else "\\n" if line.endswith("\\n") else ""
        lines[address_index] = f"  address: {address}{newline}"
    updated = "".join(lines)

if updated == original:
    print("unchanged")
elif mode == "check":
    print("change")
else:
    config.write_text(updated, encoding="utf-8")
    print("changed")
"""


adguard_home = host.data.get("docker", {}).get("adguard_home", {})
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
web_port = host.data.get("web_port", 3000)
if isinstance(web_port, bool) or not isinstance(web_port, int) or not 1 <= web_port <= 65535:
    raise ValueError("web_port must be an integer between 1 and 65535")

config_path = f"{homedir}/.docker/adguard_home/conf/AdGuardHome.yaml"  # pylint: disable=undefined-variable
web_address = f"127.0.0.1:{web_port}"
script = shlex.quote(_ADGUARD_CONFIG_SCRIPT)
quoted_path = shlex.quote(config_path)
quoted_address = shlex.quote(web_address)
check_command = (
    f"python3 -c {script} {quoted_path} {quoted_address} check"
)
apply_command = (
    f"python3 -c {script} {quoted_path} {quoted_address} apply"
)

for directory in ("conf", "work"):
    files.directory(
        name=f"Create AdGuard Home {directory} directory",
        path=f"{homedir}/.docker/adguard_home/{directory}/",  # pylint: disable=undefined-variable
        user=username,
        group=usergroup,
        mode="750",
    )

# Schedule the config edit before the service deployment so its change result
# can trigger a restart. The fact check skips missing files and already-correct
# addresses, avoiding false change reports on first setup and repeat runs.
adguard_uid = command_output_text(
    host.get_fact(Command, f"id -u {shlex.quote(username)}")
).strip()
if not adguard_uid.isdigit():
    raise RuntimeError(f"Unable to determine UID for AdGuard user {username!r}")
systemctl_user = (
    f"runuser -u {shlex.quote(username)} -- env "
    f"XDG_RUNTIME_DIR=/run/user/{adguard_uid} "
    f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{adguard_uid}/bus "
    "systemctl --user"
)

web_config = server.shell(
    name="Configure AdGuard Home web UI listen address",
    commands=[
        f"{systemctl_user} stop adguard_home",
        apply_command,
    ],
    _sudo=True,
    _if=lambda: command_output_text(
        host.get_fact(Command, check_command, _sudo=True)
    ).strip() == "change",
)

deploy_docker_service(
    service="adguard_home",
    description="AdGuard Home DNS",
    homedir=homedir,  # pylint: disable=undefined-variable
    compose_services=["adguard-home"],
    username=username,
    usergroup=usergroup,
    image=adguard_home.get("image", "adguard/adguardhome:v0.107.80"),
    restart_if=web_config,
)
