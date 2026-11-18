# gpkvt/pyinfra

This repository contains a pyinfra deployment configuration for Debian and Ubuntu systems. It includes inventory, host and group data, deployment entry points, reusable task modules, templates, files and scripts.

It uses the separate [upstream pyinfra automation tool](https://github.com/pyinfra-dev/pyinfra) to execute operations on local and remote machines. This repository is deployment code; it is not the upstream pyinfra engine.

## Repository contents

| Area | What it manages | Documentation |
| --- | --- | --- |
| System | Packages, users, SSH, host configuration, storage and services | [Task reference](tasks/) |
| Docker | Compose applications, persistent data, systemd user services and integrations | [Docker guide](docker/) |
| Network | VPN, Samba, Syncthing, firewall and proxy-related services | [Task overview](tasks-overview/) |
| Workstation | COSMIC, Flatpak, power management, hardware and desktop tools | [Feature reference](feature-reference/#workstation-role-features) |
| Configuration | Inventory, host/group data, feature flags and encrypted credentials | [Configuration](configuration/) |

Optional features are selected through deployment code and host or group data. They are not all enabled on every target.

## Requirements

- Python 3.12 or newer for the project environment.
- Debian or Ubuntu target systems, as configured by this repository.
- SSH access and suitable privileges for remote deployments.
- Docker Engine and the Compose plugin for Docker tasks.

See [development](development/) for the project environment and [configuration](configuration/) for inventory and host data.

## Deployment

Install the Python environment, review the inventory and host data, then preview the deployment:

```bash
uv sync
pyinfra inventory.py deploy.py --dry --diff
```

Review the proposed operations before applying them:

```bash
pyinfra inventory.py deploy.py --diff
```

A dry run is a review step, not a substitute for backups or testing. Some tasks modify networking, firewall rules, authentication or running services and can interrupt access.

## Docker storage and lifecycle

Docker tasks are opt-in through the `docker` host-data configuration. The repository uses these conventions:

- Compose project files and persistent application data are stored below `~/.docker/<service>/` for the configured user.
- Persistent application data uses host bind mounts. Docker-managed named volumes are not used.
- Web interfaces bind to loopback by default where applicable.
- systemd user units manage Compose project lifecycle.
- Credentials are read from the configured encrypted secrets source where supported.

The Docker guide documents the service catalog, ports, storage paths, prerequisites and service-specific settings.

## Upstream pyinfra

[Upstream pyinfra](https://pyinfra.com/) is maintained separately at [pyinfra-dev/pyinfra](https://github.com/pyinfra-dev/pyinfra). It provides the automation engine, inventory handling, facts, operations and connectors used by this repository.

See [Upstream pyinfra](upstream/) for the relationship between the engine and this deployment repository, and links to the upstream documentation.

## Reference

- [Task overview](tasks-overview/) — task families and optional feature selection.
- [Complete feature reference](feature-reference/) — task modules, feature gates and limitations.
- [Docker services](docker/) — supported applications and their configuration.
- [Configuration](configuration/) — inventory and host/group settings.
- [Deployment](deployment/) — previewing and applying changes.
- [Secrets](secrets/) — encrypted credentials.
- [Architecture](architecture/) — repository structure and execution flow.
- [Changelog](changelog/) — project changes.
