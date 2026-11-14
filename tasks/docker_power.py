"""
Deploy and configure the Docker battery monitor.

The battery saver and Sablier are mutually exclusive.
"""

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server, systemd

battery_container = host.data.get("docker_power_save", {})
sablier_enabled = host.data.get("docker_sablier", {}).get("enabled", False)

for script in ("docker-power-manager", "docker-power-monitor"):
    files.put(
        name=f"Deploy {script}",
        src=f"files/docker-battery-saver/{script}",
        dest=f"/usr/local/sbin/{script}",
        mode="750",
        user="root",
        group="root",
        _sudo=True,
    )

files.directory(
    name="Create config directory",
    path="/etc/docker/",
    mode="755",
    user="root",
    group="root",
    _sudo=True,
)

files.template(
    name="Deploy docker-power-monitor configuration",
    src="templates/docker/battery-containers.conf.j2",
    dest="/etc/docker/battery-containers.conf",
    user="root",
    group="root",
    mode="640",
    containers=battery_container,
    _sudo=True,
)

monitor_unit = files.put(
    name="Deploy docker-power-monitor systemd unit",
    src="files/docker-battery-saver/docker-power-monitor.service",
    dest="/etc/systemd/system/docker-power-monitor.service",
    mode="644",
    user="root",
    group="root",
    _sudo=True,
)

server.shell(
    name="Reload systemd after Docker power monitor unit changes",
    commands=["systemctl daemon-reload"],
    _sudo=True,
    _if=monitor_unit.did_change,
)

if sablier_enabled:
    server.shell(
        name="Restore containers previously stopped by the battery saver",
        commands=["/usr/local/sbin/docker-power-manager ac"],
        _sudo=True,
        _if=lambda: host.get_fact(
            Command,
            "test -f /var/lib/docker-power-manager/running-containers && echo present || echo absent",
        ).strip() == "present",
    )
    systemd.service(
        name="Disable Docker battery monitor while Sablier is enabled",
        service="docker-power-monitor.service",
        running=False,
        enabled=False,
        _sudo=True,
    )
else:
    systemd.service(
        name="Enable Docker battery monitor when Sablier is disabled",
        service="docker-power-monitor.service",
        running=True,
        enabled=True,
        _sudo=True,
    )
