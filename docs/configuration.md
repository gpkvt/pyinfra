# Host configuration

Host-specific desired state is stored as Python data in `group_data/`. pyinfra exposes the values for a target through `host.data`. The supplied `group_data/@local.py` is an example configuration for one environment, not a portable default. Audit and adapt it before running any deployment.

## Which files are used?

The inventory target name determines its host-data file: the local target uses `group_data/@local.py`, and a target named `web01` uses `group_data/web01.py`. Inventory groups can add shared configuration for a role or class of hosts. For example, `workstation = ["@local"]` in `inventory.py` makes `@local` a member of the `workstation` group, so pyinfra also loads `group_data/workstation.py`. Group data and host data are both available through `host.data`; keep role-wide defaults in the group file and host-specific overrides in the host file.

The workstation group is optional. Add a host to the `workstation` inventory group only if it should receive that role's configuration and eligible workstation tasks.

Keep configuration data separate from task logic. Put private keys, passwords, API tokens and credential-bearing URLs in the encrypted secrets file, not in group data. Use the deployed `gpg-vault` command to manage that file without routinely handling plaintext manually. See [Secrets management](secrets.md).

## Common settings

| Setting | Purpose | Notes |
| --- | --- | --- |
| `hostname` | System hostname | Managed by `tasks/system.py`. |
| `username` | Primary user | Used by user-scoped tasks; some tasks default to `root` if omitted. |
| `usergroup` | Primary group | Used by user-scoped tasks; some tasks default to `root`. |
| `homedir` | User home directory | Also published as `builtins.homedir`; defaults to `/root/` in `common.initialize()`. |
| `timezone` | System timezone | Use a valid zoneinfo identifier. |
| `locale` | System locale | Defaults to `en_US.UTF-8` in the system task; set to `None` to skip locale management. |
| `keyboard` | XKB keyboard configuration | Empty dictionary disables management. |
| `editor` / `visual_editor` | Default editors | `visual_editor` falls back to `editor`. |

Example:

```python
hostname = "workstation"
username = "deploy"
usergroup = "deploy"
homedir = "/home/deploy"
timezone = "Etc/UTC"
locale = "en_US.UTF-8"
editor = "vim"
```

## Workstation role

The supplied `group_data/workstation.py` defines a shared, nested `workstation` configuration. `deploy.py` checks each feature's `enabled` flag and includes its corresponding task only when that flag is true. Features are independently gated; a disabled feature is not installed by the workstation task set.

| Setting | Default in supplied group data | Effect |
| --- | --- | --- |
| `workstation.backup.enabled` | `True` | Installs Restic, Borg, rsync and Borgmatic, and renders `/etc/borgmatic/config.yaml`. It does not create or run a backup job; repository locations, credentials, sources, retention and restore testing still need configuration. |
| `workstation.power.enabled` | `True` | Installs and enables the selected power manager. `manager` must be `tlp` or `power-profiles-daemon`; the other manager is removed. |
| `workstation.hardware.enabled` | `True` | Installs `fwupd` and, when selected, CPU microcode (`intel` or `amd`). Firmware updates are not applied automatically. |
| `workstation.storage.enabled` | `True` | Installs `smartmontools` and `nvme-cli`; no monitoring schedule or alerting is configured. |
| `workstation.peripherals.enabled` | `False` | Enables optional printer/scanner support. Set `printing` and/or `scanning` to true; CUPS is enabled when printing is selected. |
| `workstation.desktop.enabled` | `False` | Installs common desktop integration utilities. `packages` can replace the default package list. |
| `workstation.maintenance.enabled` | `False` | Installs `needrestart`, `debian-goodies` and `apt-file`; no unattended upgrades or automatic reboots are enabled. |

Example role configuration:

```python
workstation = {
    "backup": {"enabled": True},
    "power": {"enabled": True, "manager": "tlp"},
    "hardware": {"enabled": True, "cpu_vendor": "amd"},
    "storage": {"enabled": True},
    "peripherals": {
        "enabled": False,
        "printing": False,
        "scanning": False,
    },
    "desktop": {"enabled": False},
    "maintenance": {"enabled": False},
}
```

