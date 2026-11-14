# Templates and static assets

Task modules use two asset types:

- **Templates** in `templates/` are rendered with host-specific values or secrets.
- **Static files** in `files/` are copied or synchronized without Jinja2 rendering.

The consuming task controls the destination, owner, group, permissions and any service reload/restart behavior.

## Jinja2 templates

| Template | Consumer | Purpose |
| --- | --- | --- |
| `templates/apt_repository.list.j2` | `tasks/apt.py` | APT source-list entries. |
| `templates/ssh_config.j2` | `tasks/ssh_config.py` | User SSH client configuration. |
| `templates/wireguard.conf.j2` | `tasks/wireguard.py` | WireGuard interface configuration. |
| `templates/dehydrated_config.j2` | `tasks/dehydrated.py` | dehydrated configuration. |
| `templates/workstation/borgmatic.yml.j2` | `tasks/workstation/backup.py` | Borgmatic configuration deployed to `/etc/borgmatic/config.yaml`. |
| `templates/Caddyfile.j2` | `tasks/caddy.py` | Caddy site configuration. |
| `templates/docker/*` | Docker task modules | Service-specific Compose definitions and the shared user-level systemd service unit. |
| `templates/git/*` | `tasks/git.py` | Git credentials/configuration fragments. |
| `templates/dotfiles/*` | User environment tasks | Rendered user dotfiles. |

Templates may receive host data, runtime values initialized by `common.py`, and explicit keyword arguments from the calling task. Do not assume every template has access to every variable: inspect the call site to determine the actual context.

## Docker Compose templates and persistent data

Each service has a Compose template under `templates/docker/<service>/docker-compose.yml.j2`; the shared systemd unit is `templates/docker/systemd.service.j2`. Compose files are deployed to `~/.docker/<service>/docker-compose.yml`. Persistent data is stored in host directories under `~/.docker/` and mounted into the containers:

| Service | Host path | Container path |
| --- | --- | --- |
| Miniflux PostgreSQL | `~/.docker/miniflux/db/` | `/var/lib/postgresql/data` |
| TimeTagger | `~/.docker/timetagger/` | `/root/_timetagger` |
| Grav | `~/.docker/grav/data/` | `/var/www/html` |
| Forgejo | `~/.docker/forgejo/data/` | `/data` |
| Portainer | `~/.docker/portainer/data/` | `/data` |
| TasmoAdmin | `~/.docker/tasmoadmin/data/` | `/data/tasmoadmin` |
| Wallabag data | `~/.docker/wallabag/data/` | `/var/www/wallabag/data` |
| Wallabag images | `~/.docker/wallabag/images/` | `/var/www/wallabag/web/assets/images` |
| Vaultwarden | `~/.docker/vaultwarden/` | `/data` |
| NocoDB | `~/.docker/nocodb/data/` | `/usr/app/data` |
| Homepage | `~/.docker/homepage/config/` plus `public/icons/` and `public/images/` | `/app/config`, `/app/public/icons`, `/app/public/images` |
| Linkwarden | `~/.docker/linkwarden/postgres/`, `data/`, `meili/` | PostgreSQL, application data, Meilisearch data |
| Paperless-ngx | `~/.docker/paperless/postgres/`, `data/`, `media/`, `consume/`, `export/` | PostgreSQL and Paperless data directories |
| Firefly III | `~/.docker/firefly-iii/database/`, `upload/`, `fints/` | MariaDB, uploads and importer config |
| Snipe-IT | `~/.docker/snipe-it/database/`, `storage/` | MariaDB and `/var/lib/snipeit` |
| WG-Easy | `~/.docker/wg-easy/` | `/etc/wireguard` and application data |

All configured service data mounts use direct host bind mounts; Compose does not create Docker-managed named volumes. The task creates service configuration directories, but the service modules may also create or assign ownership to application data directories where required. Review the individual Compose template and task before changing mount paths: application UID/GID requirements differ between images.

Some older service templates used Docker-managed named volumes. Switching an existing deployment from a named-volume layout to the current host bind mounts does not copy existing volume contents; migrate the data explicitly before applying the change.

## Important generated destinations

| Asset | Destination / behavior |
| --- | --- |
| SSH client configuration | `~/.ssh/config`, restrictive mode `0600`. |
| WireGuard interface | `/etc/wireguard/<interface>.conf`, owned by root with mode `0640`. The task does not start the interface. |
| dehydrated config | `/etc/dehydrated/config`, root-owned with mode `0600`. |
| Borgmatic config | `/etc/borgmatic/config.yaml`, root-owned with mode `0600`; review and complete its repository/source settings before relying on it. The current template also contains the literal fallback passphrase `B0rgm4t1C!`—do not use that default for real backups. |
| dehydrated hook | `/etc/dehydrated/hook.sh`, root-owned with executable permissions. |
| Docker Compose | `~/.docker/<service>/` under the configured user's home. |
| Docker systemd unit | `~/.config/systemd/user/<service>.service`. |
| Git credentials | `~/.git-credentials`, mode `0600`, only when matching secrets exist. |
| User scripts | `~/scripts/`; symlinks are created in `/usr/local/bin/`. |

**Borgmatic passphrase warning:** `templates/workstation/borgmatic.yml.j2` renders `encryption_passphrase` from `borg_passphrase` or the literal fallback `B0rgm4t1C!`. `tasks/workstation/backup.py` currently does not pass `borg_passphrase` explicitly, so the fallback is used by the current task. The generated config is root-owned with mode `0600`, which protects it from unprivileged local users, but the fallback is public in source and is not suitable for a real repository. Do not initialize or rely on a production Borg repository with this fallback; replace it with a unique secret and verify the rendering path before use.

Exact paths can be service- or task-specific and should be confirmed in the implementation before changing them.

## Static payloads

| Path | Consumer / content |
| --- | --- |
| `files/scripts/` | User utility scripts, including `gpg-vault` for managing the encrypted secrets file. |
| `files/dehydrated_hook.sh` | dehydrated hook script. |
| `files/dotfiles/` | Shell and user dotfiles. |
| `files/git/` | Git configuration. |
| `files/mc/` | Midnight Commander configuration. |
| `files/powerline/` | Powerline configuration and themes. |
| `files/tmux/` | tmux configuration. |
| `files/ufw/` | UFW application profiles/rules. |
| `files/cosmic/` | COSMIC desktop assets and configuration. |
| Other files under `files/` | Application-specific assets referenced by individual tasks. |

## Choosing the right location

| Requirement | Put it in |
| --- | --- |
| Identical file copied to every applicable host | `files/` |
| File needs host data, generated values or secret material | `templates/` |
| New desired-state setting | `group_data/<host>.py` |
| Credential or private key | encrypted secrets JSON; pass it to the task/template at render time |

## Adding an asset

1. Place the file under a directory that reflects its consumer or feature.
2. Reference it from the relevant task using a repository-relative path.
3. Set destination, owner, group and mode explicitly.
4. Consider whether a changed file requires a daemon reload, service restart or cache refresh.
5. Ensure secrets are not rendered into world-readable files or exposed in logs.
6. Update this reference and the relevant task/configuration documentation.
