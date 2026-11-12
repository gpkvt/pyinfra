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
| `tasks/docker.py` and `tasks/docker_container.py` | `docker` | Installs Docker, defines the shared Compose/systemd deployment helper, and dispatches configured container services. |
| `tasks/docker_sablier.py` | `docker` and `docker_sablier.enabled` | Installs Sablier as a user systemd service and enables on-demand startup for matching Caddy routes. It uses the custom Caddy handler deployed by `tasks/caddy.py` and is mutually exclusive with the Docker battery monitor. |
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

`tasks/ufw.py` supports the `chromecast-dlna`, `kdeconnect` and `localsend` application profiles plus `ssh` (TCP port 22). These entries accept `Allow` or `Deny` string values. Additional custom rules use a dictionary with an `action` and a `rule` string containing UFW arguments. Existing custom rules are read from `ufw show added` and compared before changes, including normalization of the optional `in` token, to keep deployments idempotent. Invalid entries are ignored. The task sets default incoming policy to deny and outgoing policy to allow, applies configured rules, and then enables UFW. Review firewall changes and ensure a recovery path before applying them remotely; the supplied local configuration sets `ssh` to `Deny`.

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
- A changed Compose file triggers `docker compose pull`; a changed Compose file or systemd unit triggers a service restart. The systemd unit stops the Compose project with `docker compose down` and starts it with `docker compose up -d`, recreating its containers. Service tasks can also register additional restart triggers for generated assets; Homepage's container is recreated when its synchronized public icons change.
- An unchanged Compose file does not trigger an image pull. Image updates therefore require a configuration change or a separate manual pull.

**Available services**

Most existing services use host-directory mounts. Linkwarden uses Docker-managed local named volumes whose backing directories are explicitly located under `~/.docker/linkwarden/`. The paths below are relative to the configured user's home directory.

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
| Linkwarden | `~/.docker/linkwarden/postgres/`, `~/.docker/linkwarden/data/`, `~/.docker/linkwarden/meili/` | `127.0.0.1:8021` |
| WG-Easy | `~/.docker/wg-easy/` (Docker local named volume) | UI: `127.0.0.1:51821`; WireGuard: UDP `51820` |
| Paperless-ngx | `~/.docker/paperless/postgres/`, `data/`, `media/`, `consume/`, `export/` | `127.0.0.1:8022` |
| Snipe-IT | `~/.docker/snipe-it/database/`, `storage/` (Docker local named volumes) | `127.0.0.1:8025` |

**Service-specific notes**

- **Paperless-ngx** runs with PostgreSQL 17, Valkey, Gotenberg and Tika. PostgreSQL data and Paperless data, media, consume and export directories are host bind mounts under `~/.docker/paperless/`; no Docker named volumes are used. The directories are created idempotently with PostgreSQL ownership `70:70` and Paperless ownership controlled by `docker.paperless.uid` / `gid` (defaults to `1000:1000`). Its web interface binds to `127.0.0.1:8022` and the supplied local Caddy configuration publishes `paperless.21x9.org`. Store `postgres_password` (URL-safe) and `secret_key` under `secrets.docker.paperless` in the encrypted secrets file. Generate a strong secret key and do not leave the example placeholders in place.

- **Firefly III** runs with MariaDB, an Alpine cron container and the FinTS importer. The application binds to `127.0.0.1:8023` (`firefly.21x9.org`) and the importer UI to `127.0.0.1:8024` (`fints.21x9.org`). Database files, Firefly uploads and importer configurations are host bind mounts under `~/.docker/firefly-iii/`; no named volumes are used. Store `database_password`, `mysql_root_password`, `app_key` and the exactly 32-character `cron_token` under `secrets.docker.firefly-iii` in the encrypted secrets file. Use a Laravel-compatible application key (for example, a `base64:`-prefixed 32-byte key). The importer is the community `benkl/firefly-iii-fints-importer` image; after first start, open its UI, set the Firefly III URL to `http://app:8080` from within the Compose network, and provide a Firefly III personal access token. The importer stores its bank connection configurations under `~/.docker/firefly-iii/fints/`. FinTS authentication data is sensitive; protect access to the importer hostname and host directory accordingly.