Review the checked-in role defaults before deploying: backup tools and power/hardware/storage utilities are enabled in the supplied example. In particular, the backup task only installs tools and deploys a Borgmatic configuration template; it does not configure repository credentials or schedule backups. The current Borgmatic template also contains a literal fallback encryption passphrase (`B0rgm4t1C!`) and the generated file is mode `0644`; do not use that fallback for real backups. See [Templates and static assets](templates.md) for the security caveat.

## Network and name resolution

`hostnames` maps IP addresses to one or more hostnames and is consumed by `tasks/hosts.py` to manage `/etc/hosts`.

```python
hostnames = {
    "127.0.0.1": "localhost",
    "::1": "localhost",
    "192.0.2.10": "app.example.test app",
}
```

VPN-related settings:

| Setting | Purpose |
| --- | --- |
| `local_network_cidr` | IPv4 CIDR used to detect whether the host is on the trusted/local network. |
| `wireguard_interface` | Interface name used by the VPN service task. |
| `wireguard_config` | Mapping of interface names to WireGuard interface settings. |

The VPN task currently checks globally scoped IPv4 addresses only. It starts/enables `wg-quick@<wireguard_interface>` when none belongs to the configured local CIDR. It does not evaluate IPv6 network membership.

## Packages and repositories

- `apt_packages`: list of Debian package names installed by `tasks/apt.py`.
- `apt_sources`: mapping of repository identifiers to signing-key and APT source definitions. The task downloads keys and creates `.list` source files.
- `flatpak_packages`: list of Flatpak application IDs. `tasks/flatpak.py` is included only when the Flatpak executable is detected.

Example:

```python
apt_packages = ["curl", "git", "rsync"]
flatpak_packages = ["org.mozilla.firefox"]
```

Review third-party repository URLs, distributions, architectures and signing-key sources before enabling them.

## System hardening and access

| Setting | Consumed by | Purpose |
| --- | --- | --- |
| `sysctl` | `tasks/system.py` | Kernel parameters, applied immediately and persisted in `/etc/sysctl.d/99-local.conf`. |
| `udev` | `tasks/system.py` | Mapping of `.rules` filenames to rule contents. |
| `usbguard` | `tasks/system.py` | Daemon policy and explicit device authorization rules. |
| `sudoers_rules` | `tasks/sudo.py` | Custom sudoers lines installed after `visudo` validation. |
| `ssh_keys` | `tasks/ssh_keys.py` | SSH keypair definitions to generate when absent. |
| `ssh_authorized_keys` | `tasks/ssh_keys.py` | Mapping of users to authorized public keys. |
| `ssh_config` | `tasks/ssh_config.py` | SSH client configuration rendered from a template. |
| `apparmor_profiles` | `tasks/apparmor.py` | Profiles to enforce. |

For detailed validation, file paths and safety considerations, see [System configuration](system.md) and [Task reference](tasks.md).

## Optional user and desktop features

| Setting | Module | Expected content |
| --- | --- | --- |
| `zsh` | `tasks/zsh.py` | Truthy enablement value; includes the Zsh dotfiles and generates `.zshrc`. |
| `zshrc_imports` | `tasks/zsh.py` | Optional list of additional Zsh configuration files or import statements inserted into the generated `.zshrc`; defaults to an empty list. |
| `zplug_plugins` | `tasks/zsh.py` | Optional list of zplug plugin definitions; defaults to an empty list. |
| `tmux` | `tasks/tmux.py` | Truthy enablement value. |
| `powerline` | `tasks/powerline.py` | Truthy enablement value. |
| `powerline_fonts` | `tasks/fonts.py` | Boolean-like flag for optional patched fonts. |
| `cosmic` | `tasks/cosmic/deploy.py` | COSMIC desktop configuration dictionary. |
| `vscodium` | `tasks/vscodium.py` | Extension configuration dictionary. |
| `mullvad_extensions` | `tasks/mullvad_extensions.py` | Extension IDs and download URLs. |
| `mullvad_browser_dir` | `tasks/mullvad_extensions.py` | Browser distribution directory; task default is `/usr/lib/mullvad-browser/distribution`. |
| `proton` | `tasks/proton.py` | Proton application selection and options. |

Example:

```python
zsh = True
zshrc_imports = [
    "source ~/.config/zsh/local.zsh",
    "source ~/.config/zsh/secrets.zsh",
]
zplug_plugins = ["zsh-users/zsh-autosuggestions", "zsh-users/zsh-syntax-highlighting"]
```

