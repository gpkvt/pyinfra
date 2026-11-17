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
