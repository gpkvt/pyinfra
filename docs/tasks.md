# Task reference

Run a consistent infrastructure workflow from one inventory: pyinfra's task modules turn host and group data into repeatable system configuration. Core tasks establish the baseline, optional tasks add services only when enabled, and workstation roles keep desktop-specific tooling separate.

<div class="docker-stats tasks-stats">
<div class="docker-stat"><span class="docker-stat-value">Core</span><span class="docker-stat-label">baseline on every full deployment</span></div>
<div class="docker-stat"><span class="docker-stat-value">Opt-in</span><span class="docker-stat-label">optional features behind data gates</span></div>
<div class="docker-stat"><span class="docker-stat-value">Per host</span><span class="docker-stat-label">host and group configuration</span></div>
<div class="docker-stat"><span class="docker-stat-value">Repeatable</span><span class="docker-stat-label">change-aware deployment operations</span></div>
</div>

## Task groups

<div class="docker-info-grid tasks-groups">
<div class="docker-info-card">
<strong>Core baseline</strong>
<p>Packages, system settings, users' SSH and Git configuration, scripts, fonts and other essentials included in every full deployment.</p>
</div>
<div class="docker-info-card">
<strong>Optional features</strong>
<p>WireGuard, VPN activation, firewall rules, Docker services, Syncthing, Proton apps, browser extensions and other capabilities enabled through host data.</p>
</div>
<div class="docker-info-card">
<strong>Workstation role</strong>
<p>Explicitly enabled desktop and hardware features such as power management, firmware tools, storage utilities, peripherals and COSMIC settings.</p>
</div>
<div class="docker-info-card">
<strong>Focused task runs</strong>
<p>Run an individual task module for diagnosis or targeted work, while keeping the full deployment entry point for normal provisioning.</p>
</div>
</div>

## How tasks are applied

<div class="docker-flow tasks-flow">
<div><b>01 · Inventory</b><p>Inventory membership and host/group data define the target machines and their desired configuration.</p></div>
<div><b>02 · Gate</b><p><code>deploy.py</code> always includes core modules and evaluates feature flags before loading optional modules.</p></div>
<div><b>03 · Configure</b><p>Task modules use pyinfra operations and templates to install packages and manage system or user configuration.</p></div>
<div><b>04 · Reconcile</b><p>Change-aware operations avoid unnecessary restarts and updates; rerunning deployment converges toward the same state.</p></div>
</div>

## Configuration model

Feature selection belongs in host or group data, not in edits to the task modules. Optional task gates are evaluated by `deploy.py`; workstation features additionally require their nested `enabled: True` setting.

```python
# Example host/group data
wireguard_config = {...}  # enables WireGuard configuration
syncthing = True          # enables Syncthing
workstation = {
    "power": {
        "enabled": True,
        "manager": "tlp",
    },
}
```

Keep credentials and other sensitive values in the encrypted secrets file. Review each feature's configuration and operational notes before enabling it, especially for network access, firewall policy, VPN routing and privileged containers.

## Task reference

The sections below describe the task modules, their inclusion conditions and the configuration keys they consume. Treat the implementation and templates as authoritative when checking accepted values or exact behavior.

## Core tasks

These task modules are included on every full deployment.

| Module | Responsibility | Main configuration |
| --- | --- | --- |
| `tasks/apt.py` | Downloads configured repository keys, writes APT source lists, updates package indexes, upgrades packages when the index changes, and installs packages. | `apt_sources`, `apt_packages` |
| `tasks/hosts.py` | Manages `/etc/hosts` mappings. | `hostnames` |
| `tasks/sudo.py` | Writes custom sudoers rules to `/etc/sudoers.d/99-local`, validates with `visudo`, and sets restrictive permissions. | `sudoers_rules` |
| `tasks/system.py` | Manages hostname, timezone, locale, editor environment, keyboard, sysctl, udev and USBGuard. | See [System configuration](system.md). |
| `tasks/ssh_keys.py` | Generates supported SSH keypairs only when both files are absent and manages authorized keys. Existing private keys are never overwritten; an incomplete keypair (only the private or public file exists) fails safely and requires manual repair. | `ssh_keys`, `ssh_authorized_keys`, `secrets.ssh` |
| `tasks/git.py` | Installs/configures Git and deploys Git-related configuration and credentials when available. | Git host data and `secrets.git_credentials` |
| `tasks/fonts.py` | Installs font packages; optionally downloads Powerline-patched fonts. | `powerline_fonts` |
| `tasks/scripts.py` | Synchronizes `files/scripts/` into the configured user's scripts directory and creates command links. This includes `gpg-vault`, the helper for managing `secrets.json.gpg`. Existing destination files not in the source are preserved. | `username`, `usergroup` |
| `tasks/mc.py` | Installs and configures Midnight Commander. | `username`, `usergroup` |

