# Deployment workflow

Run deployments from the repository root. `deploy.py` initializes shared state and includes task modules according to the selected host's configuration and available secrets.

## Before the first deployment

1. Read the safety notes in the [README](../README.md).
2. Review `inventory.py`; verify target names, SSH hostnames, ports, users and `_sudo` settings.
3. Review the matching `group_data/<host>.py` and every group-data file for groups assigned to that target. Remove example settings that do not belong on the target. For example, `@local` belongs to the `workstation` group in the supplied inventory and therefore receives `group_data/workstation.py`.
4. Prepare `secrets.json.gpg` only if the enabled features need secrets. Use `gpg-vault create` or `gpg-vault edit` after the script has been deployed; see [Secrets management](secrets.md).
5. Confirm SSH connectivity and privilege escalation on remote targets.
6. Back up important system and application configuration, and arrange console/out-of-band access for firewall or network changes.

## Preview and apply

```bash
# Show the planned changes without applying them
pyinfra inventory.py deploy.py --dry --diff

# Apply the deployment
pyinfra inventory.py deploy.py --diff
```

Limit execution to one host when testing:

```bash
pyinfra inventory.py deploy.py --limit @local --dry --diff
```

The precise CLI options can vary with pyinfra versions; consult `pyinfra --help` if an option is unavailable. `--diff` helps inspect file changes. A dry run is not a substitute for reviewing task code, backups, or recovery access.

## Task selection

### Core tasks

These modules are always included by `deploy.py`:

1. `tasks/apt.py`
2. `tasks/hosts.py`
3. `tasks/sudo.py`
4. `tasks/system.py`
5. `tasks/ssh_keys.py`
6. `tasks/git.py`
7. `tasks/fonts.py`
8. `tasks/scripts.py`
9. `tasks/mc.py`

The core set can still have conditional behavior internally, but its modules are included on every deployment. `tasks/scripts.py` also deploys the `gpg-vault` utility from `files/scripts/` and creates its command link.

### Optional tasks

| Inclusion condition in `deploy.py` | Module |
| --- | --- |
| Flatpak executable detected by `Which` | `tasks/flatpak.py` |
| `host.data.ssh_config` is truthy | `tasks/ssh_config.py` |
| `host.data.wireguard_config` and `secrets.wireguard` are truthy, and `wireguard_enabled` is not false (defaults to true) | `tasks/wireguard.py` |
| `host.data.syncthing` is truthy and `syncthing.enabled` is not false (defaults to true) | `tasks/syncthing.py` |
| `local_network_cidr` and `wireguard_interface` are truthy | `tasks/vpn.py` |
| `host.data.docker` and `host.data.caddy_config` are truthy, and `caddy_enabled` is not false (defaults to true) | `tasks/caddy.py` |
| `host.data.zsh` is truthy | `tasks/zsh.py` |
| `host.data.tmux` is truthy | `tasks/tmux.py` |
| `host.data.powerline` is truthy | `tasks/powerline.py` |
| `host.data.ufw` is truthy | `tasks/ufw.py` |
| `host.data.docker` is truthy | `tasks/docker.py`, `tasks/docker_power.py` and `tasks/docker_container.py` |
| `host.data.docker_sablier.enabled` is true (inside the Docker gate) | `tasks/docker_sablier.py` |
| `host.data.apparmor_profiles` is truthy and `apparmor_enabled` is not false (defaults to true) | `tasks/apparmor.py` |
| `workstation.limusic.enabled` is true | `tasks/workstation/limusic.py` |
| `workstation.cosmic.enabled` is true | `tasks/workstation/cosmic/deploy.py` |
| `host.data.mullvad_extensions` is truthy | `tasks/mullvad_extensions.py` |
| `host.data.vscodium` is truthy | `tasks/vscodium.py` |
| `host.data.proton` is truthy | `tasks/proton.py` |

