# pyinfra — Linux infrastructure and workstation automation

[![CI](https://img.shields.io/github/actions/workflow/status/gpkvt/pyinfra/idempotency.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/gpkvt/pyinfra/actions/workflows/idempotency.yml)
[![License: MIT](https://img.shields.io/github/license/gpkvt/pyinfra?label=license)](LICENSE)
[![Open issues](https://img.shields.io/github/issues/gpkvt/pyinfra?logo=github)](https://github.com/gpkvt/pyinfra/issues)
[![Last commit](https://img.shields.io/github/last-commit/gpkvt/pyinfra?logo=git)](https://github.com/gpkvt/pyinfra/commits/main)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![Platforms: Debian and Ubuntu](https://img.shields.io/badge/platforms-Debian%20%7C%20Ubuntu-A81D33?logo=linux&logoColor=white)

A configuration-driven automation repository built on [pyinfra](https://pyinfra.com). It provisions Linux hosts from a shared set of reusable tasks while keeping inventory, host-specific settings, deployment logic, templates, static files, and secrets separate.

The repository is primarily designed around Debian/Ubuntu systems and includes both server infrastructure and desktop/workstation configuration. It is an opinionated starting point. Machine-specific host and workstation data is excluded from Git; tracked `.example` templates provide safe starting points.

> **Caution:** A deployment can install or upgrade packages, change system files and networking, enable services, and modify firewall or USB authorization policies. Start with a dry run and a non-production target. Do not deploy the example configuration unchanged.

## What it manages

| Area | Capabilities |
| --- | --- |
| Base system | APT repositories and packages, hostname, timezone, locale, keyboard, editors, sysctl and udev |
| Access and security | SSH keys and client configuration, sudoers rules, AppArmor profiles, USBGuard, UFW |
| Networking | WireGuard configuration and conditional VPN activation based on local-network detection |
| Services | Docker Compose applications including AppFlowy, Homepage, Linkwarden, Paperless-ngx, Firefly III with FinTS import, Snipe-IT and WG-Easy; Caddy and Sablier containers for on-demand startup, with Hetzner DNS-01 certificates managed by Dehydrated; Syncthing file synchronization; opt-in on-demand Samba upload/download shares |
| Desktop | Flatpak applications, COSMIC settings, fonts, VSCodium extensions, Proton applications, optional workstation desktop utilities |
| Workstation maintenance | Backup tools and Borgmatic config, power management, firmware/microcode tools, storage health utilities, optional printer/scanner support and maintenance tools |
| User environment | Zsh, tmux, Powerline, Git, Midnight Commander, scripts and dotfiles |
| Secrets | GPG-encrypted JSON for private keys, API tokens and application credentials; command-line and VS Code vault workflows |

Optional features are included by `deploy.py` only when their configuration and prerequisites are present. See [Task reference](docs/tasks.md) and [Deployment workflow](docs/deployment.md).

## How it works

1. `inventory.py` defines local and remote targets and their connection options.
2. Copy `group_data/@local.py.example` to `group_data/@local.py` and `group_data/workstation.py.example` to `group_data/workstation.py`; these local files are ignored by Git. Host data supplies machine-specific configuration, while inventory groups load shared role configuration.
3. `deploy.py` initializes shared values and selects task modules.
4. Modules in `tasks/` declare pyinfra operations.
5. `templates/` contains rendered Jinja2 configuration; `files/` contains static payloads.
6. `common.py` decrypts `secrets.json.gpg` when present and exposes the resulting dictionary to tasks.
7. `files/scripts/gpg-vault` provides an interactive command-line workflow for creating, editing, viewing, encrypting, decrypting and rekeying the secrets file.
8. `vscode/gpg-vault/` contains a VS Code extension for encrypting/decrypting files and selected text with the same GPG format.

See [Architecture](docs/architecture.md) for the execution flow and [Configuration](docs/configuration.md) for the settings model.

### Homepage dashboard

The optional Homepage Docker service provides a configurable dashboard for deployed applications, external links and status widgets. The AppFlowy integration is a normal link only; it does not poll AppFlowy's authenticated API. Homepage is managed by Sablier for on-demand startup; configured widget API paths bypass Sablier so dashboard widgets can retrieve data without waking their target services. Its configuration is rendered from `docker.homepage` host data, while static icons are maintained in `files/homepage/icons/` and synchronized to `~/.docker/homepage/public/icons/`. The supplied local configuration groups bookmarks into Misc, Social, Entertainment and Proton, and includes service widgets for selected applications plus FRITZ!Box, Miniflux, Forgejo, Portainer, OpenWeatherMap and Glances integrations. API credentials belong in the encrypted secrets file, not tracked host data. See the [Docker task reference](docs/tasks.md#docker-services) for storage, networking, icon synchronization and widget details.

## Requirements

- Python 3.12 or newer, as required by `pyproject.toml`.
- [pyinfra](https://pyinfra.com/) installed in an isolated Python environment.
- Debian- or Ubuntu-based target systems for the supplied task implementations.
- SSH access to remote hosts and sufficient privilege escalation for system-level operations. The local target also needs the required privileges.
- GPG on the machine executing the deployment when encrypted secrets are used.
- systemd on targets for tasks that manage system services.

Individual features may require additional software or capabilities, such as Docker, Flatpak, UFW, AppArmor, USBGuard, WireGuard, or a graphical COSMIC session. Their prerequisites are described in the relevant task documentation.

## Quick start

Before the first deployment, create and edit the ignored machine-specific configuration files:

```bash
cp group_data/@local.py.example group_data/@local.py
cp group_data/workstation.py.example group_data/workstation.py
```

Replace all placeholders and review the workstation feature flags before deploying. Never commit these local files.

### 1. Get the repository

```bash
git clone https://github.com/gpkvt/pyinfra.git
cd pyinfra
```

### 2. Create an isolated Python environment

```bash
uv sync
source .venv/bin/activate
```

### 3. Review the inventory

Edit `inventory.py`:

- Replace example hostnames and SSH settings.
- Keep only targets you intend to manage.
- Remove or update entries in `disabled_hosts` as appropriate.
- Confirm which user connects and whether `_sudo` is enabled.

The special `@local` target executes against the machine running pyinfra. It is not a remote host.

### 4. Create host configuration

Create or edit `group_data/<inventory-host>.py`. For the local target, first copy `group_data/@local.py.example` to the ignored `group_data/@local.py`; for workstation role settings, copy `group_data/workstation.py.example` to the ignored `group_data/workstation.py`.

At minimum, review the user identity and home directory, hostname, locale, timezone, package lists, network settings, and every optional service configuration. Inventory groups can apply shared role data: the `workstation = ["@local"]` group membership loads your local `group_data/workstation.py` for `@local`. The tracked examples are deliberately portable and disable workstation features until you opt in. See [Configuration](docs/configuration.md) for a categorized reference.

### 5. Prepare secrets (optional)

If you use features that require credentials, manage the encrypted file with `gpg-vault` (deployed from `files/scripts/` into the user's scripts directory and linked into `/usr/local/bin/` by `tasks/scripts.py`):

```bash
gpg-vault create
gpg-vault edit
gpg-vault view
gpg-vault status
```

The utility defaults to `secrets.json` / `secrets.json.gpg`; use `gpg-vault --file path/to/other.json COMMAND` for another file. It requires GPG and uses `$EDITOR` (default `nano`) for `create` and `edit`. `view` prints decrypted contents to the terminal. Keep the GPG passphrase available to the deployment operator. `common.py` still decrypts `secrets.json.gpg` directly during deployment; `gpg-vault` is a local management helper, not part of deployment-time secret loading. Without `secrets.json.gpg`, the deployment initializes an empty secrets dictionary; secret-dependent tasks are not included. See [Secrets management](docs/secrets.md).

### 6. Preview, then deploy

From the repository root:

```bash
# Preview planned operations without applying them
pyinfra inventory.py deploy.py --dry --diff

# Apply after reviewing the preview
pyinfra inventory.py deploy.py --diff
```

To target only the local inventory host:

```bash
pyinfra inventory.py deploy.py --limit @local --dry --diff
```

Check the CLI options supported by your installed pyinfra version with `pyinfra --help`. Do not assume a dry run replaces backups or change-control procedures.

## Repository layout

```text
.
├── inventory.py             # Target hosts and connection options
├── deploy.py                # Task orchestration and feature gates
├── common.py                # Shared initialization and GPG secrets loading
├── group_data/              # Per-host and role/group configuration
├── tasks/                   # pyinfra task modules
│   └── workstation/         # Opt-in workstation feature tasks
├── templates/               # Jinja2 templates
├── files/                   # Static scripts, dotfiles and configuration
├── secrets.json.gpg.example # Placeholder secrets schema/example
└── docs/                    # Detailed project documentation
```

## Documentation

- [Architecture and execution model](docs/architecture.md)
- [Host configuration reference](docs/configuration.md)
- [Deployment workflow and safety checks](docs/deployment.md)
- [Task catalogue](docs/tasks.md)
- [Secrets management](docs/secrets.md)
- [VS Code GPG Vault extension](vscode/gpg-vault/README.md)
- [Templates and static assets](docs/templates.md)
- [System configuration details](docs/system.md)
- [Development and contribution workflow](docs/development.md)

## Operational and security notes

- Treat the checked-in host configuration as an example, not a portable default. It may contain hostnames, network ranges, usernames, repository definitions, and device-specific USBGuard rules.
- Never put private keys, API tokens, passwords, or credential-bearing URLs in `group_data/`, task code, templates, or commits. Put supported secret values in the encrypted JSON file.
- The encrypted file is only as safe as its passphrase, key management, filesystem permissions, and backups. Encryption does not make it safe to publish indiscriminately.
- `deploy.py` includes core tasks unconditionally. Review their effects even when optional features are disabled.
- WireGuard configuration deployment and VPN service activation are separate tasks. The former writes configuration; the latter conditionally enables `wg-quick@<interface>` based on IPv4 local-network detection.
- Review firewall and USBGuard rules carefully. A default-deny USB policy or restrictive firewall can lock you out of a system or peripheral.
- **Borgmatic warning:** the checked-in Borgmatic template currently contains a literal fallback encryption passphrase (`B0rgm4t1C!`) The generated `/etc/borgmatic/config.yaml` is mode `0600`, but the fallback is public in source and is not suitable for a real repository. Replace it with a unique secret before using Borgmatic for real backups.

## Development

Install the pinned project dependencies and development tools with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
pre-commit install
```

The project requires Python 3.12 or newer. `pyproject.toml` defines the runtime dependencies and the `dev` dependency group; `uv.lock` pins the resolved environment. Use `uv sync --dev` after changing the dependency definitions or updating the lockfile.

Run the configured checks and the repository's mocked task regression tests:

```bash
pre-commit run --all-files
python -m pytest tests/ -v
```

The pytest suite uses mocked pyinfra APIs; it does not deploy to or modify a real host. GitHub Actions runs it on pushes and pull requests targeting `main`.

See [Development](docs/development.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

The project is distributed under the MIT License. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
