# Infrastructure Configuration

[![python](https://img.shields.io/badge/Python-3.12-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![pyinfra](https://img.shields.io/badge/pyinfra-v3.10.0-blue)](https://pyinfra.com)
![GitHub branch check suites](https://img.shields.io/github/check-suites/gpkvt/pyinfra/main)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
![GitHub License](https://img.shields.io/github/license/gpkvt/pyinfra)

A configuration-driven infrastructure automation project built with pyinfra.

This repository provides automated provisioning and configuration of Linux systems. It manages system packages, networking, security, Docker services, desktop environments, and user configurations through reusable, modular deployment tasks.

Host-specific settings are separated from deployment logic, allowing individual features and services to be enabled or disabled through configuration.

## Features

### System management

- APT package installation and upgrades
- Flatpak application management
- Hostname and `/etc/hosts` configuration
- System configuration and directory management
- Linux kernel parameters (sysctl)
- Custom udev rules
- USB device access control using USBGuard
- Custom sudoers rules
- SSH key generation and authorized keys
- System and user font management
- Custom scripts and dotfiles

### Networking

- WireGuard VPN configuration
- Automatic VPN activation based on local network detection
- SSH client configuration
- UFW firewall management
- Caddy reverse proxy configuration
- Let's Encrypt certificate management using dehydrated

### Container services

- Docker installation and configuration
- Docker Compose deployments
- User-level systemd service management
- Miniflux
- TimeTagger

### Desktop and user environment

- COSMIC desktop configuration
- VSCodium extension management
- AppArmor profile management
- Zsh and zplug
- Powerlevel10k
- Powerline
- tmux and tmux-powerline
- Midnight Commander
- Git configuration and credentials
- Custom scripts and dotfiles

### Security

- Encrypted secrets using GPG
- SSH configuration and key management
- Custom sudoers rules
- Firewall policies
- AppArmor profile enforcement
- USBGuard USB device authorization
- Restricted permissions for sensitive configuration files

## Requirements

The project is primarily intended for Debian-based Linux systems.

### Required software

- Python 3
- pyinfra
- OpenSSH
- sudo privileges where required
- GPG for encrypted secrets

### Optional software and services

Depending on the enabled features:

- Docker and Docker Compose
- systemd
- Flatpak
- WireGuard
- UFW
- Caddy
- dehydrated
- COSMIC Desktop
- AppArmor
- USBGuard

## Getting started

### 1\. Clone the repository

bash

```bash
git clone https://github.com/gpkvt/pyinfra.git
cd pyinfra
```

### 2\. Create a Python virtual environment

bash

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3\. Install dependencies

bash

```bash
pip install pyinfra
```

For development:

bash

```bash
pip install pre-commit pylint
pre-commit install
```

### 4\. Configure the inventory

The inventory is defined in `inventory.py`.

It contains the available hosts, SSH connection settings, and privilege escalation options.

The special `@local` host represents the local execution environment.

Example:

python

```python
disabled_hosts = {
    "dns",
    "dmz",
}

_all_hosts = {
    "@local": {
        "_sudo": True,
    },
    "dns": {
        "ssh_port": 22,
        "ssh_hostname": "dns",
        "ssh_user": "root",
        "_sudo": True,
    },
}
production = [
    (hostname, options)
    for hostname, options in _all_hosts.items()
    if hostname not in disabled_hosts
]
```

Hosts listed in `disabled_hosts` are excluded from the production inventory.

### 5\. Configure host-specific settings

Host-specific configuration is maintained in `group_data/`.

The `group_data/@local.py` file contains the configuration for the local environment.

Settings are organized into logical sections:

| Section | Description |
| --- | --- |
| General | Username, group, home directory, hostname, timezone, locale, keyboard and editor |
| Network | Local network CIDR and WireGuard interface |
| Hosts | Hostname mappings |
| APT | System packages |
| System | Sysctl parameters, udev rules and USBGuard configuration |
| Sudo | Custom sudoers rules |
| SSH | SSH client configuration, keypairs and authorized keys |
| Fonts | System and user fonts |
| Flatpak | Desktop applications |
| Docker | Containerized applications and services |
| WireGuard | VPN interfaces and settings |
| Firewall | UFW application policies |
| Caddy | Reverse proxy and TLS configuration |
| Zsh | Shell configuration and plugins |
| tmux | Terminal multiplexer |
| Powerline | Terminal themes and configuration |
| VSCodium | Editor extensions |
| COSMIC | Desktop appearance, panel, dock, and workspaces |
| AppArmor | Profiles to enforce |

Optional components are controlled through configuration values. For example:

python

```python
zsh = True
powerline = True
tmux = True
```

Services such as Docker, Caddy, WireGuard, and UFW can be configured independently.

The configuration files contain examples and defaults for the local environment. Adapt them to your own infrastructure before deployment.

## Additional documentation

You can find additional documentation in [docs](docs).

## Secrets management

Sensitive configuration is maintained separately from ordinary host configuration and encrypted using GPG.

The repository provides `secrets.json.gpg.example` as a template.

The actual `secrets.json.gpg` file is not included in version control.

### Secret categories

| Section | Description |
| --- | --- |
| `dehydrated` | Hetzner DNS API credentials |
| `wireguard` | Private keys and peer configuration |
| `git_credentials` | Authenticated Git repository URLs |
| `docker` | Container application credentials |

### Create the secrets file

Copy the example:

bash

```bash
cp secrets.json.gpg.example secrets.json
```

Edit `secrets.json` and replace all placeholder values with your own credentials.

Encrypt the file:

bash

```bash
gpg --symmetric --cipher-algo AES256 secrets.json
```

This creates `secrets.json.gpg`.

After verifying that encryption succeeded, remove the plaintext file:

bash

```bash
shred -u secrets.json
```

The deployment initialization code automatically decrypts `secrets.json.gpg` when it is available.

If the encrypted file does not exist, deployment continues with an empty secrets dictionary. Features requiring secrets are consequently skipped.

### Manually decrypt secrets

For inspection or maintenance:

bash

```bash
gpg --decrypt secrets.json.gpg > secrets.json
```

Remove the decrypted file after use.

### Security recommendations

- Never commit `secrets.json` or `secrets.json.gpg`.
- Only commit the example template with placeholder values.
- Use a strong GPG passphrase.
- Restrict access to encrypted and decrypted secret files.
- Never reuse credentials across services.
- Rotate credentials if they are accidentally exposed.
- Ensure sensitive files have restrictive permissions.

For example:

bash

```bash
chmod 600 secrets.json.gpg
chmod 600 secrets.json
```

Keep the following entries in `.gitignore`:

gitignore

```gitignore
secrets.json
secrets.json.gpg
```

## Repository structure

text

```text
.
├── .github/
├── files/
│   ├── git/
│   ├── mc/
│   ├── powerline/
│   ├── scripts/
│   ├── tmux/
│   ├── ufw/
│   ├── dotfiles/
│   └── cosmic/
├── group_data/
│   └── @local.py
├── templates/
│   ├── dehydrated_config.j2
│   ├── docker/
│   │   ├── grav/
│   │   ├── miniflux/
│   │   └── timetagger/
│   ├── dotfiles/
│   ├── git/
│   ├── ssh_config.j2
│   └── wireguard.conf.j2
├── tasks/
│   ├── docker/
│   ├── cosmic/
│   ├── apt.py
│   ├── apparmor.py
│   ├── caddy.py
│   ├── dehydrated.py
│   ├── docker.py
│   ├── flatpak.py
│   ├── fonts.py
│   ├── git.py
│   ├── hosts.py
│   ├── mc.py
│   ├── powerline.py
│   ├── scripts.py
│   ├── ssh_config.py
│   ├── ssh_keys.py
│   ├── sudo.py
│   ├── system.py
│   ├── tmux.py
│   ├── ufw.py
│   ├── vpn.py
│   ├── vscodium.py
│   ├── wireguard.py
│   └── zsh.py
├── common.py
├── deploy.py
├── inventory.py
├── secrets.json.gpg.example
├── .pre-commit-config.yaml
└── README.md
```

### Main components

| Component | Responsibility |
| --- | --- |
| `inventory.py` | Defines deployment targets and SSH settings |
| `group_data/` | Contains host-specific configuration |
| `common.py` | Initializes shared configuration and decrypts secrets |
| `deploy.py` | Selects and executes deployment tasks |
| `tasks/` | Contains modular provisioning tasks |
| `files/` | Contains scripts, dotfiles, and configuration files |
| `templates/` | Contains Jinja2 templates |
| `secrets.json.gpg.example` | Documents the expected secrets structure |

## Deployment

Deployments are executed through pyinfra.

The `deploy.py` entry point initializes shared configuration and includes deployment tasks according to the active host configuration and available secrets.

### Task execution

The following tasks are always included:

- APT package management
- Host configuration
- Sudo configuration
- SSH key management
- Font management
- Git configuration
- Custom scripts
- Midnight Commander

Additional tasks are included conditionally:

| Task | Activation condition |
| --- | --- |
| Flatpak | Flatpak is available |
| SSH configuration | `ssh_config` is configured |
| WireGuard | Configuration and secrets are available |
| VPN | Local network and WireGuard interface are configured |
| dehydrated | Dehydrated secrets are available |
| Caddy | `caddy_config` is configured |
| Zsh | `zsh` is enabled |
| tmux | `tmux` is enabled |
| Powerline | `powerline` is enabled |
| UFW | `ufw` is configured |
| Docker | `docker` is configured |
| AppArmor | `apparmor_profiles` are configured |
| COSMIC | `cosmic` is configured |
| Mullvad extensions | `mullvad_extensions` is configured |
| VSCodium | `vscodium` is configured |

The `system.py` module additionally provides system-level configuration, including hostname, timezone, locale, keyboard layout, sysctl, udev and USBGuard management. It is currently not included in the main `deploy.py` entry point and must be included separately to execute these operations.

### Execute a deployment

Run the deployment using:

bash

```bash
pyinfra inventory.py deploy.py --sudo --diff
```

The `--diff` option displays the changes pyinfra intends to make.

For remote hosts, ensure SSH connectivity and the required sudo permissions are configured before deployment.

**Important:** Review the inventory and host configuration before executing deployments. Provisioning can modify system packages, network settings, firewall policies, services, and user configuration.

## Development

The project uses pre-commit to validate Python code and configuration files.

### Install development dependencies

bash

```bash
pip install pre-commit pylint
pre-commit install
```

### Run all checks

bash

```bash
pre-commit run --all-files
```

### Run individual checks

bash

```bash
pre-commit run pylint --all-files
pre-commit run check-yaml --all-files
pre-commit run pretty-format-json --all-files
```

### Code quality

The pre-commit configuration includes:

- Python linting with Pylint
- YAML validation and linting
- JSON validation and formatting
- Large-file detection
- Trailing whitespace removal
- End-of-file newline validation
- Merge conflict detection

## Design principles

- **Configuration-driven:** Host-specific behavior is controlled through configuration rather than hardcoded deployment logic.
- **Modular:** Each service and system component has its own deployment module.
- **Conditional:** Optional components are deployed only when enabled and their prerequisites are available.
- **Idempotent:** pyinfra operations aim to maintain the desired system state without unnecessary changes.
- **Secure:** Credentials and private keys are separated from ordinary configuration and encrypted.
- **Reusable:** Shared templates and configuration allow deployment logic to be reused across hosts.

## Contributing

Contributions are welcome! Please read
[CONTRIBUTING.md](CONTRIBUTING.md) before submitting changes.

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