## Optional tasks

| Module | Inclusion condition | Responsibility |
| --- | --- | --- |
| `tasks/flatpak.py` | Flatpak executable detected during initialization | Installs configured Flatpak application IDs exclusively in the user's Flatpak installation, explicitly preferring the user-scoped Flathub remote when an app is available from multiple remotes; uses a sole alternative user remote when necessary, skips already-installed user apps, and updates/cleans up only user-scoped applications and runtimes. |
| `tasks/ssh_config.py` | `ssh_config` | Renders the user's SSH client configuration with a hardened global baseline followed by configured host entries. |
| `tasks/wireguard.py` | `wireguard_config` and `secrets.wireguard` | Installs WireGuard and writes `/etc/wireguard/<interface>.conf`; does not start the service. |
| `tasks/vpn.py` | `local_network_cidr` and `wireguard_interface` | Enables/starts `wg-quick@<interface>` when the host is outside the configured IPv4 network. |
| `tasks/caddy.py` | `docker` and `caddy_config` | Builds and deploys the Docker-based Caddy image with the Sablier plugin and Dehydrated/Hetzner DNS-01 certificate renewal. |
| `tasks/syncthing.py` | `syncthing` | Installs Syncthing, enables `syncthing@<username>`, and configures its GUI listen address (loopback by default). Device and folder sharing is configured separately in Syncthing. |
| `tasks/zsh.py` | `zsh` | Installs/configures Zsh and `playerctl`, deploys a LiMusic-specific MPRIS helper, and displays the current track in HyFetch only while LiMusic is playing. The helper forces a UTF-8 locale for `playerctl` metadata so non-ASCII track names also work when Neowofetch runs with `LC_ALL=C`. |
| `tasks/tmux.py` | `tmux` | Deploys tmux configuration. |
| `tasks/powerline.py` | `powerline` | Deploys Powerline prompt configuration. |
| `tasks/ufw.py` | `ufw` | Applies configured UFW application, port and custom rules. Rejects unknown rule names, invalid actions and malformed custom-rule definitions instead of silently skipping firewall configuration. |
| `tasks/docker.py` and `tasks/docker_container.py` | `docker` | Installs Docker, defines the shared Compose/systemd deployment helper, and dispatches configured container services, including AppFlowy. |
| `tasks/docker_power.py` | `docker` | Deploys the Docker battery monitor and its systemd unit; validates configured `docker_power_save` container names before writing its shell configuration; disables the monitor and restores previously stopped containers when Sablier is enabled. |
| `tasks/docker_sablier.py` | `docker` and `docker_sablier.enabled` | Deploys Sablier as a Docker container using the Docker provider and enables on-demand startup through Compose labels. It is mutually exclusive with the Docker battery monitor. |
| `tasks/apparmor.py` | `apparmor_profiles` | Loads/enforces configured AppArmor profiles. |
| `tasks/workstation/cosmic/deploy.py` | `cosmic` | Deploys explicitly enabled COSMIC appearance, window-management, input, custom-shortcut, panel, dock and workspace settings. Display/output configuration is intentionally excluded. |

