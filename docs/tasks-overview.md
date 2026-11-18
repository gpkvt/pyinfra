# Task overview

The deployment is composed of reusable Python modules under `tasks/`. The deploy entry point selects baseline tasks and optional features using inventory, host data and group data.

## Task areas

| Area | Examples | Further information |
| --- | --- | --- |
| System foundations | APT, users, sudo, hostname, locale, sysctl, udev, SSH keys, Git and fonts | [Core task reference](tasks/#core-tasks) |
| Docker applications | Compose services, directories, bind-mounted data, systemd units and integrations | [Docker guide](docker/) |
| Network and services | WireGuard, VPN, Syncthing, Samba, UFW, Caddy, Dehydrated and AppArmor | [Optional task reference](tasks/#optional-tasks) |
| Workstation | COSMIC settings, Flatpak, backups, power, firmware, storage, peripherals and developer tools | [Workstation features](feature-reference/#workstation-role-features) |

The [complete feature reference](feature-reference/) indexes the Python modules under `tasks/`, describes their inclusion conditions and documents relevant configuration.

## Docker conventions

Docker tasks are enabled through the `docker` host-data mapping. The shared Docker tasks configure the runtime and dispatch the service modules selected for the target.

- Compose files and persistent application data are stored under `~/.docker/<service>/`.
- Persistent storage uses host bind mounts; Docker-managed named volumes are not used.
- Web interfaces bind to loopback by default where applicable.
- systemd user units manage Compose project lifecycle.
- Sablier on-demand startup and the battery monitor are mutually exclusive options.

See the [Docker guide](docker/) for the service catalog, ports, data paths, secrets and operational behavior.

## Selecting and running tasks

Optional task inclusion is controlled by `deploy.py` and host or group data. Start with the [configuration guide](configuration/), check the [feature reference](feature-reference/) and preview the deployment before applying it:

```bash
pyinfra inventory.py deploy.py --dry --diff
```

The preview should be reviewed for the intended hosts and operations. Apply only after checking the proposed changes and confirming that backups and access recovery are available where needed.
