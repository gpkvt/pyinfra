# Complete feature and configuration reference

This page indexes every deployment feature and Python task module. It explains what is always included, what is optional, which host/group settings enable it, and where to find operational detail.

Use this page to discover capabilities; use [Host configuration](configuration.md), [Task reference](tasks.md), [Docker services](docker.md), [System configuration](system.md), [Samba](samba.md), and [Secrets management](secrets.md) for detailed settings and safety notes. The current implementation in deploy.py, each task module and its template remains authoritative.

## Repository and deployment model

| Layer | File or directory | Responsibility |
| --- | --- | --- |
| Inventory | inventory.py | Targets, SSH connection options, privilege escalation and inventory groups. |
| Host/group data | group_data/ | Desired state for a host or role, exposed together through host.data. |
| Orchestration | deploy.py | Shared initialization, baseline task inclusion and optional feature gates. |
| Shared initialization | common.py | Home directory, encrypted secrets selection and Flatpak detection. |
| Task modules | tasks/ | Install packages, manage files/services and reconcile applications. |
| Templates | templates/ | Jinja2 templates for generated configuration and service definitions. |
| Static assets | files/ | Files copied or synchronized by tasks. |
| Secrets | secrets.json.gpg | Encrypted credentials and private keys, selected by inventory hostname. |

A feature is selected through host/group data, not by editing deploy.py. A non-empty mapping/list is not always equivalent to a Boolean. The tracked examples are conservative; workstation features and Samba are disabled by default.

## Core tasks: always included

These modules are included by every full deploy.py run. Individual operations inside a module can still be conditional on configuration or target facts.

| Module | What it manages | Main inputs / notes |
| --- | --- | --- |
| tasks/apt.py | APT repositories, signing keys, package indexes, upgrades and packages. | apt_sources, apt_packages. |
| tasks/hosts.py | Managed /etc/hosts entries. | hostnames maps IP addresses to lists of names. |
| tasks/sudo.py | Custom sudoers drop-in, validation and permissions. | sudoers_rules; validated with visudo. |
| tasks/system.py | Hostname, timezone, locale, editor environment, keyboard, sysctl, udev and USBGuard. | See [System configuration](system.md). |
| tasks/ssh_keys.py | SSH key generation when absent and authorized-key reconciliation. | ssh_keys, ssh_authorized_keys, ssh_authorized_keys_enabled, secrets.ssh; existing private keys are not overwritten. |
| tasks/git.py | Git installation/configuration and credential integration. | Git host data and secrets.git_credentials. |
| tasks/fonts.py | Font packages and optional Powerline-patched fonts. | powerline_fonts. |
| tasks/scripts.py | User scripts and command links, including gpg-vault. | username, usergroup; see [Secrets](secrets.md). |
| tasks/mc.py | Midnight Commander installation and user configuration. | username, usergroup. |

## Optional feature gates

These are the inclusion conditions currently evaluated by deploy.py. “Truthy” means present and non-empty unless a Boolean/default is stated.

