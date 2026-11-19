# Docker services

Deploy and operate containerized applications with a shared Compose and systemd workflow. Each service is opt-in through `host.data.docker`; persistent state lives in the configured user's home directory.

<div class="docker-stats">
<div class="docker-stat"><span class="docker-stat-value">18</span><span class="docker-stat-label">documented services</span></div>
<div class="docker-stat"><span class="docker-stat-value">~/.docker/</span><span class="docker-stat-label">persistent host storage</span></div>
<div class="docker-stat"><span class="docker-stat-value">127.0.0.1</span><span class="docker-stat-label">default web binding</span></div>
<div class="docker-stat"><span class="docker-stat-value">systemd</span><span class="docker-stat-label">user service lifecycle</span></div>
</div>

## Service catalog

The ports below are the documented defaults. Web interfaces generally bind to loopback and are intended to be published through the configured reverse proxy. AdGuard Home uses host networking; WG-Easy additionally publishes its WireGuard UDP endpoint.

| Service | Default host endpoint | Persistent host data |
| --- | --- | --- |
| Miniflux | `127.0.0.1:8080` | `miniflux/db/` |
| TimeTagger | `127.0.0.1:8080` | `timetagger/` |
| Grav | `127.0.0.1:8080` | `grav/data/` |
| Forgejo | Web `127.0.0.1:8027`, SSH `127.0.0.1:2222` | `forgejo/data/` |
| Portainer | `127.0.0.1:9000` | `portainer/data/` |
| TasmoAdmin | `127.0.0.1:8016` | `tasmoadmin/data/` |
| Wallabag | `127.0.0.1:8017` | `wallabag/data/`, `wallabag/images/` |
| Vaultwarden | `127.0.0.1:8018` | `vaultwarden/` |
| NocoDB | `127.0.0.1:8019` | `nocodb/data/` |
| Homepage | `127.0.0.1:8020` | `homepage/config/` |
| Linkwarden | `127.0.0.1:8021` | `linkwarden/postgres/`, `data/`, `meili/` |
| WG-Easy | UI `:51821`, WireGuard UDP `:51820` | `wg-easy/` |
| Paperless-ngx | `127.0.0.1:8022` | `paperless/postgres/`, `data/`, `media/`, `consume/`, `export/` |
| Firefly III | App `127.0.0.1:8023`, FinTS `:8024` | `firefly-iii/` |
| Snipe-IT | `127.0.0.1:8025` | `snipe-it/database/`, `storage/` |
| AppFlowy | `127.0.0.1:8026` | `appflowy/postgres/`, `minio/`, `search/` |
| MDMesh | `127.0.0.1:8030` | `mdmesh/postgres/`, `server/`, `caddy/`, `backups/` |
| AdGuard Home | Host network; DNS TCP/UDP `:53`, setup `:3000` | `adguard_home/conf/`, `work/` |

