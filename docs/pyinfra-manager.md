# Pyinfra Manager (COSMIC desktop app)

Pyinfra Manager is a native COSMIC desktop front end for this repository. It is
designed to operate on the local checkout and delegates deployments to the
existing `deploy.py` entry point; it does not duplicate pyinfra task logic.

## Local backend

The Python backend is the local control plane used by the desktop application:

```bash
uv run python apps/pyinfra-manager/backend/manager.py catalog
uv run python apps/pyinfra-manager/backend/manager.py hosts
uv run python apps/pyinfra-manager/backend/manager.py init-config
uv run python apps/pyinfra-manager/backend/manager.py read-config local
uv run python apps/pyinfra-manager/backend/manager.py run @local
```

The deployment command is a dry-run by default. Add `--apply` only after
reviewing the preview and explicitly confirming the changes in the UI.

## Task discovery

The catalog reads literal `local.include("tasks/...")` declarations from
`deploy.py` and adds the workstation feature modules from the same feature
mapping used by the deployment loop. The UI distinguishes core, optional and
workstation tasks. Conditional gates still belong to `deploy.py`; a catalog
entry does not imply that its feature is enabled on a target. The full
repository task reference remains the source for task behavior and options.

## Settings

The settings editor manages only these ignored local files:

- `group_data/@local.py` — host-specific configuration.
- `group_data/workstation.py` — shared workstation-role configuration.

The backend can initialize missing files from their tracked `.example`
templates, but never overwrites an existing file during initialization.
Python is parsed for syntax validation only; it is never imported or executed
by the settings editor. A changed file is backed up to `.bak` before an
atomic replacement. Saving identical content is a no-op. Existing backups
must be moved manually before another save, preventing silent backup loss.

Credentials and private keys belong in the encrypted secrets workflow, not
these settings files. The editor must never add the ignored files or backups
to Git.

## Safety model

- Dry-run is the default; applying changes requires an explicit UI action.
- Only hosts declared in the literal `_all_hosts` inventory mapping are
  accepted by the backend.
- Configuration file paths are allowlisted and symlinks are rejected.
- Configuration is syntax-checked without evaluating arbitrary Python.
- Writes are atomic, mode `0600`, and backed up before replacement.
- Deployment output is returned as text; it must be treated as potentially
  sensitive and should not be sent to telemetry.

## Building the COSMIC application

The Rust front end uses the official `libcosmic` toolkit. Install the Rust
toolchain and the native dependencies listed by the
[libcosmic project](https://github.com/pop-os/libcosmic), then build from
`apps/pyinfra-manager` with Cargo. The desktop shell should launch the local
backend with the repository root as its working directory.

The app is intentionally kept separate from the pyinfra runtime dependencies.
