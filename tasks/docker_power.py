"""
Deploy and configure docker-power-monitor and docker-power-manager
"""

from pyinfra import host
from pyinfra.operations import files, server

battery_container = host.data.get("docker_power_save", {})
scripts = [
    "docker-power-manager",
    "docker-power-monitor"
]

for script in scripts:
    files.put(
        name="Deploy {file}",
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
)

systemd_result = files.put(
    name="Create systemd service",
    src="files/docker-battery-saver/docker-power-monitor.service",
    dest="/etc/systemd/system/docker-power-monitor.service",
    mode="644",
    user="root",
    group="root",
    _sudo=True,
)

if systemd_result.changed:
    server.shell(
        name="Enable and restart power manager",
        commands=[
            "systemctl daemon-reload",
            "systemctl enable docker-power-manager",
            "systemctl restart docker-power-manager",
        ],
        _sudo=True,
    )
