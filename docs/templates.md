# Templates and Static Files

This document describes the Jinja2 templates and static payloads used by deployment tasks.

## `templates/` — Jinja2 templates

Templates are rendered by task modules to produce host-specific configuration files.

| Template / directory | Consumed by | Purpose |
| --- | --- | --- |
| `ssh_config.j2` | `tasks/ssh_config.py` | SSH client configuration |
| `wireguard.conf.j2` | `tasks/wireguard.py` | WireGuard interface configuration |
| `dehydrated_config.j2` | `tasks/dehydrated.py` | dehydrated (ACME) configuration |
| `docker/miniflux/docker-compose.yml.j2` | `tasks/docker/miniflux.py` | Miniflux Docker Compose configuration |
| `docker/timetagger/docker-compose.yml.j2` | `tasks/docker/timetagger.py` | Timetagger Docker Compose configuration |
| `docker/systemd.service.j2` | `tasks/docker.py` | User-level systemd service unit for Docker services |
| `git/git-credentials.j2` | `tasks/git.py` | Git credentials configuration |
| `dotfiles/` | User-environment tasks | Rendered user dotfiles |
| `git/` | `tasks/git.py` | Git configuration |

### Template usage

Templates can reference host data through the pyinfra templating context and, where applicable, values published by `common.initialize()`.

Common runtime variables include:

- `homedir` – Home directory of the configured user.
- `ssh_dir` – SSH configuration directory.
- `wireguard_interface` – WireGuard interface configuration.

Additional variables may be passed directly by the consuming task.

### Template-specific details

#### SSH configuration

`ssh_config.j2` generates the user's SSH client configuration.

- Source: `templates/ssh_config.j2`
- Destination: `~/.ssh/config`
- Permissions: `0600`
- Deployment runs without sudo.

#### WireGuard configuration

`wireguard.conf.j2` generates one configuration file per configured WireGuard interface.

- Source: `templates/wireguard.conf.j2`
- Destination: `/etc/wireguard/<interface>.conf`
- Ownership: `root:root`
- Permissions: `0640`

Interface configuration and private keys are passed to the template separately. Private keys are retrieved from decrypted secrets.

The task deploys configurations but does not start or enable the corresponding VPN services.

#### dehydrated configuration

`dehydrated_config.j2` generates the dehydrated configuration used for Let's Encrypt certificate management.

- Source: `templates/dehydrated_config.j2`
- Destination: `/etc/dehydrated/config`
- Ownership: `root:root`
- Permissions: `0600`

The Hetzner DNS API token is supplied through decrypted secrets. Configuration deployment is skipped when the token is unavailable.

#### Docker Compose configurations

Docker service templates generate individual Compose configurations.

- Miniflux: `templates/docker/miniflux/docker-compose.yml.j2`
- Timetagger: `templates/docker/timetagger/docker-compose.yml.j2`

Generated files are deployed to:

`~/service/docker-compose.yml`

The configured user's home directory is used as the destination root.

Additional template variables are passed by the service-specific deployment task.

#### Docker systemd service

`templates/docker/systemd.service.j2` generates user-level systemd service units for Docker Compose services.

- Destination: `~/.config/systemd/user/<service>.service`
- Permissions: `0644`

The service unit is reloaded and enabled when its configuration changes. The service is restarted when either the Compose configuration or systemd unit changes.

#### Git credentials

`templates/git/git-credentials.j2` generates the user's Git credentials file.

- Source: `templates/git/git-credentials.j2`
- Destination: `~/.git-credentials`
- Permissions: `0600`

Credentials are supplied through decrypted secrets using `git_credentials`.

The credentials file is only deployed when the corresponding secrets entry is available.

## `files/` — static payloads

Static files are copied or synchronized by tasks without Jinja2 rendering.

| Directory / file | Consumed by | Contents |
| --- | --- | --- |
| `files/scripts/` | `tasks/scripts.py` | Utility scripts |
| `files/dehydrated_hook.sh` | `tasks/dehydrated.py` | dehydrated hook script |
| `files/dotfiles/` | User-environment tasks | User dotfiles |
| `files/git/` | `tasks/git.py` | Git configuration files |
| `files/mc/` | `tasks/mc.py` | Midnight Commander configuration |
| `files/powerline/` | `tasks/powerline.py` | Powerline configuration |
| `files/tmux/` | `tasks/tmux.py` | tmux configuration |
| `files/ufw/` | `tasks/ufw.py` | Firewall rules and profiles |
| `files/cosmic/` | `tasks/cosmic/deploy.py` | COSMIC desktop assets and configuration |

### Static file deployment details

#### Scripts

Files from `files/scripts/` are synchronized to the configured user's `~/scripts/` directory.

- Permissions: `0750`
- Existing destination files not present in the source directory are preserved.
- Symbolic links are created in `/usr/local/bin/` for the deployed scripts.

#### dehydrated hook

`files/dehydrated_hook.sh` is deployed to:

`/etc/dehydrated/hook.sh`

- Ownership: `root:root`
- Permissions: `0750`

#### Git configuration

`files/git/gitconfig` is copied to:

`~/.gitconfig`

- Permissions: `0640`

#### Other configuration directories

The remaining directories contain static configuration files deployed by their respective task modules. Refer to the corresponding task for destination paths, ownership and permissions.

## Adding new templates and static files

Use the following guidelines when adding new deployment assets:

1. Use `templates/` for files that require dynamic values, host-specific configuration or secrets.
2. Use `files/` for static files that can be copied or synchronized without rendering.
3. Keep templates in directories that reflect their consuming task or application.
4. Reference templates and static files using paths relative to the repository root.
5. Define ownership and permissions explicitly in the consuming task.
6. Pass sensitive values through decrypted secrets rather than hardcoding them in templates.
7. Document new assets in this file and identify the task responsible for deploying them.

**Rule of thumb:** Static content → `files/`; parameterized content → `templates/`.
