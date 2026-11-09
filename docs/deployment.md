# Deployment Workflow

Deployments are executed through **pyinfra** from the repository root.

## Prerequisites

- SSH connectivity and the required **sudo** permissions must be configured on remote hosts before deployment.
- Review the **inventory** and **host configuration** before executing.
- Provisioning can modify system packages, network settings, firewall policies, services, and user configuration.

## Basic execution

With the standard pyinfra CLI for this layout:

bash

```bash
# Preview changes
pyinfra inventory.py deploy.py --diff --dry

# Execute the deployment
pyinfra inventory.py deploy.py --diff

# Target a single host
pyinfra inventory.py deploy.py --limit @local

# Example with sudo and auto-confirm
pyinfra @local tasks/apt.py --sudo --diff -y
```

## What gets deployed

`deploy.py` orchestrates task inclusion.

**Core tasks are always included:**

- `tasks/apt.py`
- `tasks/hosts.py`
- `tasks/sudo.py`
- `tasks/system.py`
- `tasks/ssh_keys.py`
- `tasks/git.py`
- `tasks/fonts.py`
- `tasks/scripts.py`
- `tasks/mc.py`

**Optional tasks** are included depending on available software, host configuration, and configured secrets:

| Condition | Included task |
| --- | --- |
| Flatpak detected (`builtins.flatpak`, via `check_flatpak=True`) | `tasks/flatpak.py` |
| `host.data.ssh_config` | `tasks/ssh_config.py` |
| `host.data.wireguard_config` and `secrets.wireguard` | `tasks/wireguard.py` |
| `local_network_cidr` and `wireguard_interface` | `tasks/vpn.py` |
| `secrets.dehydrated` | `tasks/dehydrated.py` |
| `host.data.caddy_config` | `tasks/caddy.py` |
| `host.data.zsh` | `tasks/zsh.py` |
| `host.data.tmux` | `tasks/tmux.py` |
| `host.data.powerline` | `tasks/powerline.py` |
| `host.data.ufw` | `tasks/ufw.py` |
| `host.data.docker` | `tasks/docker.py` |
| `host.data.apparmor_profiles` | `tasks/apparmor.py` |
| `host.data.cosmic` | `tasks/cosmic/deploy.py` |
| `host.data.mullvad_extensions` | `tasks/mullvad_extensions.py` |
| `host.data.vscodium` | `tasks/vscodium.py` |
| `host.data.proton` | `tasks/proton.py` |

Because missing secrets simply leave `secrets` empty, removing `secrets.json.gpg` cleanly disables secret-dependent features instead of failing the deployment.

## Recommended workflow

1. **Dry run**: Use `--dry` to review the intended changes.
2. **Apply**: Run without `--dry`.
3. **Inspect**: pyinfra reports per-host, per-operation changed/unchanged status.
4. **Iterate**: Adjust `group_data/` flags and re-run. Deployments are designed to be idempotent.
