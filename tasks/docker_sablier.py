"""Install and run Sablier against the configured user's systemd manager."""

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

SABLIER_VERSION = "1.20.0"
options = host.data.get("docker_sablier", {})

if options.get("enabled", False):
    username = host.data.get("username", "root")
    usergroup = host.data.get("usergroup", "root")
    homedir = host.data.get("homedir", f"/home/{username}")
    binary = f"{homedir}/.local/bin/sablier"

    files.directory(
        name="Create Sablier binary directory",
        path=f"{homedir}/.local/bin",
        user=username,
        group=usergroup,
        mode="750",
    )
    files.directory(
        name="Create Sablier configuration directory",
        path=f"{homedir}/.config/sablier",
        user=username,
        group=usergroup,
        mode="750",
    )

    server.shell(
        name="Install Sablier binary",
        commands=[
            "set -euo pipefail",
            'arch="$(dpkg --print-architecture)"',
            'case "$arch" in amd64) sablier_arch=amd64 ;; arm64) sablier_arch=arm64 ;; *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; esac',
            'tmp="$(mktemp -d)"',
            "trap 'rm -rf \"$tmp\"' EXIT",
            f'curl -fsSL "https://github.com/sablierapp/sablier/releases/download/v{SABLIER_VERSION}/sablier-{SABLIER_VERSION}-linux-$sablier_arch.tar.gz" | tar -xz -C "$tmp" sablier',
            f'install -m 0755 "$tmp/sablier" "{binary}"',
            f'chown {username}:{usergroup} "{binary}"',
        ],
        _sudo=True,
        _if=lambda: host.get_fact(
            Command,
            f'if [ -x "{binary}" ] && "{binary}" version 2>&1 | grep -q "{SABLIER_VERSION}"; then echo ready; else echo missing; fi',
        ).strip() != "ready",
    )

    config = files.template(
        name="Configure Sablier systemd provider",
        src="templates/sablier/sablier.yaml.j2",
        dest=f"{homedir}/.config/sablier/sablier.yaml",
        user=username,
        group=usergroup,
        mode="640",
        default_duration=options.get("default_duration", "60m"),
    )
    unit = files.template(
        name="Deploy Sablier user systemd service",
        src="templates/sablier/sablier.service.j2",
        dest=f"{homedir}/.config/systemd/user/sablier.service",
        user=username,
        group=usergroup,
        mode="644",
        homedir=homedir,
    )

    server.shell(
        name="Enable lingering for Sablier user manager",
        commands=[f"loginctl enable-linger {username}"],
        _sudo=True,
        _if=lambda: host.get_fact(
            Command, f"loginctl show-user {username} -p Linger"
        ).strip() != "Linger=yes",
    )

    server.shell(
        name="Enable and start Sablier",
        commands=[
            "systemctl --user daemon-reload",
            "systemctl --user enable sablier.service",
            "if systemctl --user is-active --quiet sablier.service; then "
            "systemctl --user restart sablier.service; "
            "else systemctl --user start sablier.service; fi",
        ],
        _sudo=False,
        _if=lambda: (
            config.did_change
            or unit.did_change
            or host.get_fact(
                Command,
                "systemctl --user is-active sablier.service 2>/dev/null || true",
            ).strip() != "active"
        ),
    )
