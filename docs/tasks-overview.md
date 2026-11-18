# Task library

This repository groups reusable pyinfra tasks into four practical areas. Most optional features are selected through host or group data; they are not all enabled by default.

<div class="site-cards" markdown>
  <a href="tasks/#core-tasks" class="site-card">
    <span class="site-number">01 / BASELINE</span>
    <h3>System foundations</h3>
    <p>APT, hosts, sudo, hostname, locale, sysctl, udev, SSH keys, Git, fonts and user scripts.</p>
    <strong>Core task reference →</strong>
  </a>
  <a href="docker/" class="site-card">
    <span class="site-number">02 / CONTAINERS</span>
    <h3>Docker applications</h3>
    <p>18 documented Compose services with bind-mounted state, systemd lifecycle and optional integrations.</p>
    <strong>Docker service catalog →</strong>
  </a>
  <a href="tasks/#optional-tasks" class="site-card">
    <span class="site-number">03 / OPTIONAL</span>
    <h3>Network &amp; services</h3>
    <p>WireGuard, conditional VPN, Syncthing, Samba, UFW, Caddy, Dehydrated, AppArmor and Flatpak.</p>
    <strong>Optional task reference →</strong>
  </a>
  <a href="feature-reference/#workstation-role-features" class="site-card">
    <span class="site-number">04 / WORKSTATION</span>
    <h3>Desktop &amp; hardware</h3>
    <p>COSMIC settings, backups, power management, firmware, storage, peripherals, LiMusic and developer tools.</p>
    <strong>Workstation features →</strong>
  </a>
</div>

## Docker at a glance

Docker is a major part of this repository. Set the `docker` host-data mapping to opt in. The shared tasks install/configure Docker and dispatch the service modules selected in that mapping.

- Compose files and persistent data live under `~/.docker/<service>/`.
- Persistent storage uses host bind mounts; Docker-managed named volumes are not used.
- Web interfaces bind to loopback by default where applicable.
- User systemd units manage Compose project lifecycle.
- Sablier can provide on-demand startup; a separate battery monitor can stop/restore selected containers. They are mutually exclusive.

See [Docker services](docker/) for the service catalog, ports, data paths, secrets and operational behavior.

## Configuration and safety

Optional task inclusion is controlled by `deploy.py` and host/group data. Start with the [configuration guide](configuration/), inspect the [complete feature reference](feature-reference/) and run a [dry deployment](deployment/) before applying changes.

The [complete feature reference](feature-reference/) indexes every Python module under `tasks/`, including feature gates and important limitations. It is the detailed index; this page is the short orientation.
