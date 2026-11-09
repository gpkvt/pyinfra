# Architecture

## Overview

This repository implements a configuration-driven infrastructure automation
workflow on top of [pyinfra](https://pyinfra.com). Deployment logic, target
definition, host configuration, and secrets are strictly separated:

```
inventory.py ──► defines deployment targets (hosts) + SSH settings
      │
      ▼
deploy.py ─────► orchestrator: selects which tasks to include
      │            conditions come from host.data (group_data/) and secrets
      ▼
tasks/*.py ────► modular provisioning logic (operations)
      │
      ▼
files/ + templates/ ─► static payloads (scripts, dotfiles) and Jinja2 templates
      │
      ▲
common.py ─────► initialize(): decrypts secrets, exposes shared config via builtins
      │
      ▲
group_data/ ───► host-specific configuration consumed as host.data
```

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| `inventory.py` | Defines deployment targets and SSH settings |
| `group_data/` | Contains host-specific configuration |
| `common.py` | Initializes shared configuration and decrypts secrets |
| `deploy.py` | Selects and executes deployment tasks |
| `tasks/` | Contains modular provisioning tasks |
| `files/` | Contains scripts, dotfiles, and configuration files |
| `templates/` | Contains Jinja2 templates |
| `secrets.json.gpg.example` | Documents the expected secrets structure |

## Execution flow

1. **Inventory resolution** — pyinfra loads `inventory.py`. The special
   `@local` host represents the local execution environment. Hosts listed in
   `disabled_hosts` are excluded from the production inventory.
2. **Initialization** — `deploy.py` calls `common.initialize(host)`:
   - `common.initialize()` checks whether `secrets.json.gpg` exists.
     If present, it runs `gpg --decrypt secrets.json.gpg`, parses the JSON
     output, and publishes it as `builtins.secrets`. If absent, it sets
     `builtins.secrets = {}` and prints "Loading Secrets: None, skipping…".
     Features requiring secrets are consequently skipped.
   - Shared configuration values are published as builtins:
     `builtins.homedir` (from `host.data.homedir`),
   - Optionally (`check_flatpak=True`), the Flatpak executable is detected
     via the `Which` fact and stored as `builtins.flatpak`.
3. **Task selection** — `deploy.py` includes task modules conditionally
   (see `docs/deployment.md` for the exact conditions).
4. **Execution** — pyinfra connects to each host (SSH or local) and executes
   the included operations, reporting changed vs. unchanged operations.

## Configuration access patterns

Per the module docstring in `deploy.py`:

> Configuration values are accessed through `host.data`, while shared runtime
> configuration and secrets are exposed through builtins.

That means:

- **`host.data.*`** — everything defined in `group_data/<host>.py`
  (feature flags such as `host.data.zsh`, `host.data.docker`, etc.).
- **Builtins** — cross-task runtime values (`secrets`, `homedir`,
  `ssh_dir`, `wireguard_interface`, `local_network_cidr`, `flatpak`),
  published by `common.initialize()`.

## Modularity

Each task file is self-contained and maps to one concern:

- Core tasks (always included): `apt`, `hosts`, `scripts`, `mc`, `git`.
- Optional tasks (condition-gated): `flatpak`, `ssh_config`, `wireguard`,
  `vpn`, `dehydrated`, `caddy`, `zsh`, `tmux`, `powerline`, `ufw`, `docker`,
  `apparmor`, `cosmic` (via `tasks/cosmic/deploy.py`).

Static payloads (dotfiles, scripts, firewall profiles) live under `files/`,
dynamic configuration is rendered from `templates/` using Jinja2
(`ssh_config.j2`, `wireguard.conf.j2`, `dehydrated_config.j2`,
`templates/docker/*`, `templates/dotfiles/`, `templates/git/`).
