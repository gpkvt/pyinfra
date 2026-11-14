"""Deploy an opt-in, on-demand Samba file drop."""
import ipaddress
import os

from pyinfra import host
from pyinfra.operations import apt, files, server

config = host.data.get("samba", {})
if config.get("enabled", False):
    upload_path = config.get("upload", {}).get("path", "/srv/samba/upload")
    download_path = config.get("download", {}).get("path", "/srv/samba/download")
    networks = config.get("allowed_networks", [])

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

    apt.packages(name="Install Samba server", packages=["samba"], present=True, _sudo=True)
    files.directory(
        name="Create Samba upload directory", path=upload_path,
        user="nobody", group="nogroup", mode="0770", present=True, _sudo=True,
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
        interface=config.get("interface", "lo"), _sudo=True,
    )
    files.template(
        name="Configure Samba firewall networks",
        src="templates/samba/allowed-networks.j2",
        dest="/etc/samba/allowed-networks",
        user="root", group="root", mode="0600",
        networks=networks, _sudo=True,
    )
    for script in ("samba-start", "samba-stop"):
        files.template(
            name=f"Install {script} command",
            src=f"templates/samba/{script}.j2",
            dest=f"/usr/local/sbin/{script}",
            user="root", group="root", mode="0750", _sudo=True,
        )

    server.shell(
        name="Keep Samba stopped until requested",
        commands=["systemctl stop smbd.service", "systemctl mask smbd.service"],
        _sudo=True,
        _if=lambda: (
            host.get_fact("command", command="systemctl is-active smbd.service 2>/dev/null || true").strip() == "active"
            or host.get_fact("command", command="systemctl is-enabled smbd.service 2>/dev/null || true").strip() != "masked"
        ),
    )
