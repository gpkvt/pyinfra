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
| `tasks/ssh_config.py` | `ssh_config` | Renders the user's SSH client configuration with a hardened global baseline followed by configured host entries. | `ssh_config` |
| `tasks/wireguard.py` | `wireguard_config` and `secrets.wireguard` | Installs WireGuard and writes `/etc/wireguard/<interface>.conf`; does not start the service. | `wireguard_config` |
| `tasks/vpn.py` | `local_network_cidr` and `wireguard_interface` | Enables/starts `wg-quick@<interface>` when the host is outside the configured IPv4 network. | `local_network_cidr`, `wireguard_interface` |
| `tasks/dehydrated.py` | `secrets.dehydrated` | Configures dehydrated for ACME certificate management and deploys its hook. | `secrets.dehydrated` |
| `tasks/caddy.py` | `caddy_config` | Deploys Caddy configuration from host data. | `caddy_config` |
| `tasks/syncthing.py` | `syncthing` | Installs Syncthing, enables `syncthing@<username>`, and configures its GUI listen address (loopback by default). Device and folder sharing is configured separately in Syncthing. | `syncthing` |
| `tasks/zsh.py` | `zsh` | Installs/configures Zsh and related user configuration. | `zsh` |
| `tasks/tmux.py` | `tmux` | Deploys tmux configuration. | `tmux` |
| `tasks/powerline.py` | `powerline` | Deploys Powerline prompt configuration. | `powerline` |
| `tasks/ufw.py` | `ufw` | Applies configured UFW application policies. | `ufw` |
| `tasks/docker.py` and `tasks/docker_container.py` | `docker` | Installs Docker, defines the shared Compose/systemd deployment helper, and dispatches configured Miniflux, TimeTagger, Grav, Forgejo, Portainer, TasmoAdmin, Wallabag, Vaultwarden, NocoDB and Homepage services. | `docker` |
| `tasks/apparmor.py` | `apparmor_profiles` | Loads/enforces configured AppArmor profiles. | `apparmor_profiles` |
| `tasks/cosmic/deploy.py` | `cosmic` | Deploys COSMIC desktop configuration and assets. | `cosmic` |
| `tasks/mullvad_extensions.py` | `mullvad_extensions` | Downloads configured browser extensions and deploys `user.js`. | `mullvad_extensions` |
| `tasks/vscodium.py` | `vscodium` | Installs/configures VSCodium extensions. | `vscodium` |
| `tasks/proton.py` | `proton` | Installs/configures selected Proton applications using the configured distribution sources. | `proton` |

## Feature notes

### Homepage Glances widget

When `docker.homepage.glances` is configured, the Homepage task manages a system-level `glances-web.service` running as the configured deployment user. This avoids depending on an interactive user session or user D-Bus. The service listens on the Docker host-gateway address (default `172.17.0.1`) and Homepage reaches it through the Compose `host.docker.internal:host-gateway` mapping. The Homepage network's own gateway (for example `172.27.0.1`) is not the address used by `host.docker.internal`.

When UFW is installed, the task discovers the subnet of the `homepage_default` Compose network and adds an allow rule for that source subnet, the configured Glances bind address and port. The rule is checked before it is added, so unchanged deployments do not add duplicate rules. The API port is not published by Compose and is not opened to arbitrary source networks. If the Homepage network does not exist yet (for example during its first deployment), the firewall rule is skipped and will be configured on the next deployment after Compose has created the network.

The listener address and port are configurable through `docker.homepage.glances.bind_address` and `docker.homepage.glances.port`. Keep the bind address aligned with Docker's configured `host-gateway` address if that daemon setting is customized.

### UFW firewall

`tasks/ufw.py` supports the `chromecast-dlna`, `kdeconnect` and `localsend` application profiles plus `ssh` (TCP port 22). Each configured value must be `Allow` or `Deny`; unsupported keys and values are ignored. The task sets default incoming policy to deny and outgoing policy to allow, applies configured rules, and then enables UFW. Review the resulting policy before applying it remotely. The supplied `group_data/@local.py` currently sets `ssh` to `Deny`, so do not copy that policy to a remotely managed host without a separate recovery path.

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

### Homepage configuration and widgets

Homepage configuration is stored in `~/.docker/homepage/config/`; optional host-data keys `settings`, `services`, `bookmarks`, `widgets`, `docker`, `kubernetes` and `proxmox` are rendered to their matching YAML files. Each file is rendered only when its key is present. Homepage's header widgets and service widgets are configured separately. The local example includes FRITZ!Box, Miniflux, Forgejo, Portainer and Glances widgets. Keep API credentials in the encrypted secrets file rather than tracked host data. Homepage dashboards may expose sensitive widget data, so protect access with trusted authentication, a VPN, or an authenticated reverse proxy.

