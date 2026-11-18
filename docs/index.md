# pyinfra

<div class="site-hero" markdown>
  <div class="site-eyebrow">A PRACTICAL PYINFRA DEPLOYMENT</div>
  <h1>One repo.<br><span>Linux, under control.</span></h1>
  <p class="site-lead">A reusable automation toolkit for Debian and Ubuntu servers, Docker applications and Linux workstations — built with Python and upstream pyinfra.</p>
  <p><a class="site-button" href="deployment/">Get started</a> <a class="site-button site-button-secondary" href="https://github.com/gpkvt/pyinfra">View source on GitHub</a></p>
  <div class="site-meta">Python 3.12+ · Debian &amp; Ubuntu · MIT · SSH or local execution</div>
</div>

## What this repository is

This repository is an opinionated collection of deploys, task modules, templates and host data. It is **not** the upstream pyinfra project and it is not a prebuilt server image. You choose the target, configure the features, preview the plan and apply it.

<div class="site-cards" markdown>
  <a href="docker/" class="site-card">
    <span class="site-number">01 / FEATURED</span>
    <h3>Docker applications</h3>
    <p>Compose stacks, host-side persistent data, systemd lifecycle, reverse proxy integration and optional on-demand startup.</p>
    <strong>Explore Docker →</strong>
  </a>
  <a href="tasks-overview/" class="site-card">
    <span class="site-number">02 / TASK LIBRARY</span>
    <h3>Linux system &amp; workstation</h3>
    <p>Packages, SSH, users, firewall, VPN, Flatpak, COSMIC, power, backups, hardware and developer tools.</p>
    <strong>Explore tasks →</strong>
  </a>
  <a href="configuration/" class="site-card">
    <span class="site-number">03 / CONFIGURATION</span>
    <h3>One configuration model</h3>
    <p>Python inventory, host/group data, feature gates, Jinja templates and encrypted secrets.</p>
    <strong>Configure a host →</strong>
  </a>
</div>

## Docker, without hidden storage

The Docker tasks deploy opt-in Compose applications and keep their configuration and persistent data below `~/.docker/<service>/` for the configured user.

- **Host bind mounts** for persistent application data; no Docker-managed named volumes.
- **Loopback-first ports** for web interfaces, intended for a trusted reverse proxy or VPN.
- **systemd user services** for predictable start, stop and restart behavior.
- **Change-aware reconciliation** so unchanged Compose files do not trigger unnecessary image pulls.
- **Encrypted credentials** supplied from the GPG secrets file, not committed host data.

The catalog currently documents 18 services, including Forgejo, Homepage, Linkwarden, Paperless-ngx, Firefly III, AppFlowy, MDMesh, AdGuard Home, Vaultwarden and WG-Easy. See the [Docker guide](docker/) for ports, storage paths, prerequisites and service-specific settings.

## How it fits together

<div class="site-flow" markdown>
  <div><b>1 · Inventory</b><span>Choose local or SSH targets</span></div>
  <div><b>2 · Host data</b><span>Set desired state and feature flags</span></div>
  <div><b>3 · Deploy</b><span>Compose reusable Python tasks</span></div>
  <div><b>4 · Review &amp; apply</b><span>Preview changes, then converge</span></div>
</div>

```bash
# Install the project environment
uv sync
source .venv/bin/activate

# Review the proposed changes first
pyinfra inventory.py deploy.py --dry --diff

# Apply only after checking the plan
pyinfra inventory.py deploy.py --diff
```

Tasks are designed to be idempotent: a second run against an already-correct host should not report changes or repeat unnecessary work. Dry runs are a review aid, not a replacement for backups or testing.

## The engine: upstream pyinfra

[pyinfra](https://pyinfra.com/) is the independent, open-source Python automation engine maintained at [pyinfra-dev/pyinfra](https://github.com/pyinfra-dev/pyinfra). It turns Python deploy code into commands for local machines and remote hosts, using inventory, facts, operations and connectors.

This repository uses that engine; it does not fork or redefine it. Learn the distinction and find upstream documentation on the [Upstream pyinfra page](upstream/).

## Find your way

- [Task overview](tasks-overview/) — the main task families.
- [Complete feature reference](feature-reference/) — every task module and feature gate.
- [Docker services](docker/) — service catalog, ports, storage and lifecycle.
- [Configuration](configuration/) — inventory and host/group settings.
- [Deployment](deployment/) — safe preview and execution.
- [Secrets](secrets/) — GPG-encrypted credentials.
- [Architecture](architecture/) — repository structure and execution flow.
- [Changelog](changelog/) — project changes.

<div class="site-warning" markdown>
**Before deploying:** the example inventory and host data are templates, not production-ready settings. Review target hosts, SSH access, firewall rules, ports, secrets and every proposed diff. Some tasks can change networking or security policy and may interrupt access.
</div>