All paths in the table are relative to `~/.docker/`. Services use host-directory bind mounts; Docker-managed named volumes are not used. Some supporting containers intentionally use ephemeral storage (for example, AppFlowy's Redis queue).

## How deployment works

<div class="docker-flow">
<div><b>01 · Configure</b><p>Add the service key below <code>docker</code> in host data. Secrets belong in the encrypted secrets file.</p></div>
<div><b>02 · Render</b><p>Compose is written to <code>~/.docker/&lt;service&gt;/docker-compose.yml</code>; its user systemd unit is written under <code>~/.config/systemd/user/</code>.</p></div>
<div><b>03 · Reconcile</b><p>Changed Compose configuration triggers an image pull and service reconciliation. Unchanged files do not cause an image pull.</p></div>
<div><b>04 · Operate</b><p>systemd manages start, restart and stop. Registered assets can trigger a restart only when they actually change.</p></div>
</div>

- Enable Docker services by setting `docker` to a truthy mapping. `tasks/docker.py` installs Docker and defines the shared deployment helper; `tasks/docker_container.py` dispatches configured service modules.
- Compose projects run as the configured user. Without Sablier, deployment uses `docker compose up -d`; with Sablier, it prepares containers using `docker compose up --no-start`.
- `stop_dependencies` controls whether stopping a systemd unit stops the complete Compose project or only its configured `app_services`.
- Image updates are change-triggered. To update an image without changing configuration, run an intentional manual pull for that service.
- Service modules can register extra restart triggers for generated assets. Homepage, for example, is restarted when synchronized public icons change.

## Storage and security

<div class="docker-info-grid">
<div class="docker-info-card">
<strong><code>~/.docker/&lt;service&gt;/</code></strong>
<p>Compose files, environment files and persistent application data stay grouped per service.</p>
</div>
<div class="docker-info-card">
<strong>Host bind mounts only</strong>
<p>Data is visible and backup-friendly on the host. No Docker-managed named volumes are used.</p>
</div>
<div class="docker-info-card">
<strong>Encrypted secrets</strong>
<p>Passwords, API keys and signing secrets belong in <code>secrets.json.gpg</code>, not tracked host data.</p>
</div>
<div class="docker-info-card">
<strong>Loopback by default</strong>
<p>Publish web interfaces through a trusted reverse proxy or VPN rather than exposing container ports publicly.</p>
</div>
</div>

!!! warning "Before enabling a service"
    Check for existing listeners and reverse-proxy routes, configure strong secrets, and review the Compose template. Portainer, MDMesh's supervisor and other Docker-socket consumers can control the Docker host and must be treated as privileged components.

## Optional lifecycle integrations

### Sablier

Sablier can start or resume labelled application containers on demand. It is enabled separately with `docker_sablier.enabled`; the tracked example disables it. Dynamic mode serves a waiting page while a service starts. The default provider strategy is `pause`, which preserves memory usage while idle; `stop` releases memory but causes a cold start. Sablier and the Docker battery monitor are mutually exclusive.

### Docker Power

The optional battery monitor can stop configured containers to reduce power use. When Sablier is enabled, the monitor is disabled and containers it previously stopped are restored. See [Task reference](tasks.md#docker-services) for the task gates and implementation details.

## Service configuration and operational notes

The task reference explains Homepage widgets, Linkwarden bookmark synchronization, Caddy/Dehydrated integration, AdGuard setup, MDMesh bootstrap behavior, service secrets and per-service configuration.

??? info "Detailed service notes and integration configuration"
    **Service-specific notes**

    - **MDMesh** is an Android-only MDM (it does not manage Linux endpoints) and is optional: it is deployed only when `docker.mdmesh.domain` is configured; leave the key unset to skip it. It deploys the upstream PostgreSQL 14, server, web-edge and supervisor images at the resolved `docker.mdmesh.version` (defaults to `"latest"`; a semantic version can be pinned). The web edge binds only to `127.0.0.1:8030` by default; add the public hostname to `caddy_config`, for example `"mdm.example.com:443": {"reverse_proxy": "127.0.0.1:8030"}`, so the existing Caddy instance terminates HTTPS. Set `docker.mdmesh.domain` to the same hostname. All persistent data, including PostgreSQL, server state, Caddy state/configuration and supervisor backups, uses host bind mounts under `~/.docker/mdmesh/`; there are no Docker-managed named volumes. Store `database_password`, `hash_secret` and `admin_password` under `secrets.docker.mdmesh` in the encrypted secrets file; each must be at least 32 characters and must not contain quotes, backslashes or line breaks. The initial administrator is `admin_email` (default `admin@<domain>`) and must change the configured initial password at first sign-in. The task downloads the database seed and repair scripts from the same tagged MDMesh release, seeds only a fresh database, refuses an inconsistent database, and checks enrollment defaults before skipping the bootstrap operation on later runs. The supervisor mounts the Docker socket and can control host containers; treat it as a privileged component. Set `trusted_proxies` only to the actual CIDRs used by the existing reverse proxy. MDMesh's signed release/update mechanism is retained, but automatic updates are disabled; with `version: "latest"`, the task resolves the latest stable release on each deployment and reconciles the images and bootstrap assets together. Pin a semantic version when a fixed release is required. Sablier is forcibly disabled for MDMesh, even when the global integration or a per-service opt-in is enabled: Android devices need an always-available management endpoint, and Sablier's lazy-start preparation leaves its containers created but stopped.
    - **AppFlowy** deploys the current AppFlowy Self-Hosted Commercial Compose stack (Cloud, GoTrue, PostgreSQL/pgvector, Redis, MinIO, AI, Worker, Search, Web, Admin and Nginx). Nginx binds only to `127.0.0.1:8026` and Caddy publishes `appflowy.21x9.org`. PostgreSQL, MinIO and Search data use direct bind mounts under `~/.docker/appflowy/`; no Docker-managed named volumes are used. The task renders a private `~/.docker/appflowy/.env` (mode `0600`) from encrypted `secrets.docker.appflowy` values. Set `postgres_password`, `admin_password`, `jwt_secret`, `minio_access_key` and `minio_secret_key`; URL-interpolated secrets must use the documented URL-safe formats. Change the initial administrator password after first login. Cloud uses `APPFLOWY_REDIS_URI`, AI uses `AI_REDIS_URL`, Worker uses `APPFLOWY_WORKER_REDIS_URL`, and Search receives both `APPFLOWY_INDEXER_REDIS_URL` and `APPFLOWY_SEARCH_REDIS_URL`, mapped to the same Compose `redis` service endpoint rather than container-local `localhost`. Redis follows the upstream ephemeral configuration and has no persistent data mount or AOF; pending queue state may not survive Redis replacement. AppFlowy Self-Hosted Commercial is distributed under AppFlowy's commercial self-hosted license; review its terms before deployment. Homepage receives only a normal link, not an API widget or authenticated exporter.

    - **Paperless-ngx** runs with PostgreSQL 17, Valkey, Gotenberg and Tika. PostgreSQL data and Paperless data, media, consume and export directories are host bind mounts under `~/.docker/paperless/`; no Docker named volumes are used. The directories are created idempotently with PostgreSQL ownership `70:70` and Paperless ownership controlled by `docker.paperless.uid` / `gid` (defaults to `1000:1000`). Its web interface binds to `127.0.0.1:8022` and the supplied local Caddy configuration publishes `paperless.21x9.org`. Store `postgres_password` (URL-safe) and `secret_key` under `secrets.docker.paperless` in the encrypted secrets file. Generate a strong secret key and do not leave the example placeholders in place. The host import directory `~/Paperless` is a symlink to `~/.docker/paperless/consume`; place documents there to import them.

    - **Firefly III** runs with MariaDB, an Alpine cron container and the FinTS importer. The application binds to `127.0.0.1:8023` (`firefly.21x9.org`) and the importer UI to `127.0.0.1:8024` (`fints.21x9.org`). Database files, Firefly uploads and importer configurations are host bind mounts under `~/.docker/firefly-iii/`; no named volumes are used. Store `database_password`, `mysql_root_password`, `app_key` and the exactly 32-character `cron_token` under `secrets.docker.firefly-iii` in the encrypted secrets file. Use a Laravel-compatible application key (for example, a `base64:`-prefixed 32-byte key). The importer is the community `benkl/firefly-iii-fints-importer` image; after first start, open its UI, set the Firefly III URL to `http://app:8080` from within the Compose network, and provide a Firefly III personal access token. The importer stores its bank connection configurations under `~/.docker/firefly-iii/fints/`. FinTS authentication data is sensitive; protect access to the importer hostname and host directory accordingly.


    - **Snipe-IT** runs with MariaDB 11.4 and the official `snipe/snipe-it` image. Its database and application storage use direct host bind mounts from `~/.docker/snipe-it/database/` and `~/.docker/snipe-it/storage/`, respectively. The backing directories are prepared idempotently with MariaDB ownership `999:999` and Snipe-IT ownership `10000:50`. The application binds to `127.0.0.1:8025` and the supplied local Caddy hostname is `snipeit.21x9.org`. Store `database_password`, `mysql_root_password` and a generated Laravel `app_key` under `secrets.docker.snipe-it` in the encrypted secrets file. Generate the key with `docker compose run --rm app php artisan key:generate --show`; keep the same key for the lifetime of the installation.
    - **Miniflux** uses a PostgreSQL companion container. Its database is persisted in `~/.docker/miniflux/db/`; administrator and database credentials are read from `secrets.docker.miniflux`.
    - **TimeTagger** stores its data in `~/.docker/timetagger/`, mounted at the container's `/root/_timetagger` directory.
    - **Grav** persists the complete web application data directory in `~/.docker/grav/data/`. Its `setup`, `scheduler` and `fix_permissions` options are configurable.
    - **Forgejo** persists application data in `~/.docker/forgejo/data/`. Its web and SSH ports bind to loopback by default; the public domain is configurable. The HTTP host port defaults to `8027` while the container continues listening on `3000`. Override it with `docker.forgejo.port` if needed, and point the corresponding Caddy `reverse_proxy` to the same loopback host port (for example `127.0.0.1:8027`). Existing explicit `port: 3000` host settings are not migrated automatically; update that setting and the Caddy route together to resolve a conflict.
    - **Portainer** persists data in `~/.docker/portainer/data/` and mounts `/var/run/docker.sock`. Access to Portainer effectively grants administrative control over the Docker host; expose it only through a trusted, authenticated reverse proxy.
    - **TasmoAdmin** mounts `~/.docker/tasmoadmin/data/` at `/data/tasmoadmin`, matching its `TASMO_DATADIR` setting.
    - **Wallabag** uses SQLite and persists its database/application data and article images in the two host directories shown above. The directories are mounted into the container paths used by Wallabag's `www-data` process. The supplied local Caddy configuration publishes it as `wallabag.21x9.org`; the initial credentials are `wallabag` / `wallabag`, which must be changed after first login.
    - **Vaultwarden** persists its data in `~/.docker/vaultwarden/`. Public signups and invitations are disabled. An optional Argon2 PHC admin-token hash is read from `secrets.docker.vaultwarden.admin_token`; generate it with `docker run --rm -it vaultwarden/server:latest /vaultwarden hash`. Its supplied local Caddy hostname is `vaultwarden.21x9.org`.
    - **NocoDB** persists application data in `~/.docker/nocodb/data/`, mounted at `/usr/app/data`. Its HTTP interface binds to loopback on port `8019` by default; the supplied local Caddy hostname is `nocodb.21x9.org`.
    - **Linkwarden** uses PostgreSQL 16 and Meilisearch alongside the application. Three host bind mounts store PostgreSQL data, Linkwarden archives/uploads and the Meilisearch index in `~/.docker/linkwarden/postgres/`, `~/.docker/linkwarden/data/` and `~/.docker/linkwarden/meili/`, respectively. Its web interface binds to loopback on port `8021`; the supplied local Caddy hostname is `linkwarden.21x9.org`. Database, NextAuth and Meilisearch secrets are read from `secrets.docker.linkwarden`; use distinct, URL-safe values for all three secrets. `NEXTAUTH_URL` is generated as `https://linkwarden.21x9.org/api/v1/auth` (or the configured domain). All three directories are mounted directly from the host. The manual Homepage bookmark synchronizer supports `docker.linkwarden.blacklist` for bookmark IDs and `docker.linkwarden.exclude_categories` for collection names; category matching ignores case and surrounding whitespace. Both lists default to empty. Run `python tasks/docker/linkwarden_bookmarks.py --dry-run` to preview the result before synchronization. Run `python tasks/docker/linkwarden_bookmarks.py --list-links` to print every Linkwarden link ID, category, title and URL in a tab-separated table for copying IDs into the blacklist. Listing is read-only and does not download favicons or modify files.
    - **WG-Easy** stores WireGuard configuration in a host bind mount at `~/.docker/wg-easy/`; it publishes UDP `51820` for VPN traffic and binds its administration UI to `127.0.0.1:51821`. The UI is reverse-proxied through Caddy at `vpn.21x9.org`. Complete the initial setup wizard to set the public endpoint to `vpn.21x9.org` and create the administrator account. `INSECURE=true` is set only for the HTTP connection between the container and the local Caddy reverse proxy; do not publish the UI port directly.
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



    **AdGuard Home**

    Enable it by adding an AdGuard Home mapping to `docker` in `@local.py`. It runs as a Docker Compose container using host networking, which lets DNS listen directly on host TCP/UDP port 53 without Docker port publishing. Persistent configuration and query data remain in the bind-mounted directories `~/.docker/adguard_home/conf/` and `~/.docker/adguard_home/work/`. The default image is pinned to `adguard/adguardhome:v0.107.80`; override it with `docker.adguard_home.image` when deliberately upgrading.

    Configure the web UI port with `docker.adguard_home.web_port` in `@local.py`. It defaults to `3000` when omitted; set it to `3001` if another service already occupies host port 3000. Forgejo now defaults to host port `8027`:

    ```python
    docker = {
        "adguard_home": {
            "image": "adguard/adguardhome:v0.107.80",  # Pinned container image.
            "web_port": 3001,  # Host web UI port, different from another listener on 3000.
        },
    }
    caddy_config = {
        "adguard.example.com:443": {
            "reverse_proxy": "127.0.0.1:3001",
        },
    }
    ```

    On first start, complete AdGuard Home's setup wizard at `http://<host-address>:3000` (the initial setup port remains AdGuard's default). After the configuration file exists, the task stops AdGuard before reconciling only `http.address` to `127.0.0.1:<docker.adguard_home.web_port>`, preserving the rest of `AdGuardHome.yaml`; the normal deployment then restarts the service when the address changes. The first-run configuration is left untouched until the setup wizard creates the file. The web UI is then loopback-only and should be reached through the configured Caddy reverse proxy. The default port remains 3000 unless explicitly overridden.

    DNS continues to use host TCP/UDP port 53. Configure DNS to listen only on the LAN and WireGuard addresses that should serve clients, then add DNS rewrites for the desired local names and aliases. Host networking means there are no Compose port mappings to restrict exposure. Check for an existing host resolver already using port 53 before enabling the container; do not disable or reconfigure the host resolver automatically. Point the FRITZ!Box DHCP DNS setting and/or WireGuard clients' `DNS` setting at the host's reachable AdGuard Home address. The container is opt-in and is not deployed unless `docker.adguard_home` is present.

    **Optional public DNS access:** UFW custom rules can allow DNS from any source by adding `"adguard-dns": {"action": "Allow", "rule": "53"}` to the `ufw` mapping in `@local.py`. A port rule without a protocol suffix opens both TCP and UDP port 53, and UFW reports the source as `Anywhere` (including IPv6 when IPv6 support is enabled). This is intentionally not enabled by default. Exposing DNS publicly can create an open resolver and enable abuse or amplification attacks; configure AdGuard's allowed clients and recursion policy before enabling it. Do not expose the setup wizard or administration UI publicly.

    **Storage migration**

    All configured services use direct host bind mounts below `~/.docker/`; no Docker-managed named volumes are used. When changing a service's storage definition, Docker Compose does not automatically migrate existing data. Back up the source and migrate its contents before switching templates. Existing data already in the documented host directories remains in place.

    `tasks/docker/` contains the service-specific configuration and `templates/docker/` contains the corresponding Compose files. Consult both before changing a service's supported host-data keys or storage layout.


## Implementation

- Service modules: `tasks/docker/`
- Compose templates: `templates/docker/`
- Shared deployment helper: `tasks/docker.py`
- Service dispatcher: `tasks/docker_container.py`

See [Task reference](tasks.md#docker-services) for the concise task summary and [Configuration](configuration.md) for host-data structure.
