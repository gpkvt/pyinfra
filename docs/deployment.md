# Deployment Workflow

Deployments are executed through **pyinfra** from the repository root.

## Prerequisites

- SSH connectivity and the required **sudo** permissions must be configured
  on remote hosts before deployment.
- Review the **inventory** and **host configuration** before executing.
  Provisioning can modify system packages, network settings, firewall
  policies, services, and user configuration.

## Basic execution

With the standard pyinfra CLI for this layout:

```bash
# Preview changes (the project explicitly promotes --diff)
pyinfra inventory.py deploy.py --diff

# Execute the deployment
pyinfra inventory.py deploy.py

# Target a single host
pyinfra inventory.py deploy.py @local

# Example with sudo and auto-confirm (pattern seen in the project's scripts)
pyinfra @local tasks/apt.py --sudo --diff -y
```

> **Verification note:** The exact deployment command in the project README
> could not be extracted verbatim at documentation time. The commands above
> follow upstream pyinfra CLI conventions (docs.pyinfra.com) and the
> `pyinfra @local tasks/apt.py --sudo --diff -y` pattern observed in the
> repository's scripts. Verify against the README before running.

## What gets deployed

`deploy.py` orchestrates task inclusion. **Core tasks are always included:**

- `apt`, `hosts`, `scripts`, `mc`, `git`

**Optional tasks** are included depending on available software, host
configuration, and configured secrets (conditions verbatim from `deploy.py`):

| Condition (from `deploy.py`) | Included task |
| --- | --- |
| Flatpak detected (`builtins.flatpak`, via `check_flatpak=True`) | `tasks/flatpak.py` |
| `host.data.ssh_config` | `tasks/ssh_config.py` |
| `host.data.wireguard_config` **and** `secrets.wireguard` | `tasks/wireguard.py` |
| `local_network_cidr` **and** `wireguard_interface` | `tasks/vpn.py` |
| `secrets.dehydrated` | `tasks/dehydrated.py` |
| `host.data.caddy_config` | `tasks/caddy.py` |
| `host.data.zsh` | `tasks/zsh.py` |
| `host.data.tmux` | `tasks/tmux.py` |
| `host.data.powerline` | `tasks/powerline.py` |
| `host.data.ufw` | `tasks/ufw.py` |
| `host.data.docker` | `tasks/docker.py` |
| `host.data.apparmor_profiles` | `tasks/apparmor.py` |
| `host.data.cosmic` | `tasks/cosmic/deploy.py` |

Because missing secrets simply leave `secrets` empty, dropping
`secrets.json.gpg` cleanly disables all secret-dependent features instead of
failing the deployment.

## Recommended workflow

1. **Dry run**: `--diff` to review the intended changes.
2. **Apply**: run without `--diff`.
3. **Inspect**: pyinfra reports per-host, per-operation changed/unchanged
   status.
4. **Iterate**: adjust `group_data/` flags and re-run — deployments are
   idempotent by pyinfra design.
