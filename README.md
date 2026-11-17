# pyinfra

[![CI](https://img.shields.io/github/actions/workflow/status/gpkvt/pyinfra/idempotency.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/gpkvt/pyinfra/actions/workflows/idempotency.yml)
[![License](https://img.shields.io/github/license/gpkvt/pyinfra?label=license)](LICENSE)
[![Issues](https://img.shields.io/github/issues/gpkvt/pyinfra?logo=github)](https://github.com/gpkvt/pyinfra/issues)
[![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platforms](https://img.shields.io/badge/platforms-Debian%20%7C%20Ubuntu-A81D33?logo=debian&logoColor=white)](https://www.debian.org/)

**Declarative Linux infrastructure and workstation automation, powered by [pyinfra](https://pyinfra.com/).**

pyinfra brings server setup, desktop configuration and application deployment together in one version-controlled automation repository. Reusable tasks describe the desired state; inventory and host data determine where and how those tasks run.

The project primarily targets Debian and Ubuntu. It is an opinionated, configurable toolkit rather than a ready-made image: review the examples, adapt the host configuration and preview every deployment before applying it.

> [!WARNING]
> Deployments can install or upgrade packages, change system configuration, manage services and alter firewall or USB authorization rules. A mistake can interrupt network access or lock you out of a machine. Start with a dry run and a disposable or otherwise recoverable target. Never deploy the example configuration unchanged.

## At a glance

| | |
| --- | --- |
| **Automation engine** | [pyinfra](https://pyinfra.com/) with Python task modules |
| **Supported systems** | Debian and Ubuntu |
| **Python** | 3.12 or newer |
| **Configuration** | Python inventory and host/group data, Jinja2 templates |
| **Secrets** | GPG-encrypted JSON, with CLI and VS Code vault workflows |
| **Deployment** | Local or remote over SSH |

## What you can manage

The repository is organized into reusable task modules. Optional components are selected through configuration and prerequisites; they are not all enabled by default.

<details>
<summary><strong>System foundations and security</strong></summary>

- APT repositories and package installation
- Hostname, timezone, locale, keyboard and editor configuration
- sysctl, udev and system configuration
- SSH client configuration and authorized keys
- sudoers rules and AppArmor profiles
- UFW firewall and USBGuard policies

</details>

<details>
<summary><strong>Networking and services</strong></summary>

- WireGuard configuration and conditional VPN activation
- Docker Compose applications, including AppFlowy, Homepage, Linkwarden, Paperless-ngx, Firefly III, Snipe-IT and WG-Easy
- Caddy and Sablier for reverse-proxy and on-demand service startup
- Dehydrated with Hetzner DNS-01 certificate automation
- Syncthing and optional Samba upload/download shares

</details>

<details>
<summary><strong>Desktop and workstation</strong></summary>

- Flatpak applications and COSMIC desktop settings
- Fonts, VSCodium extensions and Proton applications
- Optional desktop utilities, printer/scanner support and maintenance tools
- Power management, firmware/microcode tools and storage health utilities

</details>

<details>
<summary><strong>Developer and shell environment</strong></summary>

- Zsh, tmux, Powerline and Git configuration
- Midnight Commander, scripts and dotfiles
- A VS Code extension for GPG-based file and selection encryption

</details>

<details>
<summary><strong>Secrets management</strong></summary>

- Encrypted JSON storage for supported application credentials, tokens and private keys
- `gpg-vault` command-line workflows
- VS Code GPG Vault extension
- Secret-dependent tasks are included only when the encrypted secrets file is available

</details>

For the complete module list and feature details, see the [task reference](docs/tasks.md).

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/gpkvt/pyinfra.git
cd pyinfra
```

### 2. Install the environment

Install [uv](https://docs.astral.sh/uv/) if it is not already available, then create the project environment:

```bash
uv sync
source .venv/bin/activate
```

For development and tests, use `uv sync --dev` instead.

### 3. Create local configuration

Copy the tracked examples to their ignored, machine-specific counterparts:

```bash
cp group_data/@local.py.example group_data/@local.py
cp group_data/workstation.py.example group_data/workstation.py
```

Edit these files and replace every placeholder. Keep machine-specific values and secrets out of Git. The examples intentionally leave workstation features opt-in.

### 4. Review the inventory and host data

Review `inventory.py` before running anything:

- Keep only the hosts you intend to manage.
- Replace example hostnames and SSH settings.
- Check the connection user and privilege escalation settings.
- Review disabled hosts and inventory group membership.

Create or adapt `group_data/<inventory-host>.py` for each target. Review user identity, home directory, hostname, locale, timezone, packages, network settings and optional service configuration.

The special `@local` target runs against the machine executing pyinfra. It is not a remote host. See the [configuration guide](docs/configuration.md) for the complete settings model.

### 5. Preview before applying

Run commands from the repository root.

```bash
# Preview all selected operations; do not change the target
pyinfra inventory.py deploy.py --dry --diff

# Preview only the local target
pyinfra inventory.py deploy.py --limit @local --dry --diff
```

Read the complete diff and investigate unexpected changes before applying:

```bash
pyinfra inventory.py deploy.py --diff
```

A dry run is an important review step, not a substitute for backups, testing or change control. Check the options supported by your installed version with `pyinfra --help`.

## How the repository is structured

```text
.
├── inventory.py              # Targets and connection options
├── deploy.py                 # Task orchestration and feature gates
├── common.py                 # Shared initialization and secrets loading
├── group_data/                # Host and inventory-group configuration
├── tasks/                     # Reusable pyinfra task modules
│   └── workstation/           # Optional workstation tasks
├── templates/                 # Jinja2 configuration templates
├── files/                     # Scripts, dotfiles and static assets
├── vscode/gpg-vault/          # VS Code GPG Vault extension
├── docs/                      # Detailed documentation
└── tests/                     # Mocked task regression tests
```

The deployment flow is intentionally separated:

1. Inventory selects targets and connection settings.
2. Host and group data provide configuration.
3. `deploy.py` initializes shared values and selects task modules.
4. Task modules declare operations for pyinfra to execute.
5. Templates and static files provide the content deployed to targets.
6. `common.py` loads the encrypted secrets file when present.

See [Architecture](docs/architecture.md) for more detail.

## Secrets

When a deployment needs credentials, use the GPG vault workflow rather than putting secrets in host data, templates or task code.

The `gpg-vault` helper supports creating, editing, viewing and checking the encrypted JSON file:

```bash
gpg-vault create
gpg-vault edit
gpg-vault view
gpg-vault status
```

It defaults to `secrets.json` and `secrets.json.gpg`. Use `gpg-vault --file path/to/other.json COMMAND` to work with another file. GPG and an editor (the default is `nano`) are required for editing. The deployment loads `secrets.json.gpg` directly; without it, the shared secrets dictionary is empty and secret-dependent tasks are not selected.

Treat decrypted values and terminal output as sensitive. Protect the GPG key and passphrase, file permissions and backups. See [Secrets management](docs/secrets.md).

## Documentation

| Guide | What it covers |
| --- | --- |
| [Architecture](docs/architecture.md) | Execution flow and repository design |
| [Configuration](docs/configuration.md) | Inventory, host data and configuration options |
| [Deployment](docs/deployment.md) | Running, previewing and safely applying deployments |
| [Task reference](docs/tasks.md) | Available task modules and managed services |
| [Secrets](docs/secrets.md) | Encrypted configuration and vault workflows |
| [Templates and files](docs/templates.md) | Jinja2 templates and static assets |
| [System configuration](docs/system.md) | System-level settings and behavior |
| [Development](docs/development.md) | Local setup, tests and contribution workflow |
| [Releasing](docs/releasing.md) | Version tags and GitHub Releases |
| [VS Code GPG Vault](vscode/gpg-vault/README.md) | Extension setup and usage |

## Development and checks

Install development dependencies and the repository's pre-commit hooks:

```bash
uv sync --dev
pre-commit install
```

Run the checks before submitting a change:

```bash
pre-commit run --all-files
python -m pytest tests/ -v
```

The pytest suite mocks pyinfra APIs; it does not deploy to or modify a real host. CI runs the regression suite for pushes and pull requests targeting `main`.

Please keep task changes idempotent: a second run against an already-correct target should not report changes or repeat unnecessary work. Add or update tests and documentation alongside task behavior changes. See [Development](docs/development.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Safety and operational notes

- Treat tracked `.example` files as starting points, not production-ready configuration.
- Do not commit private keys, API tokens, passwords, credential-bearing URLs or host-specific private data.
- Review firewall and USBGuard changes carefully; restrictive policies can cut off access or disable peripherals.
- WireGuard configuration deployment and VPN service activation are separate operations. Activation is conditional on local-network detection.
- Some tasks are core deployment tasks and run regardless of optional feature flags. Review their effects before deploying.
- **Borgmatic:** the current template contains a literal fallback encryption passphrase (`B0rgm4t1C!`). This value is public in the repository and is not suitable for real backups. Replace it with a unique secret before enabling Borgmatic.

## License

Released under the [MIT License](LICENSE). See [NOTICE.md](NOTICE.md) for notices.
