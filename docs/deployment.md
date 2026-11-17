# Deployment workflow

<div class="page-intro" markdown>
  <div class="page-intro-copy">
    <span class="page-eyebrow">FROM REVIEW TO RECONCILIATION</span>
    <p class="page-lead">Prepare a target, preview the operations and apply only the changes needed to bring it into the desired state.</p>
  </div>
  <div class="page-intro-grid">
  <div class="page-intro-item"><strong>Prepare</strong><span>Inventory, data and access</span></div>
  <div class="page-intro-item"><strong>Preview</strong><span>Dry run with diffs</span></div>
  <div class="page-intro-item"><strong>Apply</strong><span>Run and verify changes</span></div>
  </div>
</div>


Run deployments from the repository root. `deploy.py` initializes shared state and includes task modules according to the selected host's configuration and available secrets.

## Before the first deployment

1. Read the safety notes in the [README](https://github.com/gpkvt/pyinfra/blob/main/README.md).
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

The core set can still have conditional behavior internally, but its modules are included on every deployment. `tasks/scripts.py` also deploys the `gpg-vault` utility from `files/scripts/` and creates its command link. The complete inclusion matrix, including cron, Samba, Docker lifecycle and nested workstation gates, is in the [Feature reference](feature-reference.md).

### Optional tasks

The optional modules are included only when the relevant configuration and runtime prerequisites are satisfied. The full inclusion matrix is maintained in the [Feature reference](feature-reference.md).

| Feature | Inclusion condition | Module(s) |
| --- | --- | --- |
| Cron | Non-empty `cron_jobs` | `tasks/cron.py` |
| Flatpak | Flatpak executable detected during initialization | `tasks/flatpak.py` |
| SSH client | Truthy `ssh_config` | `tasks/ssh_config.py` |
| WireGuard config | Truthy `wireguard_config` and `secrets.wireguard`; `wireguard_enabled` defaults true | `tasks/wireguard.py` |
| VPN activation | `local_network_cidr` and `wireguard_interface`; `vpn_enabled` defaults true | `tasks/vpn.py` |
| Syncthing | Truthy `syncthing`; nested `enabled` defaults true | `tasks/syncthing.py` |
| Shell/terminal | Truthy `zsh`, `tmux` or `powerline` respectively | `tasks/zsh.py`, `tasks/tmux.py`, `tasks/powerline.py` |
| Samba | Truthy `samba`; nested `enabled` defaults false | `tasks/samba.py` |
| UFW | Truthy `ufw`; nested `enabled` defaults true | `tasks/ufw.py` |
| Docker | Truthy `docker` | `tasks/docker.py`, `tasks/docker_container.py` |
| Docker battery monitor | Docker enabled; `docker_power_monitor` defaults true | `tasks/docker_power.py` |
| Sablier | Docker enabled and `docker_sablier.enabled` true | `tasks/docker_sablier.py` |
| Caddy/certificates | Docker enabled, truthy `caddy_config`, and `caddy_enabled` defaults true | `tasks/caddy.py`, `tasks/dehydrated.py` |
| AppArmor | Truthy `apparmor_profiles`; `apparmor_enabled` defaults true | `tasks/apparmor.py` |
| Mullvad extensions | Truthy `mullvad_extensions`; `mullvad_browser_enabled` defaults true | `tasks/mullvad_extensions.py` |
| VSCodium extensions | Truthy `vscodium`; `vscodium_enabled` defaults true | `tasks/vscodium.py` |
| Proton applications | Truthy `proton` | `tasks/proton.py` |

Docker service dispatch is configuration-key based. Supported application keys include `adguard_home`, `appflowy`, `firefly-iii`, `forgejo`, `grav`, `homepage`, `linkwarden`, `mdmesh`, `miniflux`, `nocodb`, `paperless`, `portainer`, `snipe-it`, `tasmoadmin`, `timetagger`, `vaultwarden`, `wallabag` and `wg-easy`. See [Docker services](docker.md) and the [Feature reference](feature-reference.md) for the application catalog.

Sablier and the Docker battery monitor are mutually exclusive. When Sablier is enabled, the battery monitor is disabled and containers it previously stopped are restored. Caddy's Dehydrated DNS-01 flow requires `secrets.dehydrated.hetzner_api_token`.
 
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
| `workstation.cosmic.enabled` | `tasks/workstation/cosmic/deploy.py` | Applies independently enabled appearance, window management, input, shortcuts, panel, dock, workspaces and optional config-file synchronization. Display/output settings are not managed. |
| `workstation.limusic.enabled` | `tasks/workstation/limusic.py` | Installs the latest stable x86-64 AppImage after SHA-256 verification and creates a desktop launcher. |
| `workstation.limusic.enabled` | `tasks/workstation/limusic.py` | Installs the stable x86-64 AppImage after SHA-256 verification and creates its desktop launcher. |

The tracked workstation example disables all workstation features by default. Audit and explicitly enable each feature before applying a deployment.

## Deployment behavior to understand

For the full top-level host-data index, optional task gates, COSMIC subfeatures, Docker application catalog and every task module, see the [Complete feature and configuration reference](feature-reference.md).

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
