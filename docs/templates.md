# Templates and Static Files

## `templates/` — Jinja2 templates

Rendered by task modules to produce host configuration:

| Template / directory | Consumed by | Purpose |
| --- | --- | --- |
| `ssh_config.j2` | `tasks/ssh_config.py` | SSH client configuration |
| `wireguard.conf.j2` | `tasks/wireguard.py` | WireGuard tunnel configuration |
| `dehydrated_config.j2` | `tasks/dehydrated.py` | dehydrated (ACME) configuration |
| `docker/miniflux/` | `tasks/docker.py` | Miniflux container service definition |
| `docker/timetagger/` | `tasks/docker.py` | Timetagger container service definition |
| `dotfiles/` | user-environment tasks | Rendered user dotfiles |
| `git/` | `tasks/git.py` | Git configuration |

Templates can reference host data (via the pyinfra templating context) and,
where applicable, values published by `common.initialize()` (e.g.
`homedir`, `ssh_dir`, `wireguard_interface`).

> The exact variables referenced inside each template were not extracted at
> documentation time; see the templates themselves for the authoritative list.

## `files/` — static payloads

Copied verbatim by tasks (no rendering):

| Directory | Consumed by | Contents |
| --- | --- | --- |
| `files/scripts/` | `tasks/scripts.py` | Utility scripts |
| `files/dotfiles/` | user-environment tasks | User dotfiles |
| `files/git/` | `tasks/git.py` | Git config files |
| `files/mc/` | `tasks/mc.py` | Midnight Commander config |
| `files/powerline/` | `tasks/powerline.py` | Powerline config |
| `files/tmux/` | `tasks/tmux.py` | tmux config |
| `files/ufw/` | `tasks/ufw.py` | Firewall rules/profiles |
| `files/cosmic/` | `tasks/cosmic/deploy.py` | COSMIC desktop assets/config |

Rule of thumb: **static content → `files/`, parameterized content →
`templates/`.**
