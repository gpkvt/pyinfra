# Task Reference

All deployment tasks live in `tasks/`. Each file is a pyinfra task module; static payloads come from `files/`, dynamic configuration from `templates/`.

## Core tasks (always included by `deploy.py`)

### `tasks/apt.py`

Debian package management. Configures third-party APT repositories, downloads repository signing keys, updates package indexes, upgrades installed packages and installs the system packages listed in `apt_packages`.

Repository configuration is read from `apt_sources` in the host configuration.

### `tasks/hosts.py`

Manages `/etc/hosts` entries from the `hostnames` mapping in `group_data/`.

Defaults to configuring `127.0.0.1` as `localhost`.

### `tasks/sudo.py`

Manages custom sudoers rules from the `sudoers_rules` host configuration.

Writes the rules to `/etc/sudoers.d/99-local`, validates the configuration using `visudo` before installation and sets permissions to `0440`.

### `tasks/system.py`

Manages basic operating-system configuration, including hostname, timezone, locale, default editors, keyboard layout, sysctl parameters, udev rules and USBGuard.

Configuration is read from the host data. See system.md for details.

### `tasks/ssh_keys.py`

Manages SSH keypairs and authorized keys.

Configuration:

- `ssh_keys`: List of SSH keypairs to generate.
- `ssh_authorized_keys`: Mapping of system users to public keys.

Supports Ed25519 and RSA keys. RSA keys must have at least 3072 bits.

Private keys are never overwritten automatically. SSH key passphrases are retrieved from the decrypted secrets configuration.

### `tasks/git.py`

Git configuration and dotfiles from `files/git/`, with templates from `templates/git/`.

### `tasks/fonts.py`

Installs and configures system fonts through APT, including Fontconfig and a comprehensive collection of font packages.

Optionally downloads and installs additional Powerline-patched fonts when `powerline_fonts` is enabled in the host configuration.

### `tasks/scripts.py`

Deploys arbitrary scripts from `files/scripts/` to the configured user's `~/scripts/` directory and creates symbolic links in `/usr/local/bin/`.

Uses `username` and `usergroup` from the host configuration, defaulting to `root`.

Existing destination files not present in the source directory are preserved.

### `tasks/mc.py`

Installs and configures Midnight Commander using configuration files from `files/mc/`.

## Optional tasks (condition-gated)

### `tasks/flatpak.py`

Installs Flatpak applications listed in the host configuration (e.g. Spotify, OBS Studio, Flatseal, EasyEffects, COSMIC applets).

Gated on Flatpak being detected on the host (`builtins.flatpak` fact via `Which`).

### `tasks/ssh_config.py`

Deploys the SSH client configuration rendered from `templates/ssh_config.j2`.

Gated on `host.data.ssh_config`.

### `tasks/wireguard.py`

Deploys a WireGuard tunnel configuration from `templates/wireguard.conf.j2`.

Requires both `host.data.wireguard_config` and a `wireguard` entry in the decrypted secrets.

### `tasks/vpn.py`

VPN routing/network integration.

Requires both `local_network_cidr` and `wireguard_interface` to be configured.

### `tasks/dehydrated.py`

ACME (Let's Encrypt) certificate management via dehydrated; configuration rendered from `templates/dehydrated_config.j2`.

Requires a `dehydrated` entry in secrets.

### `tasks/caddy.py`

Caddy web server / reverse proxy configuration.

Gated on `host.data.caddy_config`.

### `tasks/zsh.py`

zsh shell setup.

Gated on `host.data.zsh`.

### `tasks/tmux.py`

tmux configuration (payload from `files/tmux/`).

Gated on `host.data.tmux`.

### `tasks/powerline.py`

Powerline prompt setup (payload from `files/powerline/`).

Gated on `host.data.powerline`.

### `tasks/ufw.py`

UFW firewall rules (profiles from `files/ufw/`).

Gated on `host.data.ufw`.

### `tasks/docker.py`

Docker installation and containerized application deployment.

Sub-tasks in `tasks/docker/`; service definitions/templates under `templates/docker/` (e.g. `miniflux/`, `timetagger/`).

Gated on `host.data.docker`.

### `tasks/apparmor.py`

AppArmor profile management.

Gated on `host.data.apparmor_profiles`.

### `tasks/cosmic/` (entry: `tasks/cosmic/deploy.py`)

COSMIC desktop environment setup (payloads from `files/cosmic/`).

Gated on `host.data.cosmic`.

### `tasks/mullvad_extensions.py`

Manages Mullvad Browser extensions and user preferences.

Configuration:

- `mullvad_browser_dir`: Mullvad Browser distribution directory. Defaults to `/usr/lib/mullvad-browser/distribution`.
- `mullvad_extensions`: Dictionary of extensions to download, each containing a download URL and extension ID.
- `username` and `usergroup`: Ownership of the extensions directory and downloaded extensions.

Downloads configured XPI files into the browser's extensions directory and deploys `files/mullvad-user.js` as `user.js`.

Gated on `host.data.mullvad_extensions`.

Restart Mullvad Browser after deployment for changes to take effect.

### `tasks/vscodium.py`

Manages VSCodium extensions.

Configuration:

- `vscodium`: Dictionary containing an `extensions` list of extension IDs.
- `username`: Target user for extension installation.

Detects already installed extensions and schedules installation only for missing ones. Existing manually installed extensions are preserved.

Gated on `host.data.vscodium`.

### `tasks/proton.py`

Installs Proton applications.

Supported components:

- Proton Mail
- Proton Mail Bridge
- Proton VPN
- Proton Pass
- Proton Drive CLI

Uses the official APT repository, Flathub or official Proton DEB downloads depending on the application and configuration.

Configuration is read from `host.data.proton`.

Gated on `host.data.proton`.

## Deployment order

The complete deployment is orchestrated by `deploy.py`.

Core tasks are included first, followed by optional tasks according to their respective conditions.

The core task order is:

1. `tasks/apt.py`
2. `tasks/hosts.py`
3. `tasks/sudo.py`
4. `tasks/system.py`
5. `tasks/ssh_keys.py`
6. `tasks/git.py`
7. `tasks/fonts.py`
8. `tasks/scripts.py`
9. `tasks/mc.py`

Optional tasks are included when their corresponding configuration or prerequisites are available.

## Notes

The task descriptions above provide an overview of configuration, functionality and execution conditions. For detailed operation lists and implementation specifics, refer to the individual source files in `tasks/`.

The deployment entry point is `deploy.py`.
