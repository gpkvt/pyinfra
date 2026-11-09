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
| `templates/Caddyfile.j2` | `tasks/caddy.py` | Caddy site configuration. |
| `templates/docker/*` | Docker task modules | Compose and user-level systemd service definitions. |
| `templates/git/*` | `tasks/git.py` | Git credentials/configuration fragments. |
| `templates/dotfiles/*` | User environment tasks | Rendered user dotfiles. |

Templates may receive host data, runtime values initialized by `common.py`, and explicit keyword arguments from the calling task. Do not assume every template has access to every variable: inspect the call site to determine the actual context.

## Important generated destinations

| Asset | Destination / behavior |
| --- | --- |
| SSH client configuration | `~/.ssh/config`, restrictive mode `0600`. |
| WireGuard interface | `/etc/wireguard/<interface>.conf`, owned by root with mode `0640`. The task does not start the interface. |
| dehydrated config | `/etc/dehydrated/config`, root-owned with mode `0600`. |
| dehydrated hook | `/etc/dehydrated/hook.sh`, root-owned with executable permissions. |
| Docker Compose | Service-specific directory under the configured user's home. |
| Docker systemd unit | `~/.config/systemd/user/<service>.service`. |
| Git credentials | `~/.git-credentials`, mode `0600`, only when matching secrets exist. |
| User scripts | `~/scripts/`; symlinks are created in `/usr/local/bin/`. |

Exact paths can be service- or task-specific and should be confirmed in the implementation before changing them.

## Static payloads

| Path | Consumer / content |
| --- | --- |
| `files/scripts/` | User utility scripts. |
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
