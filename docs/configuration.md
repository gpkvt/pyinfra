# Configuration

Configuration is host-specific and lives in `group_data/`. The file `group_data/@local.py` contains the configuration for the local environment. Variables defined there are available in tasks as `host.data.<name>`.

> The shipped files contain examples and defaults for the author's local environment. **Adapt them to your own infrastructure before deployment.** Sensitive credentials and private keys are maintained separately in the encrypted secrets configuration (see `docs/secrets.md`). Default values for optional settings are determined by the consuming deployment modules.

## Configuration sections

Per the module docstring of `group_data/@local.py`, settings are organized into logical sections:

### General

Primary user, group, home directory, and system settings:

| Variable | Meaning | Example in `@local.py` |
| --- | --- | --- |
| `hostname` | System hostname | `chao` |
| `username` | Primary user name | `gpkvt` |
| `usergroup` | Primary group | `gpkvt` |
| `homedir` | Home directory (also published as `builtins.homedir`) | `/home/gpkvt` |
| `timezone` | System timezone | `Europe/Amsterdam` |
| `locale` | System locale | `en_US.UTF-8` |
| `keyboard` | Keyboard layout, model, variant and options | `de` |
| `editor` | Preferred editor | `mcedit` |
| `local_network_cidr` | Local network, used by VPN/WireGuard tasks (default `10.0.0.0/24`) | `192.168.42.0/24` |
| `wireguard_interface` | WireGuard interface name (default `False`) | `home` |

### Network — `/etc/hosts` mappings

The `hostnames` dictionary drives the `hosts` task (management of `/etc/hosts`). Example from `@local.py`:

python

```python
hostnames = {
    "127.0.0.1": "localhost local.21x9.org timetagger.21x9.org",
    "::1": "localhost local.21x9.org",
    "192.168.42.100": "storage.intern.21x9.org paperless.intern.21x9.org",
    "192.168.42.120": "storage.21x9.org",
}
```

### System

System-level configuration is managed through the following variables:

| Variable | Purpose |
| --- | --- |
| `sysctl` | Linux kernel parameters |
| `udev` | Custom udev rules |
| `usbguard` | USBGuard settings and authorization rules |

### User environment

Configuration values controlling optional shell and terminal tooling:

| Variable | Task gated | Effect |
| --- | --- | --- |
| `zsh` | `tasks/zsh.py` | Install/configure Zsh |
| `tmux` | `tasks/tmux.py` | Install/configure tmux |
| `powerline` | `tasks/powerline.py` | Install/configure Powerline |
| `powerline_fonts` | Used by font configuration | Controls Powerline font installation |
| `ssh_config` | `tasks/ssh_config.py` | Deploy SSH client configuration |

### SSH

SSH configuration and key management use the following variables:

| Variable | Purpose |
| --- | --- |
| `ssh_config` | SSH client host configuration |
| `ssh_keys` | SSH keypairs to generate/manage |
| `ssh_authorized_keys` | Public keys authorized to access the machine |

### Services and feature flags

Optional infrastructure features are controlled through host configuration:

| Variable | Task gated |
| --- | --- |
| `caddy_config` | `tasks/caddy.py` |
| `ufw` | `tasks/ufw.py` |
| `docker` | `tasks/docker.py` |
| `apparmor_profiles` | `tasks/apparmor.py` |
| `cosmic` | `tasks/cosmic/deploy.py` (COSMIC desktop) |
| `mullvad_extensions` | `tasks/mullvad_extensions.py` |
| `vscodium` | `tasks/vscodium.py` |
| `proton` | `tasks/proton.py` |

These variables can be dictionaries or lists containing the configuration consumed by the corresponding task modules; they are not necessarily simple Boolean flags.

### Combined feature requirements

Some tasks depend on multiple configuration values or external prerequisites:

- **WireGuard tunnel:** requires `wireguard_config` in host data and a `wireguard` entry in secrets.
- **VPN routing:** requires both `local_network_cidr` and `wireguard_interface` to be set.
- **Certificates (dehydrated):** requires a `dehydrated` entry in secrets.
- **Flatpak:** gated by detected availability (`builtins.flatpak`, checked via `initialize(host, check_flatpak=True)`), not by a configuration flag.

### Docker

The `docker` dictionary defines containerized applications and their deployment options.

Example from `@local.py`:

python

```python
docker = {
    "miniflux": {
        "postgres_version": 12,
        "port": "8005",
    },
    "timetagger": {
        "port": "8010",
    },
    "grav": {
        "image": "getgrav/grav:1.7",
        "port": 8015,
        "channel": "stable",
        "setup": True,
        "scheduler": True,
        "fix_permissions": True,
    },
}
```

Corresponding compose and service templates are located under `templates/docker/` (e.g. `miniflux/`, `timetagger/`).

See `docs/tasks.md` (Docker) for details.

### APT packages

The `apt_packages` list defines system packages to install and maintain.

Additional repositories are configured through `apt_sources`, which contains repository URLs, signing keys, distributions, components and architectures.

Both are consumed by `tasks/apt.py`.

### Flatpak applications

The `flatpak_packages` list contains Flatpak application IDs to install, consumed by `tasks/flatpak.py` when Flatpak is available.

Examples from `@local.py` include:

- `com.spotify.Client`
- `com.obsproject.Studio`
- `com.github.tchx84.Flatseal`
- `com.github.wwmm.easyeffects`
- Various COSMIC applets.

### Proton

The `proton` dictionary controls Proton application configuration.

The current example includes:

- Proton Mail
- Proton Bridge
- Proton VPN
- Proton Pass
- Flatpak support
- Proton Drive CLI version

The actual installation and configuration options are defined in `tasks/proton.py`.

### VSCodium

The `vscodium` dictionary contains the extensions to install.

The current example includes extensions for:

- GitHub
- Ansible
- Docker and containers
- Git
- Remote SSH
- Python
- XML and YAML
- Prettier formatting

See `tasks/vscodium.py` for implementation details.

### Mullvad Browser extensions

The `mullvad_extensions` dictionary defines browser extensions, including their extension IDs and download URLs.

The `mullvad_browser_dir` variable specifies the browser profile directory.

See `tasks/mullvad_extensions.py` for implementation details.

### COSMIC Desktop

The `cosmic` dictionary controls COSMIC desktop configuration, including:

- Appearance and dark/light mode.
- Panel position, size and applets.
- Dock position, size and applets.
- Workspace orientation and behavior.

The `cosmic_config_files` dictionary defines the source and destination directories for static COSMIC configuration files.

See `tasks/cosmic/deploy.py` for implementation details.

## Adding a new host

1. Add the host to `inventory.py` (SSH connection settings, sudo options).
2. Create a matching file in `group_data/` (named after the host) with the required variables and feature configuration.
3. Ensure the host is not listed in `disabled_hosts`.
4. Review the configuration and test the deployment before applying changes.