- **Snipe-IT** runs with MariaDB 11.4 and the official `snipe/snipe-it` image. Its database and application storage use Docker-managed local named volumes backed by `~/.docker/snipe-it/database/` and `~/.docker/snipe-it/storage/`; no direct host-path mounts are declared in Compose. The directories are prepared idempotently with MariaDB ownership `999:999` and Snipe-IT ownership `10000:50`. The application binds to `127.0.0.1:8025` and the supplied local Caddy hostname is `snipeit.21x9.org`. Store `database_password`, `mysql_root_password` and a generated Laravel `app_key` under `secrets.docker.snipe-it` in the encrypted secrets file. Generate the key with `docker compose run --rm app php artisan key:generate --show`; keep the same key for the lifetime of the installation.
- **Miniflux** uses a PostgreSQL companion container. Its database is persisted in `~/.docker/miniflux/db/`; administrator and database credentials are read from `secrets.docker.miniflux`.
- **TimeTagger** stores its data in `~/.docker/timetagger/`, mounted at the container's `/root/_timetagger` directory.
- **Grav** persists the complete web application data directory in `~/.docker/grav/data/`. Its `setup`, `scheduler` and `fix_permissions` options are configurable.
- **Forgejo** persists application data in `~/.docker/forgejo/data/`. Its web and SSH ports bind to loopback by default; the public domain is configurable.
- **Portainer** persists data in `~/.docker/portainer/data/` and mounts `/var/run/docker.sock`. Access to Portainer effectively grants administrative control over the Docker host; expose it only through a trusted, authenticated reverse proxy.
- **TasmoAdmin** mounts `~/.docker/tasmoadmin/data/` at `/data/tasmoadmin`, matching its `TASMO_DATADIR` setting.
- **Wallabag** uses SQLite and persists its database/application data and article images in the two host directories shown above. The directories are mounted into the container paths used by Wallabag's `www-data` process. The supplied local Caddy configuration publishes it as `wallabag.21x9.org`; the initial credentials are `wallabag` / `wallabag`, which must be changed after first login.
- **Vaultwarden** persists its data in `~/.docker/vaultwarden/`. Public signups and invitations are disabled. An optional Argon2 PHC admin-token hash is read from `secrets.docker.vaultwarden.admin_token`; generate it with `docker run --rm -it vaultwarden/server:latest /vaultwarden hash`. Its supplied local Caddy hostname is `vaultwarden.21x9.org`.
- **NocoDB** persists application data in `~/.docker/nocodb/data/`, mounted at `/usr/app/data`. Its HTTP interface binds to loopback on port `8019` by default; the supplied local Caddy hostname is `nocodb.21x9.org`.
- **Linkwarden** uses PostgreSQL 16 and Meilisearch alongside the application. Three Docker-managed local named volumes store PostgreSQL data, Linkwarden archives/uploads and the Meilisearch index in `~/.docker/linkwarden/postgres/`, `~/.docker/linkwarden/data/` and `~/.docker/linkwarden/meili/`, respectively. Its web interface binds to loopback on port `8021`; the supplied local Caddy hostname is `linkwarden.21x9.org`. Database, NextAuth and Meilisearch secrets are read from `secrets.docker.linkwarden`; use distinct, URL-safe values for all three secrets. `NEXTAUTH_URL` is generated as `https://linkwarden.21x9.org/api/v1/auth` (or the configured domain). The local named volumes use the Docker local volume driver with host directories under `~/.docker/`, rather than direct host-path volume entries in the service definitions.
- **WG-Easy** stores WireGuard configuration in a Docker-managed local named volume backed by `~/.docker/wg-easy/`; it publishes UDP `51820` for VPN traffic and binds its administration UI to `127.0.0.1:51821`. The UI is reverse-proxied through Caddy at `vpn.21x9.org`. Complete the initial setup wizard to set the public endpoint to `vpn.21x9.org` and create the administrator account. `INSECURE=true` is set only for the HTTP connection between the container and the local Caddy reverse proxy; do not publish the UI port directly.
- **Homepage** stores its configuration in `~/.docker/homepage/config/`, mounted at `/app/config`. It binds to loopback on port `8020` and sets `HOMEPAGE_ALLOWED_HOSTS` to the configured hostname; the supplied local Caddy hostname is `homepage.21x9.org`. Optional host-data keys `settings`, `services`, `bookmarks`, `widgets`, `docker`, `kubernetes` and `proxmox` are rendered to their matching `*.yaml` files. Each file is rendered only when its key is present; omitted sections are left untouched. The supplied `group_data/@local.py` includes service links to locally deployed applications and grouped bookmarks. Bookmark categories include Misc (GitHub, Kachelmannwetter, dict.leo, docsbot and lookscanned), Social (Reddit, Mastodon, Discord and LinkedIn), Entertainment (YouTube, Last.fm and Letterboxd), and Proton (Mail, Calendar, Drive, Docs, Sheets, VPN, Pass, Authenticator, Wallet, Meet and Lumo). Icons are referenced as local files under `/icons/`; they are not fetched from third-party favicon URLs at dashboard runtime. The icons are stored in `files/homepage/icons/` and synchronized idempotently to `~/.docker/homepage/public/icons/`; synchronization does not delete destination files, so local-only icons are preserved. Homepage is restarted only when this synchronization changes files, ensuring newly deployed icons are picked up without causing unnecessary restarts on unchanged runs. The public asset directories use mode `0755`; icon synchronization does not enforce per-file ownership or permissions, avoiding repeated metadata changes if the Homepage container adjusts mounted asset metadata. The Compose service mounts the icon and image directories separately at `/app/public/icons` and `/app/public/images`. Set each service's `icon` to a path such as `/icons/miniflux.png`. Configure the dashboard background under `docker.homepage.settings.background`; the local example uses the official Homepage sample image hosted by Unsplash. Replace the URL or use a local image such as `/images/background.jpg` stored in `~/.docker/homepage/public/images/`. Homepage also supports `blur`, `saturate` and `brightness` background options. The local example configures `settings.layout.Services` with `style: row` and `columns: 3`, arranging service cards in three columns. Adjust the column count in host data to suit the display. Docker socket access is not enabled by default. Homepage dashboards may expose sensitive widget data, so protect access with a trusted reverse proxy authentication policy, Homepage authentication, or a VPN.

