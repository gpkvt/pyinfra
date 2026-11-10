# Task reference

`deploy.py` is the authoritative task orchestrator. It always includes the core modules and includes optional modules only when their gate is truthy. This page summarizes each module; inspect the implementation and its templates for the definitive behavior and accepted data shape.

## Core tasks

These task modules are included on every full deployment.

| Module | Responsibility | Main configuration |
| --- | --- | --- |
| `tasks/apt.py` | Downloads configured repository keys, writes APT source lists, updates package indexes, upgrades packages when the index changes, and installs packages. | `apt_sources`, `apt_packages` |
| `tasks/hosts.py` | Manages `/etc/hosts` mappings. | `hostnames` |
| `tasks/sudo.py` | Writes custom sudoers rules to `/etc/sudoers.d/99-local`, validates with `visudo`, and sets restrictive permissions. | `sudoers_rules` |
| `tasks/system.py` | Manages hostname, timezone, locale, editor environment, keyboard, sysctl, udev and USBGuard. | See [System configuration](system.md). |
| `tasks/ssh_keys.py` | Generates supported SSH keypairs only when absent and manages authorized keys. Existing private keys are not overwritten. | `ssh_keys`, `ssh_authorized_keys`, `secrets.ssh` |
| `tasks/git.py` | Installs/configures Git and deploys Git-related configuration and credentials when available. | Git host data and `secrets.git_credentials` |
| `tasks/fonts.py` | Installs font packages; optionally downloads Powerline-patched fonts. | `powerline_fonts` |
| `tasks/scripts.py` | Synchronizes `files/scripts/` into the configured user's scripts directory and creates command links. This includes `gpg-vault`, the helper for managing `secrets.json.gpg`. Existing destination files not in the source are preserved. | `username`, `usergroup` |
| `tasks/mc.py` | Installs and configures Midnight Commander. | `username`, `usergroup` |

## Optional tasks

| Module | Inclusion condition | Responsibility |
| --- | --- | --- |
| `tasks/flatpak.py` | Flatpak executable detected during initialization | Installs configured Flatpak application IDs. |
| `tasks/ssh_config.py` | `ssh_config` | Renders the user's SSH client configuration. |
| `tasks/wireguard.py` | `wireguard_config` and `secrets.wireguard` | Installs WireGuard and writes `/etc/wireguard/<interface>.conf`; does not start the service. |
| `tasks/vpn.py` | `local_network_cidr` and `wireguard_interface` | Enables/starts `wg-quick@<interface>` when the host is outside the configured IPv4 network. |
| `tasks/dehydrated.py` | `secrets.dehydrated` | Configures dehydrated for ACME certificate management and deploys its hook. |
| `tasks/caddy.py` | `caddy_config` | Deploys Caddy configuration from host data. |
| `tasks/zsh.py` | `zsh` | Installs/configures Zsh and related user configuration. |
| `tasks/tmux.py` | `tmux` | Deploys tmux configuration. |
| `tasks/powerline.py` | `powerline` | Deploys Powerline prompt configuration. |
| `tasks/ufw.py` | `ufw` | Applies configured UFW application policies. |
| `tasks/docker.py` | `docker` | Deploys configured Docker Compose services and user-level systemd units. |
| `tasks/apparmor.py` | `apparmor_profiles` | Loads/enforces configured AppArmor profiles. |
| `tasks/cosmic/deploy.py` | `cosmic` | Deploys COSMIC desktop configuration and assets. |
| `tasks/mullvad_extensions.py` | `mullvad_extensions` | Downloads configured browser extensions and deploys `user.js`. |
| `tasks/vscodium.py` | `vscodium` | Installs configured VSCodium extensions that are not already installed. |
| `tasks/proton.py` | `proton` | Installs/configures selected Proton applications using the configured distribution sources. |

## Workstation role tasks

The modules below are included by `deploy.py` only when the matching nested setting under `host.data.workstation` has `enabled: True`. Their shared defaults are defined in `group_data/workstation.py`; inventory membership determines which hosts receive that group data.

