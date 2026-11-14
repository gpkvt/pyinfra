"""Deploy an opt-in, on-demand Samba file drop."""
import ipaddress
import os
import shlex

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server

from common import command_output_text

config = host.data.get("samba", {})
if config.get("enabled", False):
    upload_path = config.get("upload", {}).get("path", "/srv/samba/upload")
    download_path = config.get("download", {}).get("path", "/srv/samba/download")
    networks = config.get("allowed_networks", [])
    idle_timeout = config.get("idle_timeout", 1800)
    interface = config.get("interface", "lo")

    if (
        not isinstance(idle_timeout, int)
        or isinstance(idle_timeout, bool)
        or idle_timeout < 0
    ):
        raise ValueError("samba.idle_timeout must be a non-negative integer")
    if not isinstance(interface, str) or not interface or not all(
        character.isalnum() or character in "_.:-" for character in interface
    ):
        raise ValueError("samba.interface must be a valid Linux interface name")
    for label, path in (("upload", upload_path), ("download", download_path)):
        if not isinstance(path, str) or not os.path.isabs(path):
            raise ValueError(f"samba.{label}.path must be an absolute path")
    if upload_path == download_path:
        raise ValueError("Samba upload and download paths must be different")
    if not isinstance(networks, list) or not networks:
        raise ValueError("samba.allowed_networks must contain at least one LAN/VPN CIDR")
    try:
        networks = [str(ipaddress.ip_network(value, strict=False)) for value in networks]
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid samba.allowed_networks entry: {error}") from error

    def needs_samba_apparmor_hook():
        return command_output_text(host.get_fact(
            Command,
            command=(
                "test -x /usr/share/samba/update-apparmor-samba-profile && "
                "grep -Fq 'include if exists <samba/smbd-shares>' "
                "/etc/apparmor.d/usr.sbin.smbd && "
                "! grep -Fq 'ExecStartPre=/usr/share/samba/"
                "update-apparmor-samba-profile' "
                "/usr/lib/systemd/system/smbd.service "
                "/lib/systemd/system/smbd.service "
                "/etc/systemd/system/smbd.service.d/*.conf "
                "2>/dev/null && echo yes || true"
            ),
        )).strip() == "yes"

    apt.packages(
        name="Install Samba server, client and idle-monitor dependencies",
        packages=["samba", "smbclient"] + (["nftables"] if idle_timeout else []),
        present=True, _sudo=True,
    )
    files.directory(
        name="Create Samba upload directory", path=upload_path,
        user="root", group="nogroup", mode="1770", present=True, _sudo=True,
    )
    quoted_upload_path = shlex.quote(upload_path)

    def needs_upload_permission_migration():
        return command_output_text(host.get_fact(
            Command,
            command=(
                f"find {quoted_upload_path} -xdev "
                "\\( ! -user root -o ! -group nogroup "
                "-o \\( -type d ! -perm -1000 \\) \\) "
                "-print -quit | grep -q . && echo yes || true"
            ),
        )).strip() == "yes"

    server.shell(
        name="Protect existing Samba upload contents from deletion",
        commands=[
            f"chown -R root:nogroup -- {quoted_upload_path}",
            f"find {quoted_upload_path} -xdev -type d ! -perm -1000 "
            "-exec chmod +t {} +",
        ],
        _sudo=True,
        _if=needs_upload_permission_migration,
    )
    files.directory(
        name="Create Samba download directory", path=download_path,
        user="root", group="root", mode="0755", present=True, _sudo=True,
    )
    files.template(
        name="Configure on-demand Samba shares",
        src="templates/samba/smb.conf.j2", dest="/etc/samba/smb.conf",
        user="root", group="root", mode="0644",
        upload_path=upload_path, download_path=download_path,
        server_string=config.get("server_string", "On-demand file exchange"),
        workgroup=config.get("workgroup", "WORKGROUP"),
        interface=interface, _sudo=True,
    )
    files.directory(
        name="Create Samba AppArmor systemd drop-in directory",
        path="/etc/systemd/system/smbd.service.d",
        present=True, _sudo=True,
        _if=needs_samba_apparmor_hook,
    )
    files.template(
        name="Enable automatic Samba AppArmor share permissions",
        src="templates/samba/smbd-apparmor.conf.j2",
        dest="/etc/systemd/system/smbd.service.d/apparmor.conf",
        user="root", group="root", mode="0644",
        _sudo=True, _if=needs_samba_apparmor_hook,
    )
    files.template(
        name="Configure Samba firewall networks",
        src="templates/samba/allowed-networks.j2",
        dest="/etc/samba/allowed-networks",
        user="root", group="root", mode="0600",
        networks=networks, _sudo=True,
    )
    files.template(
        name="Configure Samba idle traffic counter",
        src="templates/samba/idle-nftables.j2",
        dest="/etc/samba/idle-nftables.conf",
        user="root", group="root", mode="0600",
        networks=networks, interface=interface, _sudo=True,
    )
    files.template(
        name="Install Samba idle checker",
        src="templates/samba/samba-idle-check.j2",
        dest="/usr/local/sbin/samba-idle-check",
        user="root", group="root", mode="0750",
        idle_timeout=idle_timeout, _sudo=True,
    )
    for unit in ("samba-idle.service", "samba-idle.timer"):
        files.template(
            name=f"Install {unit}",
            src=f"templates/samba/{unit}.j2",
            dest=f"/etc/systemd/system/{unit}",
            user="root", group="root", mode="0644", _sudo=True,
        )
    for script in ("samba-start", "samba-stop"):
        files.template(
            name=f"Install {script} command",
            src=f"templates/samba/{script}.j2",
            dest=f"/usr/local/sbin/{script}",
            user="root", group="root", mode="0750",
            idle_timeout=idle_timeout, _sudo=True,
        )

    def needs_systemd_reload():
        """Return true only when a managed systemd unit needs reloading."""
        return command_output_text(host.get_fact(
            Command,
            command=(
                "for unit in smbd.service samba-idle.service samba-idle.timer; do "
                'if systemctl show "$unit" --property=NeedDaemonReload --value '
                "2>/dev/null | grep -qx yes; then echo yes; break; fi; done"
            ),
        )).strip() == "yes"

    server.shell(
        name="Reload systemd unit definitions when needed",
        commands=["systemctl daemon-reload"], _sudo=True,
        _if=needs_systemd_reload,
    )
    server.shell(
        name="Keep Samba stopped until requested",
        commands=[
            "systemctl stop samba-idle.timer 2>/dev/null || true",
            "nft delete table inet samba_idle 2>/dev/null || true",
            "rm -f /run/samba-idle.state",
            "systemctl stop smbd.service",
            "systemctl mask smbd.service",
        ],
        _sudo=True,
        _if=lambda: (
            command_output_text(host.get_fact(
                Command,
                command="test -e /run/samba-started && echo yes || true",
            )).strip() != "yes"
            and (
                command_output_text(host.get_fact(
                    Command,
                    command="systemctl is-active smbd.service 2>/dev/null || true",
                )).strip() == "active"
                or command_output_text(host.get_fact(
                    Command,
                    command="systemctl is-enabled smbd.service 2>/dev/null || true",
                )).strip() != "masked"
                or command_output_text(host.get_fact(
                    Command,
                    command="systemctl is-active samba-idle.timer 2>/dev/null || true",
                )).strip() == "active"
                or bool(command_output_text(host.get_fact(
                    Command,
                    command="nft list table inet samba_idle 2>/dev/null || true",
                )).strip())
                or command_output_text(host.get_fact(
                    Command,
                    command="test -e /run/samba-idle.state && echo present || true",
                )).strip() == "present"
            )
        ),
    )
