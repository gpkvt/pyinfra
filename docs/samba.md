# On-demand Samba file exchange

The optional Samba task provides two guest-accessible SMB shares for quick LAN/VPN file exchange:

- **Upload** is a shared, writable dropbox. Guests can upload, replace and remove files. All guest connections use the same Unix identity (nobody), so this is not a private per-device inbox and users are not isolated from one another. Do not use it for confidential uploads.
- **Download** is guest-readable and read-only. Publish files by copying them into the configured download directory on the server.

The task installs both the Samba server and `smbclient`, which provides a command-line client for testing guest share access directly from the server (for example, `smbclient -N //127.0.0.1/Upload -c 'ls'`). The service is deliberately **not enabled at boot**. The deployment installs and configures Samba, stops it and masks smbd.service. It does not start Samba or open the firewall. Run the deployed scripts when file exchange is needed:

    sudo samba-start
    # Connect from a client to \\server-address\Upload or \\server-address\Download
    sudo samba-stop

The scripts are safe to repeat. Start adds only missing UFW allow rules for the configured CIDRs, unmasks and starts smbd. Stop stops and masks smbd, then removes only matching rules found in UFW's added-rule list. TCP 445 is the only SMB port used; NetBIOS is disabled. The scripts manage UFW rules and therefore require UFW to be installed and active/configured on the host. If UFW is not the host firewall, adapt the scripts before use.

## Configuration

Set a top-level samba mapping in host data:

    samba = {
        "enabled": True,
        "interface": "enp3s0",
        "allowed_networks": ["192.168.1.0/24", "10.20.0.0/24"],
        "idle_timeout": 3600,  # 0 disables automatic shutdown
        "workgroup": "WORKGROUP",
        "server_string": "On-demand file exchange",
        "upload": {"path": "/srv/samba/upload"},
        "download": {"path": "/srv/samba/download"},
    }

| Key | Default | Description |
| --- | --- | --- |
| enabled | False | Opts into installation and configuration. |
| interface | lo | Interface name Samba binds to, in addition to loopback. |
| allowed_networks | required | Non-empty list of IPv4/IPv6 CIDRs allowed through UFW on TCP 445. |
| idle_timeout | 1800 | Stop Samba after this many seconds without incoming SMB packets from allowed networks; any non-negative integer is accepted, and 0 disables automatic shutdown. Checks run every 60 seconds. |
| workgroup | WORKGROUP | SMB workgroup. |
| server_string | On-demand file exchange | Server description. |
| upload.path | /srv/samba/upload | Persistent upload directory. |
| download.path | /srv/samba/download | Persistent download directory. |

Both paths must be distinct absolute paths. The task creates them if absent and never deletes their contents. Upload files are owned by the guest Unix identity; download files are not modified by Samba. Place files in the download directory using normal server-side tools and ensure they are world-readable.

When `idle_timeout` is greater than zero, `samba-start` installs a dedicated nftables counter and starts a systemd timer. The counter observes incoming TCP 445 packets on the configured interface from allowed CIDRs; unrelated interface traffic does not reset the timeout. The monitor checks every 60 seconds and stops Samba through `samba-stop` after the configured idle period. The default idle period is 30 minutes; any positive timeout is accepted. The monitor and its counter are removed when Samba is stopped manually or automatically. The idle monitor requires nftables (`nft`) and systemd.

The scripts are installed as /usr/local/sbin/samba-start and /usr/local/sbin/samba-stop. If /usr/local/sbin is not in the invoking user's PATH, call them by absolute path.

## Security

This is intended only for a trusted LAN or VPN. Guest upload is intentionally frictionless, but all guests share one Unix identity and can manage files in the Upload share. Anyone with network access to TCP 445 can read the Download share and upload to Upload. Restrict allowed_networks to trusted CIDRs, do not forward TCP 445 from the internet, and stop the service when it is not needed. The firewall rules are temporary operational state: deployment does not open them, and samba-stop removes the matching rules.

The task does not create Samba user accounts, perform automatic cleanup, or automatically start the service after reboot.