`zshrc_imports` entries are rendered into the generated `.zshrc`; ensure referenced files exist for the configured user. Keep credentials out of these files unless they are protected separately.

## Service configuration

### Docker

`docker` is a mapping of service names to service-specific settings. The supported keys are `miniflux`, `timetagger`, `grav`, `forgejo`, `portainer`, `tasmoadmin`, `wallabag`, `vaultwarden`, `nocodb` and `homepage`. Each service has its own options; inspect its module under `tasks/docker/` and its Compose template under `templates/docker/<service>/` before adding keys.

All current services persist application data through host bind mounts below the configured user's home directory:

| Service | Persistent host path | Default loopback port |
| --- | --- | --- |
| Miniflux | `~/.docker/miniflux/db/` (PostgreSQL database) | `8080` |
| TimeTagger | `~/.docker/timetagger/` | `8080` |
| Grav | `~/.docker/grav/data/` | `8080` |
| Forgejo | `~/.docker/forgejo/data/` | `3000` (HTTP), `2222` (SSH) |
| Portainer | `~/.docker/portainer/data/` | `9000` |
| TasmoAdmin | `~/.docker/tasmoadmin/data/` | `8016` |
| Wallabag | `~/.docker/wallabag/data/`, `~/.docker/wallabag/images/` | `8017` |
| Vaultwarden | `~/.docker/vaultwarden/` | `8018` |
| NocoDB | `~/.docker/nocodb/data/` | `8019` |
| Homepage | `~/.docker/homepage/config/` | `8020` |

The interfaces bind to `127.0.0.1` by default. The shared Docker helper renders Compose files under `~/<service>/` and user-level systemd units under `~/.config/systemd/user/`. A changed Compose file triggers an image pull; a changed Compose file or systemd unit triggers a service restart. No pull is performed when the Compose file is unchanged.

Service-specific behavior:

- **Miniflux** runs with a PostgreSQL companion container. Set its `postgres_version` and optional `port` in host data; credentials are supplied through `secrets.docker.miniflux`.
- **TimeTagger** mounts its persistent directory at the container's `/root/_timetagger`.
- **Grav** supports `image`, `port`, `channel`, `setup`, `scheduler` and `fix_permissions` options.
- **Forgejo** supports `image`, `port`, `ssh_port`, `ssh_server` and `domain`. HTTP and SSH bind to loopback by default.
- **Portainer** mounts the Docker socket, giving it administrative control over the Docker host. Keep its interface private or protect the reverse-proxy route with strong authentication.
- **TasmoAdmin** mounts its data at `/data/tasmoadmin` inside the container, matching `TASMO_DATADIR`.
- **Wallabag** uses SQLite, stores its database/application data and article images in the two host directories above, and disables public registration. Change the initial `wallabag` / `wallabag` account password immediately. The supplied local configuration publishes it through Caddy at `wallabag.21x9.org`.
- **Vaultwarden** disables public signups and invitations. Its optional `admin_token` secret must contain an Argon2 PHC hash, generated with `docker run --rm -it vaultwarden/server:latest /vaultwarden hash`. The supplied local configuration publishes it through Caddy at `vaultwarden.21x9.org`.
- **NocoDB** persists its application data in `~/.docker/nocodb/data/`, mounted at `/usr/app/data`. It supports `image`, `port` and `domain`; the supplied local configuration publishes it through Caddy at `nocodb.21x9.org`.
- **Homepage** persists its dashboard configuration in `~/.docker/homepage/config/`, mounted at `/app/config`. It supports `image`, `port` and `domain`; `domain` is passed to `HOMEPAGE_ALLOWED_HOSTS` and must contain the hostname (and port, if applicable), not a URL scheme. The supplied local configuration publishes it through Caddy at `homepage.21x9.org`. Docker socket integration is not enabled by default; configure a restricted socket proxy separately if container discovery is required. Since widgets can display sensitive data, protect the dashboard with reverse-proxy authentication, Homepage authentication, or a VPN.

**Migration note:** The current templates use host bind mounts. If a host was deployed while an earlier Wallabag or Vaultwarden template used Docker-managed named volumes, Compose does not migrate that data automatically. Back up and copy the named-volume contents into the corresponding host directory before switching. Data already present in the host directories is retained.