| Feature / module | Gate | Defaults and behavior |
| --- | --- | --- |
| Flatpak — tasks/flatpak.py | Flatpak executable detected by common.initialize(check_flatpak=True). | Skipped when Flatpak is absent. Uses user-scoped remotes/apps; flatpak_packages supplies application IDs. |
| Cron — tasks/cron.py | cron_jobs is non-empty. | Installs/enables cron and manages named user/root jobs. Each job needs a name, command and schedule. See [Cron jobs](tasks.md#cron-jobs). |
| SSH client — tasks/ssh_config.py | ssh_config is truthy. | Renders the configured user's SSH client configuration and hardened baseline. |
| WireGuard — tasks/wireguard.py | wireguard_config, secrets.wireguard, and wireguard_enabled (default true). | Installs WireGuard and writes interface configuration; does not start the interface. |
| Automatic VPN — tasks/vpn.py | local_network_cidr and wireguard_interface, plus vpn_enabled (default true). | Starts/enables wg-quick when no global IPv4 address is in the local CIDR. IPv6 is not considered. |
| Syncthing — tasks/syncthing.py | syncthing is truthy and syncthing.enabled (default true). | Installs/enables the configured user's service. GUI binds to loopback by default; sharing is configured in Syncthing. |
| Zsh — tasks/zsh.py | zsh is truthy. | Deploys Zsh configuration, imports/plugins and the LiMusic-aware HyFetch helper. |
| tmux — tasks/tmux.py | tmux is truthy. | Deploys tmux configuration. |
| Powerline — tasks/powerline.py | powerline is truthy. | Deploys Powerline prompt configuration. |
| Samba — tasks/samba.py | samba is truthy and samba.enabled (default false). | Installs on-demand LAN/VPN shares; Samba remains stopped/masked until explicitly started. See [Samba](samba.md). |
| UFW — tasks/ufw.py | ufw is truthy and ufw.enabled (default true). | Applies firewall policy and rules. Review remote SSH access before enabling. |
| Docker — tasks/docker.py, tasks/docker_container.py | docker is truthy. | Installs/configures Docker and dispatches Compose services. Persistent data uses host bind mounts below the configured home directory's .docker/. |
| Docker battery monitor — tasks/docker_power.py | Docker is enabled and docker_power_monitor (default true). | Battery-aware container stop/restore behavior; mutually exclusive with Sablier. |
| Sablier — tasks/docker_sablier.py | Docker is enabled and docker_sablier.enabled is true. | On-demand container startup; disables the battery monitor and restores containers previously stopped by it. |
| Caddy/Dehydrated — tasks/caddy.py, tasks/dehydrated.py | Docker, caddy_config and caddy_enabled (default true). | Docker Caddy reverse proxy and DNS-01 certificate support. Hetzner API token required for that DNS challenge. |
| AppArmor — tasks/apparmor.py | apparmor_profiles is truthy and apparmor_enabled (default true). | Loads/enforces configured profiles. |
| Mullvad extensions — tasks/mullvad_extensions.py | mullvad_extensions is truthy and mullvad_browser_enabled (default true). | Installs configured browser extensions and policy. |
| VSCodium extensions — tasks/vscodium.py | vscodium is truthy and vscodium_enabled (default true). | Installs configured extension IDs that are not already installed. |
| Proton — tasks/proton.py | proton is truthy. | Selects Proton applications and installation sources. Drive CLI requires explicit drive_cli_version. |

## Workstation role features

Workstation tasks require the host to receive workstation group data and the matching nested enabled: true flag. The sample inventory assigns @local to the workstation group. Every feature is disabled in group_data/workstation.py.example.

| Feature | Module | Configuration | Effect / limitations |
| --- | --- | --- | --- |
| Backup tools | tasks/workstation/backup.py | workstation.backup.enabled | Installs Borg, Restic, rsync and Borgmatic and renders Borgmatic config. Does not configure repositories/credentials or run/schedule backups. |
| Power management | tasks/workstation/power.py | workstation.power.enabled, manager | Selects tlp or power-profiles-daemon and removes the conflicting manager. |
| Firmware/microcode | tasks/workstation/hardware.py | workstation.hardware.enabled, cpu_vendor | Installs fwupd and optional Intel/AMD microcode; does not apply firmware updates. |
| Storage inspection | tasks/workstation/storage.py | workstation.storage.enabled | Installs SMART/NVMe tools; no polling or alerting is configured. |
| Printers/scanners | tasks/workstation/peripherals.py | workstation.peripherals.enabled, printing, scanning | Installs selected packages; CUPS is enabled when printing is selected. |
| Desktop utilities | tasks/workstation/desktop.py | workstation.desktop.enabled, optional packages | Installs default or supplied integration packages. |
| Maintenance | tasks/workstation/maintenance.py | workstation.maintenance.enabled | Installs interactive maintenance tools; no unattended upgrades or reboot schedule. |
| LiMusic | tasks/workstation/limusic.py | workstation.limusic.enabled | Installs latest stable x86-64 AppImage, verifies SHA-256 and creates icon/desktop launcher. |
| COSMIC desktop | tasks/workstation/cosmic/deploy.py | workstation.cosmic.enabled | Master switch for appearance, window management, input, shortcuts, panel, dock, workspaces and optional config-file sync. Display/output layout is not managed. |

### COSMIC subfeatures

All subfeatures are nested below workstation.cosmic and have their own enabled flag.

| Key | Module | Settings |
| --- | --- | --- |
| appearance | tasks/workstation/cosmic/appearance.py | mode: dark or light. |
| window_management | tasks/workstation/cosmic/window_management.py | autotile, autotile_behavior (PerWorkspace/Global), focus_follows_cursor, cursor_follows_focus, edge_snap_threshold. |
| input | tasks/workstation/cosmic/input.py | Raw RON strings for default mouse and touchpad settings. |
| shortcuts | tasks/workstation/cosmic/shortcuts.py | Complete custom shortcut RON map. |
| panel | tasks/workstation/cosmic/panel.py | Position, size, autohide, extend, anchor gap and optional left/center/right applet lists. |
| dock | tasks/workstation/cosmic/dock.py | Position, size, autohide, extend, anchor gap and optional applet lists. |
| workspaces | tasks/workstation/cosmic/workspaces.py | Custom workspace RON configuration. |
| config_files | tasks/workstation/cosmic/config_files.py | Named directory mappings with repository-relative src and home-relative dest. |

The live COSMIC exporter is files/scripts/export_cosmic_config.py. Use --dry-run to preview supported settings before updating host data. It preserves management flags and unrelated values and leaves unsupported settings unchanged.

## Docker application catalog

Enable Docker applications by adding a non-empty mapping below docker. Each service has its own module and usually a Compose template. Check the module/template for accepted keys and required secrets; do not assume every service accepts the same generic options.

| Configuration key | Module | Application / notes |
| --- | --- | --- |
| adguard_home | tasks/docker/adguard_home.py | AdGuard Home DNS filtering; host networking and firewall review required. |
| appflowy | tasks/docker/appflowy.py | AppFlowy workspace; PostgreSQL, MinIO, Search and private environment file. |
| firefly-iii | tasks/docker/firefly-iii.py | Personal finance manager; database/application secrets. |
| forgejo | tasks/docker/forgejo.py | Git hosting; web and optional SSH clone endpoint. |
| grav | tasks/docker/grav.py | Grav CMS; image/channel/setup/scheduler options. |
| huginn | tasks/docker/huginn.py | Automation agents; PostgreSQL, web process, worker and encrypted secrets. |
| homepage | tasks/docker/homepage.py | Service dashboard, widgets, services, bookmarks and icon synchronization. |
| linkwarden | tasks/docker/linkwarden.py | Bookmark manager; PostgreSQL, Meilisearch and app secret. |
| mdmesh | tasks/docker/mdmesh.py | Android-only MDM; PostgreSQL, server, edge and supervisor. |
| miniflux | tasks/docker/miniflux.py | RSS reader with PostgreSQL companion and explicit database major version. |
| nocodb | tasks/docker/nocodb.py | No-code database frontend. |
| paperless | tasks/docker/paperless.py | Paperless-ngx; database, data/media/consume/export directories and secrets. |
| portainer | tasks/docker/portainer.py | Docker management UI; privileged host control. |
| snipe-it | tasks/docker/snipe-it.py | IT asset management; database and Laravel secrets. |
| tasmoadmin | tasks/docker/tasmoadmin.py | Tasmota device management. |
| timetagger | tasks/docker/timetagger.py | Time tracking; credentials stored in mode-0600 environment file. |
| vaultwarden | tasks/docker/vaultwarden.py | Bitwarden-compatible password manager; admin token in encrypted secrets. |
| wallabag | tasks/docker/wallabag.py | Read-it-later application. |
| wg-easy | tasks/docker/wg-easy.py | WireGuard web administration and UDP endpoint. |

All persistent service state is stored in host directories under the configured user's .docker/<service>/. These are bind mounts, not Docker-managed named volumes. Supporting containers may intentionally use ephemeral storage; inspect Compose templates before relying on data durability. Most web interfaces bind to loopback for Caddy; AdGuard and VPN protocol ports are deliberate exceptions. See [Docker services](docker.md) for ports, storage, Caddy, Sablier and lifecycle behavior.

### Docker helper and lifecycle modules

| Module | Role |
| --- | --- |
| tasks/docker.py | Docker installation and shared Compose/systemd deployment helper. |
| tasks/docker_container.py | Configured service dispatcher. |
| tasks/docker_power.py | Battery-aware container monitor and restore logic. |
| tasks/docker_sablier.py | Sablier server and on-demand startup labels. |
| tasks/caddy.py | Caddy reverse proxy deployment. |
| tasks/dehydrated.py | Certificate renewal helper/timer. |
| tasks/homepage_config.py | Homepage configuration support. |
| tasks/docker/linkwarden_bookmarks.py | Controller-side Linkwarden-to-Homepage bookmark synchronization. |

## Complete task-module inventory

This list includes implementation, nested feature, helper and test-fixture modules. Helper modules are not necessarily included directly by deploy.py.

| Python module | Purpose |
| --- | --- |
| tasks/apparmor.py | AppArmor profile enforcement. |
| tasks/apt.py | APT repositories and packages. |
| tasks/caddy.py | Caddy reverse proxy and certificate integration. |
| tasks/cron.py | Named cron jobs. |
| tasks/dehydrated.py | Certificate renewal timer/service. |
| tasks/docker.py | Shared Docker installation and Compose helper. |
| tasks/docker/adguard_home.py | AdGuard Home. |
| tasks/docker/appflowy.py | AppFlowy. |
| tasks/docker/ci-smoke.py | CI-only Compose smoke fixture, not a production service. |
| tasks/docker/firefly-iii.py | Firefly III. |
| tasks/docker/forgejo.py | Forgejo. |
| tasks/docker/grav.py | Grav. |
| tasks/docker/homepage.py | Homepage. |
| tasks/docker/linkwarden.py | Linkwarden. |
| tasks/docker/linkwarden_bookmarks.py | Bookmark synchronization helper. |
| tasks/docker/mdmesh.py | MDMesh Android MDM. |
| tasks/docker/miniflux.py | Miniflux. |
| tasks/docker/nocodb.py | NocoDB. |
| tasks/docker/paperless.py | Paperless-ngx. |
| tasks/docker/portainer.py | Portainer. |
| tasks/docker/snipe-it.py | Snipe-IT. |
| tasks/docker/tasmoadmin.py | TasmoAdmin. |
| tasks/docker/timetagger.py | TimeTagger. |
| tasks/docker/vaultwarden.py | Vaultwarden. |
| tasks/docker/wallabag.py | Wallabag. |
| tasks/docker/wg-easy.py | WG-Easy. |
| tasks/docker_container.py | Docker service dispatcher. |
| tasks/docker_power.py | Docker battery monitor. |
| tasks/docker_sablier.py | Sablier deployment. |
| tasks/flatpak.py | User-scoped Flatpak management. |
| tasks/fonts.py | Fonts. |
| tasks/git.py | Git configuration. |
| tasks/homepage_config.py | Homepage configuration helpers. |
| tasks/hosts.py | /etc/hosts entries. |
| tasks/mc.py | Midnight Commander. |
| tasks/mullvad_extensions.py | Mullvad Browser extensions. |
| tasks/powerline.py | Powerline prompt. |
| tasks/proton.py | Proton applications. |
| tasks/samba.py | On-demand Samba file exchange. |
| tasks/scripts.py | User scripts and command links. |
| tasks/ssh_config.py | SSH client configuration. |
| tasks/ssh_keys.py | SSH keys and authorized keys. |
| tasks/sudo.py | Sudoers configuration. |
| tasks/syncthing.py | Syncthing. |
| tasks/system.py | Host/system configuration and hardening. |
| tasks/tmux.py | tmux configuration. |
| tasks/ufw.py | UFW firewall. |
| tasks/vpn.py | Conditional WireGuard activation. |
| tasks/vscodium.py | VSCodium extensions. |
| tasks/wireguard.py | WireGuard installation/configuration. |
| tasks/workstation/backup.py | Workstation backup tools. |
| tasks/workstation/cosmic/appearance.py | COSMIC theme appearance. |
| tasks/workstation/cosmic/config.py | COSMIC settings helpers. |
| tasks/workstation/cosmic/config_files.py | COSMIC config directory synchronization. |
| tasks/workstation/cosmic/deploy.py | COSMIC subtask orchestration. |
| tasks/workstation/cosmic/dock.py | COSMIC dock. |
| tasks/workstation/cosmic/input.py | COSMIC mouse/touchpad input. |
| tasks/workstation/cosmic/panel.py | COSMIC panel and applets. |
| tasks/workstation/cosmic/shortcuts.py | COSMIC shortcuts. |
| tasks/workstation/cosmic/window_management.py | COSMIC window-management preferences. |
| tasks/workstation/cosmic/workspaces.py | COSMIC workspace layout. |
| tasks/workstation/desktop.py | Desktop integration packages. |
| tasks/workstation/hardware.py | Firmware tools and CPU microcode. |
| tasks/workstation/limusic.py | LiMusic AppImage and launcher. |
| tasks/workstation/maintenance.py | Interactive maintenance tools. |
| tasks/workstation/peripherals.py | Printer/scanner support. |
| tasks/workstation/power.py | Workstation power manager. |
| tasks/workstation/storage.py | SMART/NVMe utilities. |
| tasks/zsh.py | Zsh and shell helper. |

## Configuration key index

The host schema is group_data/@local.py.example; the workstation schema is group_data/workstation.py.example. Copy them to ignored local files and customize them.

| Configuration keys | Purpose | Detailed reference |
| --- | --- | --- |
| hostname, username, usergroup, homedir | Host identity and user paths. | [Common settings](configuration.md#common-settings) |
| timezone, locale, keyboard, editor, visual_editor | OS defaults and environment. | [Common settings](configuration.md#common-settings), [System](system.md) |
| hostnames | Managed hosts-file mappings. | [Network](configuration.md#network-and-name-resolution) |
| local_network_cidr, wireguard_interface, wireguard_enabled, vpn_enabled, wireguard_config | WireGuard and VPN activation. | [Network](configuration.md#network-and-name-resolution) |
| apt_packages, apt_sources, flatpak_packages | Package sources and application IDs. | [Packages](configuration.md#packages-and-repositories) |
| sysctl, udev, usbguard, sudoers_rules | Kernel, device, USB and privilege policy. | [System](system.md) |
| ssh_keys, ssh_authorized_keys, ssh_authorized_keys_enabled, ssh_config | SSH identities, access and client defaults. | [SSH client configuration](configuration.md#ssh-client-configuration) |
| zsh, zshrc_imports, zplug_plugins, tmux, powerline, powerline_fonts | Shell, terminal and prompt. | [Optional user features](configuration.md#optional-user-and-desktop-features) |
| cron_jobs | Named user/root cron entries. | [Cron jobs](tasks.md#cron-jobs) |
| samba | On-demand LAN/VPN shares and idle timeout. | [Samba](samba.md) |
| syncthing | User-level Syncthing and GUI address. | [Syncthing](configuration.md#syncthing) |
| ufw | Firewall defaults and rules. | [Firewall](configuration.md#firewall) |
| docker_install, docker_power_monitor, docker, docker_power_save | Docker installation, services and battery-aware containers. | [Docker](docker.md) |
| docker_sablier | On-demand container sessions and provider strategy. | [Docker/Sablier](docker.md#optional-lifecycle-integrations) |
| caddy_config, caddy_enabled, caddy_versions | Reverse proxy and Caddy plugin. | [Docker](docker.md), [Caddy/Sablier](configuration.md#caddy-and-sablier) |
| dehydrated_auto_domains, dehydrated_zones, dehydrated_blacklist, dehydrated_wildcards | Certificate discovery/enrollment policy. | [Caddy/Sablier](configuration.md#caddy-and-sablier) |
| apparmor_profiles, apparmor_enabled | AppArmor profiles and master gate. | [System](system.md) |
| mullvad_extensions, mullvad_browser_dir, mullvad_browser_enabled | Browser extensions and policy location. | [Optional user features](configuration.md#optional-user-and-desktop-features) |
| vscodium, vscodium_enabled | VSCodium extensions and master gate. | [Optional user features](configuration.md#optional-user-and-desktop-features) |
| proton | Proton components and Drive CLI version. | [Optional user features](configuration.md#optional-user-and-desktop-features) |
| workstation | Opt-in workstation features and COSMIC subfeatures. | [Workstation role](configuration.md#workstation-role) |
| secrets.json.gpg | Host-scoped/shared credentials and private keys. | [Secrets](secrets.md) |

## Operational safety and idempotency

- Run a dry deployment and inspect the diff before applying changes.
- Keep real host data and secrets out of Git. Tracked .example files are templates, not production configuration.
- Review firewall, VPN, SSH, Samba, Docker socket and reverse-proxy changes for lockout or exposure risk.
- Tasks should check current state before changing it. An identical second deployment should not report changes or restart services without a real reason.
- Docker persistence uses explicit host bind mounts below the configured home directory's .docker/; Docker-managed named volumes are not used.
- Installing backup tools is not a backup strategy: configure repositories, encryption credentials, schedules and restore tests separately.
- A dry run is a planning aid, not rollback. Back up important state and retain console/out-of-band access for network changes.

## Related guides

- [Architecture](architecture.md) — repository structure and runtime lifecycle.
- [Host configuration](configuration.md) — field-level host and role settings.
- [Deployment](deployment.md) — preview and apply.
- [Task reference](tasks.md) — detailed task behavior and examples.
- [Docker](docker.md) — service ports, storage and lifecycle.
- [Secrets](secrets.md) — encrypted credential schema and tools.
- [Templates](templates.md) — generated files and static payloads.
- [Development](development.md) — tests, linting and contribution workflow.