`tasks/docker.py` installs Docker and defines the shared service deployment helper. Caddy's Dehydrated DNS-01 flow is part of `tasks/caddy.py` and requires `secrets.dehydrated.hetzner_api_token`; there is no separate Dehydrated task gate in `deploy.py`. `tasks/docker_container.py` dispatches to service modules for the configured keys: `miniflux`, `timetagger`, `grav`, `forgejo`, `portainer`, `tasmoadmin`, `wallabag`, `vaultwarden`, `nocodb`, `linkwarden`, `homepage`, `paperless`, `firefly-iii`, `snipe-it` and `wg-easy`. `tasks/docker_power.py` deploys the Docker battery monitor; when Sablier is enabled it restores containers previously stopped by the battery saver and disables that monitor. `tasks/docker_sablier.py` is included only when `docker_sablier.enabled` is true, before application service dispatch. Sablier and the battery monitor are mutually exclusive.

A truthy dictionary or list is a common activation mechanism; these settings are not necessarily Boolean switches. The exact expected structure is described in [Configuration](configuration.md) and [Task reference](tasks.md).

### Workstation role tasks

The workstation role is assigned through inventory group membership, not by naming a host `workstation`. In the supplied inventory, `workstation = ["@local"]` assigns the local target to the group; its shared settings are in `group_data/workstation.py`.

`deploy.py` checks these nested `workstation` flags and includes the matching module only when `enabled` is true:

| Setting | Module | Notes |
| --- | --- | --- |
| `workstation.backup.enabled` | `tasks/workstation/backup.py` | Installs backup tools and renders Borgmatic configuration; does not schedule or run backups. |
| `workstation.power.enabled` | `tasks/workstation/power.py` | Installs/enables either TLP or Power Profiles Daemon and removes the conflicting manager. |
| `workstation.hardware.enabled` | `tasks/workstation/hardware.py` | Installs fwupd and optional Intel/AMD microcode; no unattended firmware updates. |
| `workstation.storage.enabled` | `tasks/workstation/storage.py` | Installs SMART/NVMe inspection tools; no polling or alert schedule. |
| `workstation.peripherals.enabled` | `tasks/workstation/peripherals.py` | Printer and scanner packages are separately controlled by `printing` and `scanning`; printing enables CUPS. |
| `workstation.desktop.enabled` | `tasks/workstation/desktop.py` | Installs common desktop integration packages; optional `packages` replaces the defaults. |
| `workstation.maintenance.enabled` | `tasks/workstation/maintenance.py` | Installs maintenance utilities only; no unattended upgrades or scheduled reboots. |
| `workstation.cosmic.enabled` | `tasks/workstation/cosmic/deploy.py` | Applies enabled COSMIC appearance, panel, dock and workspace settings. |

The tracked workstation example disables all workstation features by default. Audit and explicitly enable each feature before applying a deployment.

## Deployment behavior to understand

- `tasks/apt.py` configures configured repositories, refreshes package indexes, upgrades packages when the index update changes, and installs configured packages.
- `tasks/system.py` can change hostname, timezone, locale, editor environment, keyboard layout, sysctl, udev and USBGuard configuration.
- `tasks/ufw.py` sets default incoming traffic to deny and outgoing traffic to allow, applies supported application/port rules, then enables UFW. Supported keys are `chromecast-dlna`, `kdeconnect`, `localsend` and `ssh`; each accepts `Allow` or `Deny`, while unknown keys/values are ignored. Explicitly allow the actual remote-management port before deployment: the checked-in local example sets `ssh` to `Deny`, which can cut off remote access.
- `tasks/ssh_keys.py` does not overwrite existing private keys, but can manage authorized keys.
- `tasks/wireguard.py` installs WireGuard and writes interface configuration; it does not start or enable the service.
- `tasks/vpn.py` enables and starts `wg-quick@<interface>` when no globally scoped IPv4 address belongs to `local_network_cidr`. It only examines IPv4 addresses.
- Docker tasks prepare Compose projects with `docker compose up --no-start` so Sablier can start services on demand. A changed Compose file triggers an image pull and service reconciliation; user-level systemd operations run as the configured account (or via `runuser` when deployment runs as root). Sablier's default dynamic strategy serves a themed loading page while a service starts; blocking mode is available for clients that cannot use the dynamic page. See [Task reference](tasks.md#docker-services).

## Recommended operating loop

1. Make one focused configuration change.
2. Run a dry deployment against one host.
3. Inspect the diff and the task implementation for high-impact operations.
4. Apply to the test host.
5. Verify the resulting service, network, access and application behavior.
6. Expand to additional hosts only after validation.

For task-level detail, see [Task reference](tasks.md). For implementation work, see [Development](development.md).