| Module | Responsibility | Configuration |
| --- | --- | --- |
| `tasks/workstation/backup.py` | Installs Restic, Borg, rsync and Borgmatic; renders `/etc/borgmatic/config.yaml`. It does not create, schedule or run backups. | `workstation.backup.enabled` |
| `tasks/workstation/power.py` | Installs/enables TLP or Power Profiles Daemon and removes the conflicting manager. | `workstation.power.enabled`, `workstation.power.manager` |
| `tasks/workstation/hardware.py` | Installs fwupd and optional CPU microcode. Firmware updates are not applied automatically. | `workstation.hardware.enabled`, `workstation.hardware.cpu_vendor` (`intel`, `amd` or unset) |
| `tasks/workstation/storage.py` | Installs `smartmontools` and `nvme-cli`; does not configure polling or alerting. | `workstation.storage.enabled` |
| `tasks/workstation/peripherals.py` | Installs optional printer/scanner packages; enables CUPS when printing is selected. | `workstation.peripherals.enabled`, `printing`, `scanning` |
| `tasks/workstation/desktop.py` | Installs common desktop integration utilities. A custom package list replaces the defaults. | `workstation.desktop.enabled`, optional `packages` list |
| `tasks/workstation/maintenance.py` | Installs `needrestart`, `debian-goodies` and `apt-file`; does not enable unattended upgrades or schedule reboots. | `workstation.maintenance.enabled` |

The supplied `group_data/workstation.py` enables backup, power, hardware and storage by default. Peripheral support, desktop utilities and maintenance utilities are disabled. Review the group data before assigning additional hosts to the workstation group.

## Feature notes

### GPG secret utility

`tasks/scripts.py` deploys `files/scripts/gpg-vault` with the other user scripts and creates its command link. The helper provides `create`, `edit`, `view`, `encrypt`, `decrypt`, `rekey` and `status`; see [Secrets management](secrets.md). It is not invoked by `deploy.py`: `common.initialize()` remains responsible for decrypting `secrets.json.gpg` during deployment.

### APT

Repository definitions include a signing-key URL and destination plus repository URL, distribution, components and optional architectures/types. Review third-party repository configuration carefully: adding a repository delegates package trust to that repository's signing key and publishing process.

### SSH keys

The task supports Ed25519 and RSA key generation; RSA keys must be at least 3072 bits. Private keys are not overwritten when they already exist. Passphrases can be supplied through `secrets.ssh`. Keep backups of keys and verify authorized-key changes before removing access paths.

### WireGuard and VPN activation

The WireGuard task installs the package and renders one file per configured interface. The VPN task is separate: it inspects globally scoped IPv4 addresses using `ip -j -4 addr show scope global`, compares them with `local_network_cidr`, and enables/runs the configured `wg-quick@...` service when outside that network. IPv6 is not considered by the network-detection check.

### Docker services

Service-specific definitions live in `tasks/docker/` and `templates/docker/`. The current repository includes Miniflux, TimeTagger and Grav modules. Compose files and user-level systemd units are deployed under the configured user's home/configuration directories. Changes can cause image pulls and service restarts.

### Browser and editor extensions

Mullvad extension downloads are defined by extension IDs and URLs. VSCodium extension installation is additive: already-installed extensions are detected and left in place. Review external download sources before enabling either task.

### Proton

The Proton task supports components selected through the `proton` configuration, including Mail, Mail Bridge, VPN, Pass and Drive CLI. Installation source varies by component and configuration; consult `tasks/proton.py` for the exact current options.

## Run an individual task

For diagnosis or focused testing, pyinfra can run a task file directly. Example:

```bash
pyinfra inventory.py tasks/system.py --dry --diff
```

A task run directly may not have all initialization or feature-gate behavior of `deploy.py`; inspect whether the task initializes shared state itself. Prefer the full entry point for normal provisioning.
