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
| `tasks/ssh_config.py` | `ssh_config` | Renders the user's SSH client configuration with a hardened global baseline followed by configured host entries. |
| `tasks/wireguard.py` | `wireguard_config` and `secrets.wireguard` | Installs WireGuard and writes `/etc/wireguard/<interface>.conf`; does not start the service. |
| `tasks/vpn.py` | `local_network_cidr` and `wireguard_interface` | Enables/starts `wg-quick@<interface>` when the host is outside the configured IPv4 network. |
| `tasks/dehydrated.py` | `secrets.dehydrated` | Configures dehydrated for ACME certificate management and deploys its hook. |
| `tasks/caddy.py` | `caddy_config` | Deploys Caddy configuration from host data. |
| `tasks/syncthing.py` | `syncthing` | Installs Syncthing, enables `syncthing@<username>`, and configures its GUI listen address (loopback by default). Device and folder sharing is configured separately in Syncthing. |
| `tasks/zsh.py` | `zsh` | Installs/configures Zsh and related user configuration. |
| `tasks/tmux.py` | `tmux` | Deploys tmux configuration. |
| `tasks/powerline.py` | `powerline` | Deploys Powerline prompt configuration. |
| `tasks/ufw.py` | `ufw` | Applies configured UFW application policies. |
| `tasks/docker.py` and `tasks/docker_container.py` | `docker` | Installs Docker, defines the shared Compose/systemd deployment helper, and dispatches configured Miniflux, TimeTagger, Grav, Forgejo, Portainer, TasmoAdmin, Wallabag, Vaultwarden, NocoDB and Homepage services. |
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

### UFW firewall

`tasks/ufw.py` supports the `chromecast-dlna`, `kdeconnect` and `localsend` application profiles plus `ssh` (TCP port 22). Each configured value must be `Allow` or `Deny`; unsupported keys and values are ignored. The task sets default incoming policy to deny and outgoing policy to allow, applies configured rules, and then enables UFW. Review the resulting policy before applying it remotely. The supplied `group_data/@local.py` currently sets `ssh` to `Deny`, so do not copy that policy to a remotely managed host without a separate recovery path.

### APT

Repository definitions include a signing-key URL and destination plus repository URL, distribution, components and optional architectures/types. Review third-party repository configuration carefully: adding a repository delegates package trust to that repository's signing key and publishing process.

### SSH keys and client hardening

The key task supports Ed25519 and RSA key generation; RSA keys must be at least 3072 bits. Private keys are not overwritten when they already exist. Passphrases can be supplied through `secrets.ssh`. Keep backups of keys and verify authorized-key changes before removing access paths.

The SSH client task writes a global `Host *` baseline before the configured `ssh_config` host entries. It enables `HashKnownHosts`, `StrictHostKeyChecking accept-new`, `UpdateHostKeys`, and public-key authentication; disables agent forwarding, X11 forwarding, local commands and configured forwarding; and sets connection timeout/keepalive values. With OpenSSH's first-obtained-value behavior, these baseline options take precedence over later host-specific entries. `accept-new` automatically records previously unseen host keys but still rejects changed keys; verify host fingerprints through a trusted channel when onboarding sensitive systems.

### WireGuard and VPN activation

The WireGuard task installs the package and renders one file per configured interface. The VPN task is separate: it inspects globally scoped IPv4 addresses using `ip -j -4 addr show scope global`, compares them with `local_network_cidr`, and enables/runs the configured `wg-quick@...` service when outside that network. IPv6 is not considered by the network-detection check.

### Docker services

When `host.data.docker` is truthy, `deploy.py` includes `tasks/docker.py` and `tasks/docker_container.py`. The first installs Docker and defines the shared `deploy_docker_service()` helper. The second includes a service module from `tasks/docker/` for each configured service key.

**Deployment behavior**

- Compose files are rendered to `~/<service>/docker-compose.yml`.
- User-level systemd units are rendered to `~/.config/systemd/user/<service>.service`.
- Persistent data and per-service Docker directories live under the configured user's `~/.docker/` directory.
- A changed Compose file triggers `docker compose pull`; a changed Compose file or systemd unit triggers a service restart.
- An unchanged Compose file does not trigger an image pull. Image updates therefore require a configuration change or a separate manual pull.

**Available services**

All persistent application data currently uses host bind mounts. The paths below are relative to the configured user's home directory.

