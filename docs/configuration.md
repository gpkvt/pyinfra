# Configuration

Configuration is host-specific and lives in `group_data/`. The file
`group_data/@local.py` contains the configuration for the local environment.
Variables defined there are available in tasks as `host.data.<name>`.

> The shipped files contain examples and defaults for the author's local
> environment. **Adapt them to your own infrastructure before deployment.**
> Sensitive credentials and private keys are maintained separately in the
> encrypted secrets configuration (see `docs/secrets.md`). Default values for
> optional settings are determined by the consuming deployment modules.

## Configuration sections

Per the module docstring of `group_data/@local.py`, settings are organized
into logical sections:

### General

Primary user, group, and home directory, plus network basics:

| Variable | Meaning | Seen in `@local.py` |
| --- | --- | --- |
| `username` | Primary user name | `gpkvt` |
| `usergroup` | Primary group | `gpkvt` |
| `homedir` | Home directory (also published as `builtins.homedir`) | `/home/gpkvt` |
| `local_network_cidr` | Local network, used by VPN/WireGuard tasks (default `10.0.0.0/24`) | `192.168.42.0/24` |
| `wireguard_interface` | WireGuard interface name (default `False`) | `home` |

### Network — `/etc/hosts` mappings

The `hostnames` dictionary drives the `hosts` task (management of
`/etc/hosts`). Example from `@local.py`:

```python
hostnames = {
    "127.0.0.1": "localhost local.21x9.org timetagger.21x9.org",
    "::1": "localhost local.21x9.org",
    "192.168.42.100": "storage.intern.21x9.org paperless.intern.21x9.org huginn.intern.21x9.org grafana.intern.21x9.org ha.intern.21x9.org",
    "192.168.42.120": "storage.21x9.org",
}
```

### User environment

Boolean feature flags controlling optional shell/terminal tooling:

| Flag | Task gated | Effect |
| --- | --- | --- |
| `zsh` | `tasks/zsh.py` | Install/configure zsh |
| `tmux` | `tasks/tmux.py` | Install/configure tmux |
| `powerline` | `tasks/powerline.py` | Install/configure Powerline |
| `ssh_config` | `tasks/ssh_config.py` | Deploy SSH client configuration |

### Services and feature flags

Flags enabling further infrastructure features (each gates one task in
`deploy.py`):

| Flag | Task gated |
| --- | --- |
| `caddy_config` | `tasks/caddy.py` |
| `ufw` | `tasks/ufw.py` |
| `docker` | `tasks/docker.py` |
| `apparmor_profiles` | `tasks/apparmor.py` |
| `cosmic` | `tasks/cosmic/deploy.py` (COSMIC desktop) |

Combined feature requirements:

- **WireGuard tunnel**: requires `wireguard_config` in host data **and**
  a `wireguard` entry in secrets.
- **VPN routing**: requires both `local_network_cidr` **and**
  `wireguard_interface` to be set.
- **Certificates (dehydrated)**: requires a `dehydrated` entry in secrets.
- **Flatpak**: gated by detected availability (`builtins.flatpak`, checked
  via `initialize(host, check_flatpak=True)`), not by a config flag.

### Docker

The Docker section defines containerized applications and their deployment
options. Corresponding compose/service templates ship under
`templates/docker/` (e.g. `miniflux/`, `timetagger/`). See
`docs/tasks.md` (docker) for details.

### APT packages

The APT section lists system packages to install and maintain; consumed by
`tasks/apt.py`.

### Flatpak applications

Flatpak application IDs to install, consumed by `tasks/flatpak.py` when
Flatpak is available. Examples from `@local.py` include
`com.spotify.Client`, `com.obsproject.Studio`, `com.github.tchx84.Flatseal`,
`com.github.wwmm.easyeffects`, and various COSMIC applets
(`dev.cappsy.CosmicExtAppletDict`, `dev.edfloreshz.CosmicTweaks`, …).

> **Note:** The exact variable names for the Docker/APT/COSMIC sections beyond
> those quoted above could not be fully extracted from `@local.py` at
> documentation time. Consult `group_data/@local.py` directly — it is fully
> commented and serves as the canonical reference for all host variables.

## Adding a new host

1. Add the host to `inventory.py` (SSH connection settings, sudo options).
2. Create a matching file in `group_data/` (named after the host) with the
   required variables/flags.
3. Ensure the host is not listed in `disabled_hosts`.
