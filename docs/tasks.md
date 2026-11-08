# Task Reference

All deployment tasks live in `tasks/`. Each file is a pyinfra task module;
static payloads come from `files/`, dynamic configuration from `templates/`.

## Core tasks (always included by `deploy.py`)

### `tasks/apt.py`
Debian package management. Installs and maintains the system packages listed
in the APT section of the host configuration.

### `tasks/hosts.py`
Manages `/etc/hosts` entries from the `hostnames` mapping in `group_data/`.

### `tasks/scripts.py`
Deploys arbitrary scripts from `files/scripts/`.

### `tasks/mc.py`
Installs and configures Midnight Commander (configuration from `files/mc/`).

### `tasks/git.py`
Git configuration (dotfiles from `files/git/`, templates from `templates/git/`).

## Optional tasks (condition-gated)

### `tasks/flatpak.py`
Installs Flatpak applications listed in the host configuration (e.g. Spotify,
OBS Studio, Flatseal, EasyEffects, COSMIC applets). Gated on Flatpak being
detected on the host (`builtins.flatpak` fact via `Which`).

### `tasks/ssh_config.py`
Deploys the SSH client configuration rendered from
`templates/ssh_config.j2`. Gated on `host.data.ssh_config`.

### `tasks/wireguard.py`
Deploys a WireGuard tunnel configuration from `templates/wireguard.conf.j2`.
Requires **both** `host.data.wireguard_config` and a `wireguard` entry in the
decrypted secrets.

### `tasks/vpn.py`
VPN routing/network integration. Requires both `local_network_cidr` and
`wireguard_interface` to be configured.

### `tasks/dehydrated.py`
ACME (Let's Encrypt) certificate management via dehydrated; configuration
rendered from `templates/dehydrated_config.j2`. Requires a `dehydrated` entry
in secrets.

### `tasks/caddy.py`
Caddy web server / reverse proxy configuration. Gated on
`host.data.caddy_config`.

### `tasks/zsh.py`
zsh shell setup. Gated on `host.data.zsh`.

### `tasks/tmux.py`
tmux configuration (payload from `files/tmux/`). Gated on `host.data.tmux`.

### `tasks/powerline.py`
Powerline prompt setup (payload from `files/powerline/`). Gated on
`host.data.powerline`.

### `tasks/ufw.py`
UFW firewall rules (profiles from `files/ufw/`). Gated on `host.data.ufw`.

### `tasks/docker.py`
Docker installation and containerized application deployment. Sub-tasks in
`tasks/docker/`; service definitions/templates under `templates/docker/`
(e.g. `miniflux/`, `timetagger/`). Gated on `host.data.docker`.

### `tasks/apparmor.py`
AppArmor profile management. Gated on `host.data.apparmor_profiles`.

### `tasks/cosmic/` (entry: `tasks/cosmic/deploy.py`)
COSMIC desktop environment setup (payloads from `files/cosmic/`). Gated on
`host.data.cosmic`.

> **Note:** Detailed operation lists per task (which pyinfra operations each
> file runs, with which arguments) were not extracted file-by-file at
> documentation time. Each task file is commented; treat this reference as the
> map and the source files as the detail.
