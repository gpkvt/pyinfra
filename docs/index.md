# pyinfra

**Linux infrastructure and workstation automation**

[pyinfra](https://pyinfra.com/) turns Python-based host configuration into repeatable infrastructure operations. This repository provides an opinionated, configuration-driven automation setup for Debian and Ubuntu servers and workstations.

<div class="grid cards" markdown>

-   :material-server-network: **Infrastructure**

    ---

    Configure Linux hosts, packages, repositories, networking, SSH, firewall rules and system services.

-   :material-docker: **Application services**

    ---

    Deploy Docker Compose applications with persistent host data, systemd integration and optional on-demand startup.

-   :material-monitor: **Workstations**

    ---

    Manage desktop applications, COSMIC settings, Flatpak, power management, hardware utilities and user environments.

-   :material-shield-lock: **Secrets**

    ---

    Keep credentials out of tracked configuration with GPG-encrypted JSON and the `gpg-vault` workflows.

</div>

## What is included?

| Area | Examples |
| --- | --- |
| Base system | APT packages and repositories, hostname, timezone, locale, sysctl and udev |
| Access and security | SSH, sudoers, AppArmor, USBGuard and UFW |
| Networking | WireGuard configuration and conditional VPN activation |
| Services | Docker Compose applications, Caddy, Dehydrated, Syncthing and Samba |
| Desktop | COSMIC settings, Flatpak applications, fonts and VSCodium extensions |
| Maintenance | Backup tools, firmware utilities, storage health and power management |
| User environment | Zsh, tmux, Powerline, Git and dotfiles |

Features are selected through host and role configuration. Optional workstation features are disabled in the tracked example until explicitly enabled.

## Getting started

1. Clone the repository.
2. Create local host configuration from the tracked examples.
3. Review the inventory and every enabled feature.
4. Preview the deployment before applying it.

```bash
git clone https://github.com/gpkvt/pyinfra.git
cd pyinfra

cp group_data/@local.py.example group_data/@local.py
cp group_data/workstation.py.example group_data/workstation.py

uv sync
source .venv/bin/activate

# Review planned changes first.
pyinfra inventory.py deploy.py --dry --diff

# Apply only after reviewing the plan.
pyinfra inventory.py deploy.py --diff
```

**Important:** Do not deploy the example configuration unchanged. It contains machine-specific placeholders and features that require deliberate review. A deployment can install packages, modify system files and networking, enable services, and change firewall or USB authorization policies. Start with a dry run and a non-production target.

See [Requirements and configuration](configuration.md) and the [deployment workflow](deployment.md) before running a deployment.

## How it is structured

- `inventory.py` defines target hosts and connection settings.
- `group_data/` contains host-specific and shared role configuration.
- `deploy.py` initializes shared values and selects task modules.
- `tasks/` contains reusable pyinfra task implementations.
- `templates/` contains host-aware Jinja2 configuration templates.
- `files/` contains static scripts and configuration assets.
- `docs/` contains the detailed project documentation.

Read the [architecture overview](architecture.md) for the execution model.

## Documentation

- [Architecture](architecture.md) — repository layers and execution lifecycle.
- [Host configuration](configuration.md) — host data, role settings and feature flags.
- [Deployment workflow](deployment.md) — previewing, targeting and applying changes.
- [Task reference](tasks.md) — task modules and managed services.
- [Secrets management](secrets.md) — GPG-encrypted credentials and vault workflows.
- [System configuration](system.md) — Linux settings and security controls.
- [Templates and static assets](templates.md) — generated files and static payloads.
- [Development](development.md) — tests, checks and contribution workflow.
- [Contributing](../CONTRIBUTING.md) — how to report issues and propose changes.

## Requirements

- Python 3.12 or newer.
- pyinfra installed in an isolated Python environment.
- Debian- or Ubuntu-based Linux targets for the supplied task implementations.
- SSH access and sufficient privileges for remote targets.
- GPG when encrypted secrets are used.
- systemd on targets for tasks that manage system services.

Individual features can require additional tools such as Docker, Flatpak, UFW, AppArmor, USBGuard or WireGuard. Check the relevant documentation before enabling them.

## Safety and idempotency

The tasks are designed to be safe to run repeatedly and to avoid reporting changes when the target already matches the desired state. The repository includes pytest regression tests, pre-commit checks and a CI deployment-idempotency check.

Run the checks during development:

```bash
pre-commit run --all-files
python -m pytest tests/ -v
```

Review [operational and security notes](https://github.com/gpkvt/pyinfra#operational-and-security-notes) before using the configuration on real systems.

## Project links

- [Source code](https://github.com/gpkvt/pyinfra)
- [Issue tracker](https://github.com/gpkvt/pyinfra/issues)
- [Discussions and changes](https://github.com/gpkvt/pyinfra/pulls)
- [MIT License](https://github.com/gpkvt/pyinfra/blob/main/LICENSE)
