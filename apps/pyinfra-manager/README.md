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

## Local application builds

There is no GitHub Actions build workflow or automatically published desktop
artifact. Install Rust/Cargo and the required COSMIC development libraries,
then run these commands from the repository root:

```bash
cargo fmt --manifest-path apps/pyinfra-manager/Cargo.toml --all -- --check
cargo clippy --manifest-path apps/pyinfra-manager/Cargo.toml --all-targets -- -D warnings
cargo build --manifest-path apps/pyinfra-manager/Cargo.toml --release
```

The executable is `apps/pyinfra-manager/target/release/pyinfra-manager`.
Desktop entry and AppStream metadata remain under `resources/`. The executable
is not a self-contained installer; COSMIC system libraries and the Python
project environment must be installed separately.
