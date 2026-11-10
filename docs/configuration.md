# Host configuration

Host-specific desired state is stored as Python data in `group_data/`. pyinfra exposes the values for a target through `host.data`. The supplied `group_data/@local.py` is an example configuration for one environment, not a portable default. Audit and adapt it before running any deployment.

## Which files are used?

The inventory target name determines its host-data file: the local target uses `group_data/@local.py`, and a target named `web01` uses `group_data/web01.py`. Inventory groups can add shared configuration for a role or class of hosts. For example, `workstation = ["@local"]` in `inventory.py` makes `@local` a member of the `workstation` group, so pyinfra also loads `group_data/workstation.py`. Group data and host data are both available through `host.data`; keep role-wide defaults in the group file and host-specific overrides in the host file.

The workstation group is optional. Add a host to the `workstation` inventory group only if it should receive that role's configuration and eligible workstation tasks.

Keep configuration data separate from task logic. Put private keys, passwords, API tokens and credential-bearing URLs in the encrypted secrets file, not in group data. See [Secrets management](secrets.md).

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

Review the checked-in role defaults before deploying: backup tools and power/hardware/storage utilities are enabled in the supplied example. In particular, the backup task only installs tools and deploys a Borgmatic configuration template; it does not configure repository credentials or schedule backups.

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
| `zsh` | `tasks/zsh.py` | Truthy enablement value. |
| `tmux` | `tasks/tmux.py` | Truthy enablement value. |
| `powerline` | `tasks/powerline.py` | Truthy enablement value. |
| `powerline_fonts` | `tasks/fonts.py` | Boolean-like flag for optional patched fonts. |
| `cosmic` | `tasks/cosmic/deploy.py` | COSMIC desktop configuration dictionary. |
| `vscodium` | `tasks/vscodium.py` | Extension configuration dictionary. |
| `mullvad_extensions` | `tasks/mullvad_extensions.py` | Extension IDs and download URLs. |
| `mullvad_browser_dir` | `tasks/mullvad_extensions.py` | Browser distribution directory; task default is `/usr/lib/mullvad-browser/distribution`. |
| `proton` | `tasks/proton.py` | Proton application selection and options. |

## Service configuration

### Docker

`docker` is a mapping of service names to service-specific settings. The repository currently includes service modules for Miniflux, TimeTagger and Grav. Example keys in the supplied configuration include ports, image, database version and service-specific setup options. Consult the relevant `tasks/docker/` module and Compose template before adding or changing keys; the schema is service-specific.

### Caddy

`caddy_config` maps site addresses to Caddy directives consumed by `tasks/caddy.py`. The example uses TLS certificate paths and reverse-proxy destinations. Ensure the referenced certificates exist and that upstream services are reachable.

### Firewall

`ufw` maps application/profile names to policy actions used by `tasks/ufw.py`. Review the installed UFW application profiles and rules before enabling changes on a remote host.

## Secrets-dependent configuration

The following features combine host data with encrypted secrets:

- WireGuard requires `wireguard_config` plus matching `secrets.wireguard` entries.
- dehydrated requires a `secrets.dehydrated` entry.
- Git credentials are deployed only when `secrets.git_credentials` is present.
- SSH key generation can use `secrets.ssh` passphrases.
- Miniflux uses `secrets.docker.miniflux` for credentials.

The absence of `secrets.json.gpg` does not stop the whole deployment; `common.initialize()` sets an empty secrets dictionary. See [Secrets management](secrets.md) for the supported structure.

## Adding a host

1. Add a target entry to `_all_hosts` in `inventory.py`.
2. Add its name to `disabled_hosts` until it is ready, if you want to prevent accidental selection through `production`.
3. Create `group_data/<host>.py` with only the settings needed by that host.
4. Verify SSH and privilege escalation.
5. Run a dry deployment with a host limit and review every proposed operation.
