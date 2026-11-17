# Pyinfra Manager (COSMIC desktop app)

Pyinfra Manager is a native COSMIC desktop front end for this repository. It
delegates deployment to the existing `deploy.py` entry point and does not
duplicate pyinfra task logic.

## Using the application

1. Start Pyinfra Manager. It first checks `PYINFRA_REPOSITORY`, the last
   valid checkout saved under `$XDG_CONFIG_HOME/pyinfra-manager/repository`
   (or `~/.config/pyinfra-manager/repository`), the launch directory, and
   the executable's parent directories. You can also enter a checkout path
   directly in the path field. A valid checkout must contain `deploy.py`,
   `inventory.py`, `pyproject.toml`, `group_data/`, `tasks/`, and the
   manager backend. Valid paths are remembered for the next launch.
2. Open **Tasks** and load the catalog. It includes literal includes from
   `deploy.py`, the workstation task loop parsed from that file, and Python
   modules found below `tasks/`. The `entrypoint` field distinguishes modules
   included by the deployment from implementation/helper modules.
3. Open **Settings** to initialize and edit `group_data/@local.py` and
   `group_data/workstation.py`. The app opens the selected file with the
   desktop's configured editor.
4. Use **Validate both settings files** after editing. Validation parses Python
   syntax only; it never imports or executes configuration.
5. Select a host under **Deploy** and review **Preview (dry-run)** output.
   Applying changes is a separate two-step action.

The application currently runs the full `deploy.py` orchestration for the
selected host. Feature inclusion remains controlled by the configuration
gates in `deploy.py`; the task catalog is an inventory, not a second feature
switchboard.

## Local backend

The Python backend is also usable independently:

```bash
uv run python apps/pyinfra-manager/backend/manager.py catalog
uv run python apps/pyinfra-manager/backend/manager.py hosts
uv run python apps/pyinfra-manager/backend/manager.py init-config
uv run python apps/pyinfra-manager/backend/manager.py read-config local
uv run python apps/pyinfra-manager/backend/manager.py validate-config local group_data/@local.py
uv run python apps/pyinfra-manager/backend/manager.py run @local
uv run python apps/pyinfra-manager/backend/manager.py run @local --apply
```

The deployment command is a dry-run by default. The `--apply` flag is required
to make changes.

## Settings and backups

The settings menu manages only these ignored local files:

- `group_data/@local.py` — host-specific configuration.
- `group_data/workstation.py` — shared workstation-role configuration.

Missing files are initialized from tracked `.example` templates without
overwriting existing files. Before opening a file in an external editor, the
backend creates a timestamped mode-`0600` backup under
`$XDG_STATE_HOME/pyinfra-manager/backups` (or
`~/.local/state/pyinfra-manager/backups`). Python syntax validation is
available from the settings page. Configuration is never evaluated by the
editor backend.

Credentials and private keys belong in the encrypted secrets workflow, not
these settings files. The app does not add local configuration or backups to
Git. Deployment output may contain sensitive host details and is kept local.

## Safety model

- Dry-run is the default; applying changes requires an explicit second action.
- Only hosts declared in the literal `_all_hosts` inventory mapping are
  accepted by the backend.
- Configuration file paths are allowlisted; symlinked config files and a
  symlinked `group_data` directory are rejected.
- Settings syntax is parsed without evaluating arbitrary Python.
- Backups are private and stored outside the repository.
- Deployment output is not sent to telemetry or an external service.

## Building locally

Install Rust/Cargo and the native libraries listed by the
[libcosmic project](https://github.com/pop-os/libcosmic), then build:

```bash
cd apps/pyinfra-manager
cargo build --release
```

The resulting executable is `target/release/pyinfra-manager`. Install
`resources/org.pyinfra.Manager.desktop` into
`~/.local/share/applications/` to add it to the desktop launcher. The app
expects `uv` and the Python project dependencies to be available on the
system, and it must be pointed at a pyinfra repository checkout.

## Manual Linux builds

The **Build COSMIC Desktop App** workflow is available from the repository's
Actions tab and runs only when manually dispatched. It checks Rust formatting,
runs Clippy with warnings denied, and builds the release executable on Ubuntu
24.04 for x86_64.

The workflow uploads a `pyinfra-manager-linux-x86_64` archive containing the
executable, desktop entry, AppStream metadata, and application README. Download
it from the workflow run's **Artifacts** section. This archive is not a
self-contained installer: COSMIC system libraries and the Python runtime and
project dependencies must be installed separately.
