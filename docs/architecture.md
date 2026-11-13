# Architecture

This project uses [pyinfra](https://pyinfra.com/) to turn Python host data into repeatable infrastructure operations. Its main separation is between **where to connect**, **what a host should look like**, and **how to implement each change**.

## Repository layers

```text
inventory.py ─────── target names, SSH options and privilege escalation
       │
       ▼
group_data/ ──────── per-host desired configuration (host.data)
       │
       ▼
deploy.py ────────── initialization and conditional task selection
       │
       ▼
tasks/*.py ───────── pyinfra operations and task-specific validation
       │             ├── templates/  rendered, parameterized files
       │             └── files/      static payloads
       ▲
common.py ────────── shared runtime values and decrypted secrets
```

| Component | Responsibility |
| --- | --- |
| `inventory.py` | Declares target hosts, SSH connection settings and `_sudo` behavior. |
| `group_data/` | Supplies target-specific and group/role settings, exposed together through `host.data`. |
| `deploy.py` | Calls initialization, includes core tasks and gates optional tasks. |
| `common.py` | Loads the encrypted secrets file and publishes shared runtime values. |
| `tasks/` | Declares operations for system, network, service and user configuration. |
| `templates/` | Holds Jinja2 templates rendered by task modules. |
| `files/` | Holds static files copied or synchronized by task modules, including the `gpg-vault` secret-management utility. |

## Execution lifecycle

1. **Inventory loading.** pyinfra loads `inventory.py`. `production` is built from `_all_hosts` after removing names in `disabled_hosts`. The special `@local` host represents the machine running pyinfra.
2. **Initialization.** `deploy.py` calls `common.initialize(host, check_flatpak=True)`. The function checks for `secrets.json.gpg`; when present, it runs `gpg --decrypt`, parses JSON, and assigns the result to `builtins.secrets`. If absent, it assigns an empty dictionary. It also sets `builtins.homedir` and, when requested, `builtins.flatpak` from the `Which` fact.
3. **Task selection.** Core task modules are included unconditionally. Optional modules are included when the relevant `host.data` value, secret entry, or detected executable is truthy. The workstation role is an inventory group: `workstation = ["@local"]` assigns the local target to that group, and pyinfra loads `group_data/workstation.py` alongside the host's own data. `deploy.py` then includes each `tasks/workstation/*.py` module only when its matching `workstation.<feature>.enabled` setting is true. The exact gates are listed in [Deployment workflow](deployment.md).
4. **Local secret maintenance.** `files/scripts/gpg-vault` is synchronized to the configured user's scripts directory by `tasks/scripts.py` and linked into `/usr/local/bin/`. It is an operator-facing tool; `common.initialize()` continues to decrypt `secrets.json.gpg` itself during deployment.
5. **Operation execution.** pyinfra prepares operations by reading facts and determining the required changes, then executes them in order. Facts read directly in deploy code describe the pre-deployment state; use operation callbacks such as `did_change` and `any_changed` through `_if` when a later operation depends on an earlier operation's result. Never branch on an operation's change result with an ordinary Python `if` during preparation.

## Configuration namespaces

### Host and group data

Values in `group_data/<host>.py` and matching group-data files are exposed through `host.data`. A target can therefore receive both its host-specific settings and shared role settings. For example, `workstation = ["@local"]` in `inventory.py` assigns `@local` to the `workstation` group, whose settings are defined in `group_data/workstation.py`. Tasks access these values with `host.data.<name>` or `host.data.get(<name>, default)`. Existing host settings include `apt_packages`, `wireguard_config`, `docker`, `ufw`, and `zsh`; workstation role settings are nested under `host.data.workstation`.

### Shared builtins

`common.initialize()` currently publishes:

| Name | Meaning |
| --- | --- |
| `secrets` | Parsed decrypted JSON dictionary, or `{}` if no encrypted file is found. |
| `homedir` | `host.data.homedir`, defaulting to `/root/`. |
| `flatpak` | Result of the Flatpak `Which` fact when `check_flatpak=True`. |

Some task modules initialize `common` themselves when `homedir` has not yet been set. Avoid adding new implicit globals; prefer explicit task inputs where practical.

## Task organization

Tasks are grouped by responsibility rather than by host. General tasks live directly under `tasks/`; optional workstation-role tasks are grouped under `tasks/workstation/`. `deploy.py` owns orchestration and should remain the authoritative place for full-deployment feature gates. A task module should:

- Read only the host data and secrets it needs.
- Validate user-controlled configuration before creating operations where appropriate.
- Keep file ownership and permissions explicit.
- Avoid overwriting user-generated material unless that behavior is intentional and documented.
- Be safe to run repeatedly and use pyinfra facts/conditions to minimize unnecessary changes.

## Docker lifecycle

Docker Compose projects, generated environment files and persistent host data live below
\`~/.docker/<service>/\`. Each project is managed by a user-level systemd unit whose
working directory is that service directory. Persistent data uses explicit host bind
mounts; Docker-managed named volumes are not used.

Keep Compose lifecycle commands behind the shared systemd helper. Replacing this flow
with pyinfra's stateless \`docker.compose\` operation would bypass the user-level unit
and Sablier preparation/restart rules. The helper instead gates image pulls,
container reconciliation and systemd restarts on actual configuration changes.

## Templates and static assets

Use `templates/` when a file needs host-specific values or secrets at render time. Use `files/` for static content. A task is responsible for choosing the destination, owner, group, mode and reload/restart behavior. See [Templates and static files](templates.md).

## Important boundaries

- A task being present in the repository does not mean it is automatically deployed; `deploy.py` controls inclusion.
- Secret availability and host configuration are separate conditions. WireGuard, for example, needs both a host-side interface definition and matching secret data.
- The WireGuard task writes configuration but does not start the tunnel. The VPN task manages the `wg-quick@...` service based on IPv4 network detection.
- The local target can change the machine executing pyinfra. Treat `@local` with the same care as a production host.
