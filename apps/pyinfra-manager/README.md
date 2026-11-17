# Pyinfra Manager

See [the application guide](../../docs/pyinfra-manager.md) for setup, task
discovery, settings, deployment safety, and build instructions.

The COSMIC front end is in `src/`; its local Python backend is in
`backend/manager.py`. The backend can also be used directly from the
repository root:

```bash
uv run python apps/pyinfra-manager/backend/manager.py catalog
uv run python apps/pyinfra-manager/backend/manager.py hosts
uv run python apps/pyinfra-manager/backend/manager.py run @local
```

Deployments are dry-run by default. Pass `--apply` only after reviewing the
preview.

## Automated builds

GitHub Actions builds the Linux x86_64 release executable when application
files change and supports manual builds.

To create a build manually:

1. Open the repository's **Actions** tab.
2. Select **Build COSMIC Desktop App**.
3. Select **Run workflow**.
4. Download the `pyinfra-manager-linux-x86_64` artifact after completion.

Extract the archive and run `./pyinfra-manager`.

The artifact contains the executable, desktop entry, AppStream metadata, and
this README. It is a build artifact, not a self-contained installer; Rust and
COSMIC system dependencies are not bundled.