`docker` service configuration is independent of encrypted credentials. Put Miniflux credentials and the optional Vaultwarden admin-token hash in the encrypted secrets file; see [Secrets management](secrets.md).

### Caddy

`caddy_config` maps site addresses to Caddy directives consumed by `tasks/caddy.py`. The example uses TLS certificate paths and reverse-proxy destinations. Ensure the referenced certificates exist and that upstream services are reachable.

### Syncthing

Set `syncthing` to a dictionary to install Syncthing and enable its per-user systemd service (`syncthing@<username>`). The task uses the top-level `username` setting to select the service account and configures the GUI listen address through the Syncthing CLI. The GUI defaults to loopback-only (`127.0.0.1:8384`); change this only when remote access is deliberately secured, for example behind an authenticated reverse proxy or VPN.

```python
syncthing = {
    "gui_address": "127.0.0.1:8384",
}
```

The package creates the device identity and initial configuration on first start. Add remote devices and shared folders through the Syncthing GUI or its CLI/API; this task does not replace the generated device identity or overwrite the complete `config.xml`.

### Firewall

`ufw` maps supported application/service names to `Allow` or `Deny` actions. The current keys are `chromecast-dlna`, `kdeconnect`, `localsend` and `ssh` (TCP port 22); unsupported keys and values are ignored. The task sets default incoming traffic to deny and outgoing traffic to allow, applies the configured rules, and enables UFW. For example:

```python
ufw = {
    "ssh": "Allow",
    "kdeconnect": "Allow",
    "localsend": "Allow",
}
```

Review the effective rules before enabling changes on a remote host. The checked-in `group_data/@local.py` currently sets `ssh` to `Deny`; that example must not be copied to a remotely managed host unless another management path is available.

## Secrets-dependent configuration

The following features combine host data with encrypted secrets:

- WireGuard requires `wireguard_config` plus matching `secrets.wireguard` entries.
- dehydrated requires a `secrets.dehydrated` entry.
- Git credentials are deployed only when `secrets.git_credentials` is present.
- SSH key generation can use `secrets.ssh` passphrases.
- Miniflux uses `secrets.docker.miniflux` for credentials.
- Vaultwarden optionally uses `secrets.docker.vaultwarden.admin_token` for its Argon2 PHC admin-token hash.

The absence of `secrets.json.gpg` does not stop the whole deployment; `common.initialize()` sets an empty secrets dictionary. See [Secrets management](secrets.md) for the supported structure.

## Adding a host

1. Add a target entry to `_all_hosts` in `inventory.py`.
2. Add its name to `disabled_hosts` until it is ready, if you want to prevent accidental selection through `production`.
3. Create `group_data/<host>.py` with only the settings needed by that host.
4. Verify SSH and privilege escalation.
5. Run a dry deployment with a host limit and review every proposed operation.


## SSH client configuration

Set `ssh_config` to a mapping of OpenSSH `Host` patterns to configuration lines. The `tasks/ssh_config.py` task renders these entries into the configured user's `~/.ssh/config`.

The generated file begins with a hardened `Host *` baseline that applies to all destinations:

- `HashKnownHosts yes` hashes hostnames in `known_hosts`.
- `StrictHostKeyChecking accept-new` accepts and records new host keys, but rejects changed keys.
- `UpdateHostKeys yes` allows OpenSSH to learn additional host keys after a trusted connection.
- `PubkeyAuthentication yes` and `IdentitiesOnly yes` prefer explicitly configured public-key identities.
- `ForwardAgent no`, `ForwardX11 no`, `PermitLocalCommand no` and `ClearAllForwardings yes` disable common forwarding and local-command features.
- `ConnectTimeout 15`, `ServerAliveInterval 60` and `ServerAliveCountMax 3` bound connection setup and detect unresponsive peers.

The baseline is intentionally rendered before custom host entries. OpenSSH uses the first obtained value for most options, so later entries cannot override these baseline values. Other per-host settings remain available:

```python
ssh_config = {
    "github.com": """
  HostName github.com
  IdentityFile ~/.ssh/id_github
  User git
    """,
    "192.0.2.*": """
  User deploy
  Port 2222
    """,
}
```

When connecting to a new host, verify its fingerprint through a trusted channel where practical. `accept-new` protects against changed keys, but the first connection still relies on trusting the key presented at that time.