Use `python files/scripts/export_cosmic_config.py --dry-run` to preview supported live COSMIC settings before updating `group_data/@local.py`; omit `--dry-run` to apply the update. The exporter reads only settings managed by the COSMIC tasks, preserves management flags and unrelated host data, and leaves settings it cannot reliably reconstruct unchanged (including the numeric `anchor_gap` value).
| `tasks/mullvad_extensions.py` | `mullvad_extensions` | Downloads configured browser extensions and deploys `user.js`. |
| `tasks/vscodium.py` | `vscodium` | Installs configured VSCodium extensions that are not already installed. |
| `tasks/proton.py` | `proton` | Installs/configures selected Proton applications using the configured distribution sources. |
| `tasks/cron.py` | Non-empty `cron_jobs` | Installs the cron package, ensures the daemon is enabled/running, and manages named user/root crontab entries. |

## Workstation role tasks

The modules below are included by `deploy.py` only when the matching nested setting under `host.data.workstation` has `enabled: True`. Their shared defaults are defined in `group_data/workstation.py`; inventory membership determines which hosts receive that group data.

| Module | Responsibility | Configuration |
| --- | --- | --- |
| `tasks/workstation/backup.py` | Installs Restic, Borg, rsync and Borgmatic; renders `/etc/borgmatic/config.yaml`. It does not create, schedule or run backups. | `workstation.backup.enabled` |
| `tasks/workstation/power.py` | Installs/enables TLP or Power Profiles Daemon and removes the conflicting manager. | `workstation.power.enabled`, `workstation.power.manager` |
| `tasks/workstation/hardware.py` | Installs fwupd and optional CPU microcode. Firmware updates are not applied automatically. | `workstation.hardware.enabled`, `workstation.hardware.cpu_vendor` (`intel`, `amd` or unset) |
| `tasks/workstation/storage.py` | Installs `smartmontools` and `nvme-cli`; does not configure polling or alerting. | `workstation.storage.enabled` |
| `tasks/workstation/peripherals.py` | Installs optional printer/scanner packages; enables CUPS when printing is selected. | `workstation.peripherals.enabled`, `printing`, `scanning` |
| `tasks/workstation/desktop.py` | Installs common desktop integration utilities. A custom package list replaces the defaults. | `workstation.desktop.enabled`, optional `packages` list |
| `tasks/workstation/maintenance.py` | Installs `needrestart`, `debian-goodies` and `apt-file`; does not enable unattended upgrades or schedule reboots. | `workstation.maintenance.enabled` |
| `tasks/workstation/limusic.py` | Installs the latest stable Limusic x86-64 AppImage, verifies its published SHA-256 digest, deploys the matching upstream icon and creates a user-level desktop launcher discoverable by COSMIC. The AppImage retains its self-updater. | `workstation.limusic.enabled` |