Homepage supports two distinct widget types: service widgets are configured inside each service entry in services.yaml, while header/info widgets are configured in widgets.yaml. Both are supplied through the docker.homepage.services and docker.homepage.widgets host-data keys. The local example enables:
- **FRITZ!Box** status, uptime and transfer rates at 192.168.42.1. Enable *Allow access for applications* and *Transmit status information over UPnP* in the FRITZ!Box network settings. The widget does not require credentials and supports at most four fields.
- **Miniflux** unread/read article counts. Create an API key under Miniflux Settings → API keys.
- **Forgejo** repository, notification, issue and pull-request counts using Homepage's Gitea-compatible widget. Create an API token with notifications, repository and issue permissions.
- **Portainer** running/stopped/total container counts. Create an API access token and verify the environment ID (1 in the supplied example) in Portainer.
- **OpenWeatherMap** current weather and forecast for Cologne, Germany, configured with metric units and a five-minute cache. Homepage reads the API key from the shared `settings.providers.openweathermap` entry, which resolves `HOMEPAGE_VAR_OPENWEATHERMAP_API_KEY` from the container environment. Store the key under `secrets.docker.homepage.environment` in `secrets.json.gpg`; an OpenWeatherMap One Call API subscription/key is required. See the [OpenWeatherMap widget documentation](https://gethomepage.dev/widgets/info/openweathermap/).
- **Glances** host metrics (CPU, memory, CPU temperature, uptime and the `/` filesystem). The Homepage task manages a system-level `glances-web.service` running as the configured deployment user; this avoids depending on an interactive user session or user D-Bus. When the unit changes, it restarts the service and removes only a stale Glances web-server process matching the configured user, bind address and port before starting the managed instance; the separate Glances server mode (`-s`) is not affected. Glances listens on Docker's host-gateway address (default `172.17.0.1:61208`) and is reached using the Compose `host.docker.internal:host-gateway` mapping. The Homepage network's own gateway (for example `172.27.0.1`) is not the address used by `host.docker.internal`. UFW access is managed centrally through the `ufw` configuration in `group_data/@local.py`: `docker-host-glances` allows the Homepage Docker subnet (`172.27.0.0/16`) to reach the Glances listener at the Docker host-gateway address (`172.17.0.1:61208`). The Homepage task does not add firewall rules itself. The API port is not published by Compose or opened to arbitrary source networks. If the Docker subnet, host-gateway address, Glances bind address or port changes, update the corresponding custom UFW rule to match `docker.homepage.glances.bind_address` and `docker.homepage.glances.port`.
- A date/time widget using the German locale and 24-hour time format, and DuckDuckGo search. CPU, memory and filesystem metrics are provided by Glances to avoid duplicate resource displays.

The Miniflux, Forgejo and Portainer service widgets use their public HTTPS hostnames (`rss.21x9.org`, `forgejo.21x9.org` and `portainer.21x9.org`) as API URLs. The Homepage Compose template maps these names to Docker's `host-gateway` address with `extra_hosts`; this prevents container DNS from resolving a public hostname to the host's loopback address (`127.0.0.1`). Caddy receives the HTTPS requests on the host gateway and routes them by hostname to the services bound to host loopback ports. Keep Caddy reachable on the host-gateway interface on port 443. The `host.docker.internal` mapping remains available separately for host services such as Glances. Homepage substitutes `{{HOMEPAGE_VAR_*}}` placeholders from its environment. The example `secrets.json.gpg.example` documents `HOMEPAGE_VAR_MINIFLUX_API_KEY`, `HOMEPAGE_VAR_FORGEJO_API_KEY`, `HOMEPAGE_VAR_PORTAINER_API_KEY` and `HOMEPAGE_VAR_OPENWEATHERMAP_API_KEY` under `hosts.@local.docker.homepage.environment`; `tasks/docker/homepage.py` merges this secret mapping into the container environment, with secret values taking precedence. Keep the actual API keys only in the encrypted secrets file, never in `@local.py`. The Portainer widget's `env: 1` refers to the example environment ID; change it if the Portainer environment has a different ID.

**Optional integrations:** Homepage also supports widgets for WGEasy, Grafana, Home Assistant and Paperless-ngx. These applications are not deployed by this repository's Docker service tasks (Grafana, Home Assistant and Paperless-ngx are referenced only as external LAN services; WG-Easy is deployed by this repository, but its Homepage widget is not enabled in the supplied local configuration). Add them as service entries only when the corresponding application is reachable from the Homepage container. For WGEasy v15 and newer, use widget type wgeasy, version 2, and the configured username/password; older releases use API version 1. See the [WGEasy widget documentation](https://gethomepage.dev/widgets/services/wgeasy/). The FRITZ!Box, Miniflux, Forgejo/Gitea and Portainer widget schemas are documented in the [Homepage service widget reference](https://gethomepage.dev/widgets/services/).

Example optional service entries (add them to a group in docker.homepage.services and replace the URLs and credentials with values reachable from the Homepage container):

```python
{
    "WG-Easy": {
        "href": "https://wg-easy.example.org",
        "widget": {
            "type": "wgeasy",
            "url": "http://wg-easy:51821",
            "version": 2,  # WGEasy v15+
            "username": "{{HOMEPAGE_VAR_WGEASY_USERNAME}}",
            "password": "{{HOMEPAGE_VAR_WGEASY_PASSWORD}}",        },
    },
},
{
    "Grafana": {
        "href": "https://grafana.example.org",
        "widget": {
            "type": "grafana",
            "version": 2,  # Grafana > 10.4
            "url": "http://grafana:3000",
            "username": "{{HOMEPAGE_VAR_GRAFANA_USERNAME}}",
            "password": "{{HOMEPAGE_VAR_GRAFANA_PASSWORD}}",
        },
    },
},
{
    "Home Assistant": {
        "href": "https://ha.example.org",
        "widget": {
            "type": "homeassistant",
            "url": "http://homeassistant:8123",
            "key": "{{HOMEPAGE_VAR_HOME_ASSISTANT_TOKEN}}",
        },
    },
},
{
    "Paperless-ngx": {
        "href": "https://paperless.example.org",
        "widget": {
            "type": "paperlessngx",
            "url": "http://paperless:8000",
            "key": "{{HOMEPAGE_VAR_PAPERLESS_TOKEN}}",
            "fields": ["total", "inbox"],
        },
    },
},
```

The local Homepage configuration declares the Miniflux, Forgejo and Portainer API-key environment variables with empty defaults. Store their actual values in `secrets.docker.homepage.environment` in `secrets.json.gpg`; `tasks/docker/homepage.py` merges that mapping over `docker.homepage.environment`, so secret values always take precedence. Do not put real credentials in tracked host-data files. For WGEasy v15 and newer, use widget type wgeasy and version 2; older releases use API version 1. See the [WGEasy widget documentation](https://gethomepage.dev/widgets/services/wgeasy/), [Grafana](https://gethomepage.dev/widgets/services/grafana/), [Home Assistant](https://gethomepage.dev/widgets/services/homeassistant/) and [Paperless-ngx](https://gethomepage.dev/widgets/services/paperlessngx/) documentation.

Header widgets and service widgets can expose network and application data. Keep Homepage behind trusted authentication, a VPN, or an authenticated reverse proxy. API keys must have only the permissions needed for read-only dashboard access.


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


### On-demand Docker services

On-demand startup is controlled by `docker_sablier`. The supplied local configuration enables Sablier with a 60-minute default session and a five-minute Caddy blocking timeout. Only reverse-proxy routes whose loopback port matches a configured Docker service are wrapped; unmatched Caddy routes remain unchanged.

Each managed Docker systemd unit opts in through an `[X-Sablier]` section. The default group is the Docker service name. Firefly III's web, cron and FinTS routes share the `firefly-iii` group.

Per-service overrides are configured under the matching `docker.<service>` entry:

```python
docker = {
    "linkwarden": {
        # Other Linkwarden settings...
        "sablier": {"enabled": False},  # Keep this service always running.
    },
    "paperless": {
        # Other Paperless settings...
        "sablier": {"stop_dependencies": False},
    },
}
```

By default, Sablier stops the complete Compose project after the session expires. Set `stop_dependencies=False` globally or per service to stop only the application containers and leave databases and other dependencies running. Application service names are declared by the service tasks.

Sablier uses the configured user's systemd manager. The task enables lingering so that manager remains available after logout. Caddy is built separately with the Sablier handler and selected through a systemd override; the APT-managed `/usr/bin/caddy` is not replaced. Disabling `docker_sablier.enabled` removes the override and restores the packaged Caddy binary.

Sablier and the Docker battery saver are mutually exclusive. When Sablier is enabled, the battery monitor is stopped and disabled, and containers previously stopped by the battery saver are restored first. Disabling Sablier re-enables the battery monitor.