| Service | Persistent data | Default loopback interface |
| --- | --- | --- |
| Miniflux | `~/.docker/miniflux/db/` (PostgreSQL) | `127.0.0.1:8080` |
| TimeTagger | `~/.docker/timetagger/` | `127.0.0.1:8080` |
| Grav | `~/.docker/grav/data/` | `127.0.0.1:8080` |
| Forgejo | `~/.docker/forgejo/data/` | Web: `127.0.0.1:3000`; SSH: `127.0.0.1:2222` |
| Portainer | `~/.docker/portainer/data/` | `127.0.0.1:9000` |
| TasmoAdmin | `~/.docker/tasmoadmin/data/` | `127.0.0.1:8016` |
| Wallabag | `~/.docker/wallabag/data/`, `~/.docker/wallabag/images/` | `127.0.0.1:8017` |
| Vaultwarden | `~/.docker/vaultwarden/` | `127.0.0.1:8018` |
| NocoDB | `~/.docker/nocodb/data/` | `127.0.0.1:8019` |
| Homepage | `~/.docker/homepage/config/` | `127.0.0.1:8020` |

**Service-specific notes**

- **Miniflux** uses a PostgreSQL companion container. Its database is persisted in `~/.docker/miniflux/db/`; administrator and database credentials are read from `secrets.docker.miniflux`.
- **TimeTagger** stores its data in `~/.docker/timetagger/`, mounted at the container's `/root/_timetagger` directory.
- **Grav** persists the complete web application data directory in `~/.docker/grav/data/`. Its `setup`, `scheduler` and `fix_permissions` options are configurable.
- **Forgejo** persists application data in `~/.docker/forgejo/data/`. Its web and SSH ports bind to loopback by default; the public domain is configurable.
- **Portainer** persists data in `~/.docker/portainer/data/` and mounts `/var/run/docker.sock`. Access to Portainer effectively grants administrative control over the Docker host; expose it only through a trusted, authenticated reverse proxy.
- **TasmoAdmin** mounts `~/.docker/tasmoadmin/data/` at `/data/tasmoadmin`, matching its `TASMO_DATADIR` setting.
- **Wallabag** uses SQLite and persists its database/application data and article images in the two host directories shown above. The directories are mounted into the container paths used by Wallabag's `www-data` process. The supplied local Caddy configuration publishes it as `wallabag.21x9.org`; the initial credentials are `wallabag` / `wallabag`, which must be changed after first login.
- **Vaultwarden** persists its data in `~/.docker/vaultwarden/`. Public signups and invitations are disabled. An optional Argon2 PHC admin-token hash is read from `secrets.docker.vaultwarden.admin_token`; generate it with `docker run --rm -it vaultwarden/server:latest /vaultwarden hash`. Its supplied local Caddy hostname is `vaultwarden.21x9.org`.
- **NocoDB** persists application data in `~/.docker/nocodb/data/`, mounted at `/usr/app/data`. Its HTTP interface binds to loopback on port `8019` by default; the supplied local Caddy hostname is `nocodb.21x9.org`.
- **Homepage** stores its configuration in `~/.docker/homepage/config/`, mounted at `/app/config`. It binds to loopback on port `8020` and sets `HOMEPAGE_ALLOWED_HOSTS` to the configured hostname; the supplied local Caddy hostname is `homepage.21x9.org`. Optional host-data keys `settings`, `services`, `bookmarks`, `widgets`, `docker`, `kubernetes` and `proxmox` are rendered to their matching `*.yaml` files. Each file is rendered only when its key is present, so omitted sections are left untouched. Docker socket access is not enabled by default. Homepage dashboards may expose sensitive widget data, so protect access with a trusted reverse proxy authentication policy, Homepage authentication, or a VPN.

**Storage migration**

The current Compose templates use host bind mounts, not Docker-managed named volumes. If a service was previously deployed using an earlier named-volume template (notably Wallabag or Vaultwarden), Docker Compose will not copy that volume's contents into the new host directory. Back up the old volume and migrate its contents before switching templates. Existing data already in the documented host directories remains in place.

`tasks/docker/` contains the service-specific configuration and `templates/docker/` contains the corresponding Compose files. Consult both before changing a service's supported host-data keys or storage layout.

### Browser and editor extensions

Mullvad extension downloads are defined by extension IDs and URLs. The supplied local configuration includes Wallabagger for connecting the browser to the self-hosted Wallabag instance. VSCodium extension installation is additive: already-installed extensions are detected and left in place. Review external download sources before enabling either task.

### Proton

The Proton task supports components selected through the `proton` configuration, including Mail, Mail Bridge, VPN, Pass and Drive CLI. Installation source varies by component and configuration; consult `tasks/proton.py` for the exact current options.

## Run an individual task

For diagnosis or focused testing, pyinfra can run a task file directly. Example:

```bash
pyinfra inventory.py tasks/system.py --dry --diff
```

A task run directly may not have all initialization or feature-gate behavior of `deploy.py`; inspect whether the task initializes shared state itself. Prefer the full entry point for normal provisioning.