The tracked `group_data/workstation.py.example` disables every workstation feature by default. Copy it to the ignored `group_data/workstation.py` and explicitly enable the features required by each host. Review the group data before assigning additional hosts to the workstation group. Limusic is also disabled by default; set `workstation.limusic.enabled = True` to install it for the configured user. The task uses the latest stable x86-64 AppImage from [Limusic releases](https://github.com/SimoHypers/limusic/releases), checks the release-published SHA-256 digest, installs the matching application icon under `~/.local/share/icons/`, and writes `~/.local/share/applications/limusic.desktop` so COSMIC can find it. The AppImage is stored in `~/.local/opt/limusic/` and keeps Limusic's built-in updater; the task downloads a new stable release only when the release tag changes.


### Cron jobs

Define jobs in the host or group data key `cron_jobs`. The list is empty by default, so hosts without configured jobs do not install or enable cron. Each entry requires a stable `name`, a single-line `command`, and at least one schedule field (`minute`, `hour`, `day_of_month`, `month`, `day_of_week`, or `special_time`). The schedule fields accept the same values as pyinfra's `crontab.crontab` operation, including lists and cron expressions such as `"*/15"`.

- `scope: "user"` (default) manages the crontab of the configured `username`.
- `scope: "root"` manages root's crontab.
- `present: False` removes the named job; keep its `name` and `command` in the configuration while removing it.
- The stable `name` is stored as pyinfra's `cron_name`, so changing a command or schedule updates the existing entry instead of adding a duplicate.
- The task installs the Debian/Ubuntu `cron` package and ensures the `cron` service is enabled and running whenever the list contains jobs. Both scopes are managed through sudo, so the deployment account needs suitable sudo privileges.
- Duplicate names within the same target user's crontab, multiline names/commands and unknown configuration fields are rejected.

Example:

```python
cron_jobs = [
    {
        "name": "daily-cleanup",
        "command": "/usr/local/bin/cleanup.sh",
        "scope": "user",
        "special_time": "@daily",
    },
    {
        "name": "system-maintenance",
        "command": "/usr/local/sbin/maintenance.sh",
        "scope": "root",
        "minute": 0,
        "hour": 4,
    },
]
```

## Feature notes

### Linkwarden bookmarks in Homepage

When both `docker.linkwarden` and `docker.homepage` are configured and `secrets.docker.homepage.environment.HOMEPAGE_VAR_LINKWARDEN_API_KEY` is present, `tasks/docker/linkwarden_bookmarks.py` runs on the pyinfra controller before Homepage is rendered. It retrieves the authenticated account’s paginated Linkwarden search results, groups URL bookmarks by collection, and updates only the marked managed section in `group_data/@local.py`. Favicons are stored in `files/homepage/icons/` and deployed by the existing additive Homepage icon sync. Manual bookmarks outside the managed section are preserved. Run `python tasks/docker/linkwarden_bookmarks.py --dry-run` from the repository checkout to preview the generated groups; this fetches the API data but does not download favicons or modify files. Run the same command without `--dry-run` to perform the synchronization manually. API or pagination failures abort synchronization before the managed bookmarks are changed; unavailable favicons are simply omitted. The controller therefore needs network access to the configured Linkwarden domain and write access to the repository checkout. Reuse the existing Homepage Linkwarden widget API key from the encrypted secrets file; no additional token is needed. Configure `docker.linkwarden.blacklist` in `group_data/@local.py` with Linkwarden bookmark IDs (integers or strings) to omit selected bookmarks. IDs are matched against each API result’s `id` field; URLs are never used as blacklist keys. The default empty list synchronizes all eligible bookmarks. Remove an ID from the list to restore that bookmark on the next run.

### GPG secret utility

`tasks/scripts.py` deploys `files/scripts/gpg-vault` with the other user scripts and creates its command link. The helper provides `create`, `edit`, `view`, `encrypt`, `decrypt`, `rekey` and `status`; see [Secrets management](secrets.md). It is not invoked by `deploy.py`: `common.initialize()` remains responsible for decrypting `secrets.json.gpg` during deployment.

### UFW firewall

`tasks/ufw.py` supports the `chromecast-dlna`, `kdeconnect` and `localsend` application profiles plus `ssh` (TCP port 22). These entries accept `Allow` or `Deny` string values. Additional custom rules use a dictionary with an `action` and a `rule` string containing UFW arguments. Existing custom rules are read from `ufw show added` and compared before changes, including normalization of the optional `in` token, to keep deployments idempotent. Invalid entries are ignored. The task sets default incoming policy to deny and outgoing policy to allow, applies configured rules, and then enables UFW. Review firewall changes and ensure a recovery path before applying them remotely; the supplied local configuration sets `ssh` to `Deny`.

### APT

Repository definitions include a signing-key URL and destination plus repository URL, distribution, components and optional architectures/types. Review third-party repository configuration carefully: adding a repository delegates package trust to that repository's signing key and publishing process.

### SSH keys and client hardening

The key task supports Ed25519 and RSA key generation; RSA keys must be at least 3072 bits. Private keys are not overwritten when they already exist. Passphrases can be supplied through `secrets.ssh`. Keep backups of keys and verify authorized-key changes before removing access paths.

The SSH client task writes a global `Host *` baseline before the configured `ssh_config` host entries. It enables `HashKnownHosts`, `StrictHostKeyChecking accept-new`, `UpdateHostKeys`, and public-key authentication; disables agent forwarding, X11 forwarding, local commands and configured forwarding; and sets connection timeout/keepalive values. With OpenSSH's first-obtained-value behavior, these baseline options take precedence over later host-specific entries. `accept-new` automatically records previously unseen host keys but still rejects changed keys; verify host fingerprints through a trusted channel when onboarding sensitive systems.

### WireGuard and VPN activation

The WireGuard task installs the package and renders one file per configured interface. The VPN task is separate: it uses pyinfra's `hardware.Ipv4Addrs` fact, excludes loopback, link-local and unspecified addresses to match globally scoped IPv4 detection, compares the remaining addresses with `local_network_cidr`, and enables/runs the configured `wg-quick@...` service when outside that network. IPv6 is not considered by the network-detection check.

### Docker services

Docker is an optional feature enabled by a truthy `docker` mapping in host data. `tasks/docker.py` installs Docker and defines the shared Compose/systemd helper; `tasks/docker_container.py` dispatches each configured service module.

The deployment helper renders Compose projects below `~/.docker/<service>/` and user-level systemd units below `~/.config/systemd/user/`. Changed Compose files trigger image pulls and service reconciliation; unchanged files do not trigger pulls. Additional generated assets can register precise restart triggers. Sablier changes preparation to `docker compose up --no-start` and starts labelled applications on demand.

All persistent service data uses direct host-directory bind mounts below `~/.docker/`; Docker-managed named volumes are not used. See the dedicated [Docker services guide](docker.md) for the service catalog, ports, storage paths, lifecycle, security and service-specific configuration notes.

### Browser and editor extensions

Mullvad extension downloads are defined by extension IDs and URLs. The supplied local configuration includes Wallabagger for connecting the browser to the self-hosted Wallabag instance. VSCodium extension installation is additive: already-installed extensions are detected and left in place. Review external download sources before enabling either task.

### Proton

The Proton task supports components selected through the `proton` configuration, including Mail, Mail Bridge, VPN, Pass and Drive CLI. Installation source varies by component and configuration; consult `tasks/proton.py` for the exact current options. When Drive CLI installation is enabled, set `proton.drive_cli_version` explicitly; deployment fails if it is missing or empty. The deprecated misspelled `proton.drive_cll_version` setting is no longer accepted.

## On-demand Samba file exchange

`tasks/samba.py` | `samba.enabled` | Installs Samba with guest `Upload` and read-only `Download` shares, but leaves `smbd` stopped and masked. The `samba-start` and `samba-stop` scripts manage TCP 445 UFW rules and service lifecycle. Optional `samba.idle_timeout` enables automatic shutdown after a period without SMB traffic. See [Samba configuration and security](samba.md).

## Run an individual task

For diagnosis or focused testing, pyinfra can run a task file directly. Example:

```bash
pyinfra inventory.py tasks/system.py --dry --diff
```

A task run directly may not have all initialization or feature-gate behavior of `deploy.py`; inspect whether the task initializes shared state itself. Prefer the full entry point for normal provisioning.


### On-demand Docker services

On-demand startup is controlled by `docker_sablier`. The tracked `group_data/@local.py.example` disables Sablier by default and documents a 15-minute default session for when it is enabled. Browser-facing routes use Sablier's dynamic strategy by default: while an idle service resumes or starts, Sablier immediately serves a themed loading page that periodically checks readiness and then redirects the browser to the requested URL. The default theme is `ghost`, details are shown, and the page refreshes every five seconds. Dynamic mode avoids holding the original browser request open, so Caddy no longer has a global two-minute response write deadline. Only Caddy reverse-proxy routes whose loopback port matches a configured Docker service are wrapped; unmatched routes remain unchanged.

Sablier runs as a Docker container using its Docker provider and the Docker socket. Caddy runs in a custom Docker image containing the Sablier Caddy plugin. Caddy uses host networking so existing loopback reverse-proxy upstreams continue to work. Dehydrated runs inside the Caddy container and uses the Hetzner DNS-01 hook; set `secrets.dehydrated.hetzner_api_token` in the encrypted secrets file.

Each Compose workload is prepared with `docker compose up --no-start`. This creates missing containers and reconciles changed Compose configuration (including Sablier labels) without starting on-demand services. Existing container labels are checked against the generated override; label drift forces a Compose recreation and restarts the user systemd unit so the workload is brought back up with the corrected labels. This is required because Docker container labels are immutable after creation. Sablier resumes a paused or starts a stopped labelled application container when a matching request arrives. Sablier follows Compose `depends_on` metadata to start required dependencies in order. Dependencies that should share the application's idle lifecycle must also carry `sablier.enable=true` and the same group.

The `sablier_services` list under a service's `docker.<service>` configuration declares every Compose service to pause or stop together when its session expires. It defaults to `app_services`, so dependencies remain running unless explicitly included. One-shot containers must not be included. Add database and supporting service names when they should share the application's idle-session lifecycle.

The separate `app_services` list identifies application containers for systemd stop behavior. `stop_dependencies` controls whether manually stopping the user systemd unit stops the complete Compose project or only those application containers; it does not control Sablier's idle-session behavior.

Per-service overrides remain available under `docker.<service>.sablier`. Supported options include `enabled`, `group`, `session_duration`, `strategy`, `display_name`, `theme`, `show_details` and `refresh_frequency`. The global defaults are `strategy: dynamic`, `theme: ghost`, `show_details: True` and `refresh_frequency: 5s`. Set `enabled: False` to keep a service outside Sablier management. Use `strategy: blocking` for clients that cannot handle the dynamic HTML waiting page; `blocking_timeout` remains configurable globally and per service for that strategy. Homepage is managed by Sablier by default; only its configured widget API paths bypass Sablier so dashboard widgets can retrieve data without waking the target services.

Caddy performs the initial Dehydrated run before starting its server. A user-level systemd timer runs daily at 03:00 and invokes the renewal script inside the container with `docker exec`; `Persistent=true` catches a missed run after downtime. The script reloads Caddy only when certificate fingerprints change. The image creates the `/etc/dehydrated/conf.d` directory configured by `CONFIG_D`, and the Hetzner hook safely handles both numeric and textual `exit_hook` arguments. The Caddy Compose service has a health check against its local admin API, and pyinfra waits for it to become healthy after a recreation. After the health check, pyinfra compares the deployed Caddyfile checksum with a marker stored in the persistent `/config` bind mount. A missing or mismatched marker triggers Caddyfile validation and a reload; the marker is updated atomically only after both commands succeed. This makes a skipped or failed reload retry on the next deployment even when the template itself reports no change, while an unchanged acknowledged configuration avoids unnecessary reloads. A newly started Caddy container reads its mounted Caddyfile at startup. Pyinfra checks each preceding file operation's `did_change()` result before enabling the renewal-timer, image-build, container-start or health-wait operation; an unchanged, present image and healthy container do not trigger these operations.

Caddy's entrypoint starts with the minimal `NET_BIND_SERVICE`, `SETUID` and `SETGID` capabilities, runs Dehydrated at startup and on its daily timer as the configured deployment user, then starts Caddy as that same non-root user with only the ambient `NET_BIND_SERVICE` capability needed for ports 80 and 443. The Compose service drops all other capabilities and keeps `no-new-privileges` enabled. Caddy's persistent configuration, Dehydrated state, certificates, data and runtime state use explicit host bind mounts from directories below `~/.docker/caddy/`. Sablier and Caddy are deployed only when Docker and their corresponding configuration gates are enabled. Existing host Caddy installations are not migrated, stopped, or uninstalled automatically; prepare ports 80 and 443 manually before enabling the Docker-based Caddy service.

Sablier and the Docker battery saver are mutually exclusive. The global `docker_sablier.provider_strategy` defaults to `pause`: idle containers are frozen and resume quickly on the next request, but continue consuming RAM. Set it to `stop` to release their memory at the cost of a cold start. Sablier applies this strategy to every managed Docker container; it cannot select pause or stop per service. Sablier 1.20.0 has no built-in delayed stop after a pause, so a one-hour pause-then-stop lifecycle is not configured here. When Sablier is enabled, the battery monitor is stopped and disabled, and containers previously stopped by the battery saver are restored first. Disabling Sablier re-enables the battery monitor.
