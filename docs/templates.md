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

Each service has a Compose template under `templates/docker/<service>/docker-compose.yml.j2`; the shared systemd unit is `templates/docker/systemd.service.j2`. Compose files are deployed to `~/<service>/docker-compose.yml`. Persistent data is stored in host directories under `~/.docker/` and mounted into the containers:

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

These are host bind mounts, not Docker-managed named volumes. The task creates service configuration directories, but the service modules may also create or assign ownership to application data directories where required. Review the individual Compose template and task before changing mount paths: application UID/GID requirements differ between images.

Wallabag and Vaultwarden previously used named-volume templates. Switching from one of those templates to the current host bind mounts does not copy existing volume contents; migrate the data explicitly before applying the change on a host that still has data in the old volume.

## Important generated destinations

| Asset | Destination / behavior |
| --- | --- |
| SSH client configuration | `~/.ssh/config`, restrictive mode `0600`. |
| WireGuard interface | `/etc/wireguard/<interface>.conf`, owned by root with mode `0640`. The task does not start the interface. |
| dehydrated config | `/etc/dehydrated/config`, root-owned with mode `0600`. |
| Borgmatic config | `/etc/borgmatic/config.yaml`, root-owned with mode `0600`; review and complete its repository/source settings before relying on it. The current template also contains the literal fallback passphrase `B0rgm4t1C!`—do not use that default for real backups. |
| dehydrated hook | `/etc/dehydrated/hook.sh`, root-owned with executable permissions. |
| Docker Compose | Service-specific directory under the configured user's home. |
| Docker systemd unit | `~/.config/systemd/user/<service>.service`. |
| Git credentials | `~/.git-credentials`, mode `0600`, only when matching secrets exist. |
| User scripts | `~/scripts/`; symlinks are created in `/usr/local/bin/`. |

**Security issue to resolve in implementation:** `templates/workstation/borgmatic.yml.j2` currently renders `storage.encryption_passphrase` from `borg_passphrase` or the literal fallback `B0rgm4t1C!`. The backup task writes the resulting configuration root-owned with mode `0644`. Do not rely on the fallback for real repositories; supply a unique secret through a verified secret-safe rendering path and ensure the resulting configuration is not readable by untrusted users. The current backup task does not explicitly pass a `borg_passphrase` argument, so verify the template context before assuming a host-data value overrides the fallback.

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
