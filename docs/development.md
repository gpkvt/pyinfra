# Development

This guide covers local development, validation and the conventions used when extending the automation.

## Development environment

The project requires Python 3.12 or newer. Runtime dependencies are declared in `pyproject.toml`, development tools are in the `dev` dependency group, and `uv.lock` pins the resolved versions.

Install [uv](https://docs.astral.sh/uv/) if it is not already available, then synchronize the environment:

```bash
uv sync --dev
pre-commit install
```

Activate the created virtual environment when running commands interactively:

```bash
source .venv/bin/activate
```

After changing dependencies in `pyproject.toml`, update the lockfile with `uv lock` and run `uv sync --dev` again. Prefer `uv add PACKAGE` for runtime dependencies and `uv add --dev PACKAGE` for development dependencies so the project metadata and lockfile stay consistent.

## Run checks

Run all configured hooks:

```bash
pre-commit run --all-files
```

Run one hook:

```bash
pre-commit run pylint --all-files
pre-commit run check-yaml --all-files
pre-commit run check-json --all-files
```

The source of truth for hook versions and arguments is `.pre-commit-config.yaml`.

## Run the test suite

Run the mocked task regression tests in the synchronized development environment:

```bash
uv run pytest tests/ -v
```

The tests stub pyinfra host, fact and operation APIs. They check task-module evaluation and selected helper behavior without connecting to or changing a real host. The GitHub Actions workflow `.github/workflows/idempotency.yml` runs pytest and pre-commit as separate jobs for pushes and pull requests targeting `main`.

The CI coverage inventory in `.github/ci/task_coverage.json` enumerates every Python task module and every file under `files/scripts/`. The `tests/test_task_coverage.py` checks that the inventory cannot silently omit new or removed files, that every task module is explicitly classified, and that Python and shell utility sources pass syntax validation. It also evaluates every deployment module in a mocked pyinfra context with safe fixtures and requires each module to schedule at least one operation; dispatchers must include at least one child task. The `helper` classification is reserved for shared code that does not itself schedule pyinfra operations. These module smoke tests validate deployment preparation and operation scheduling, not changes on a live host. The real two-pass integration deployment remains the `deploy.py` check below. A separate behavioral coverage map in `tests/function_coverage.json` links every Python function in `tasks/` and `files/scripts/` to one or more pytest cases. `tests/test_function_coverage.py` compares that map against the AST-discovered function inventory and verifies that mapped tests exist and assert results or expected exceptions. Keep the map synchronized when adding, removing or renaming functions. The mapping is an inventory guard, not a substitute for reviewing whether each test asserts the function's expected outputs, side effects and no-op behavior.

## Deployment idempotency check

The same CI workflow performs two real deployments with pyinfra against the runner's local host (`--limit @local`). The deployment job waits until both pytest and pre-commit have completed, then runs even if either prerequisite failed. This preserves the deployment diagnostics instead of skipping them after an earlier failure; the overall workflow still reports the failed prerequisite.

Both pyinfra passes use `--diff` so file changes are included in the deployment output while `--json` preserves the machine-readable result used by the idempotency assertion. The deployment check uses the dedicated inventory `.github/ci/inventory.py` and isolated data directory `.github/ci/group_data/`, rather than the production `inventory.py` and personal workstation configuration. The CI inventory gives every optional configuration key an explicit, non-empty fixture. It enables tmux, a minimal Docker smoke service, cron, and the workstation hardware, storage, desktop-integration and maintenance package tasks. Those workstation tasks install inspection or integration utilities only; CI does not apply firmware updates, configure power management, alter peripheral services, or create backup jobs. Configurations for VPN, firewall, Caddy, AppArmor, Syncthing, Mullvad Browser, VSCodium, Proton and SSH authorized keys are present but explicitly gated off because they would alter runner networking, services, installed applications, or login access. Disabled APT repository fixtures are skipped before key downloads or repository changes. GitHub-hosted Ubuntu runners provide Docker Engine and Compose, so CI reuses those packages rather than installing Docker CE. The smoke service is an Alpine container with no persistent data or published ports. The workflow verifies that it is running after the first deployment. It still executes the normal `deploy.py` entry point and baseline tasks. The first run converges the disposable Ubuntu runner; the second run uses pyinfra's JSON results to verify that no operation changed anything. Any changed operation, failed operation, or missing result data fails the deployment check.

This is an integration check, not a dry run. It installs and configures software on the ephemeral GitHub Actions runner, which is discarded after the job. It does not target the production hosts in `inventory.py`.

## Configured checks

| Check | Purpose |
| --- | --- |
| `check-added-large-files` | Rejects newly added files over the configured size limit (2000 KB). |
| `check-yaml` | Validates YAML syntax. |
| `check-json` | Validates JSON syntax. |
| `pretty-format-json` / `jsonlint` | Formats JSON using the configured hook arguments. |
| `trailing-whitespace` | Removes trailing whitespace. |
| `end-of-file-fixer` | Ensures a final newline. |
| `check-merge-conflict` | Detects unresolved merge markers. |
| `pylint` | Lints Python files with the configured disabled-message list. |
| `yamllint` | Lints YAML in strict mode. |

Some hooks modify files automatically. Review the resulting diff after running them.

## Adding a feature

1. Identify whether the feature belongs to one host or a reusable inventory group/role. Put host-specific settings in `group_data/<host>.py`; put shared role settings in `group_data/<group>.py` and assign hosts to that group in `inventory.py`.
2. Add or update a focused task module under `tasks/` (use a subdirectory such as `tasks/workstation/` for a cohesive role).
3. Add static payloads to `files/` or parameterized Jinja2 templates to `templates/`.
4. Add the task inclusion condition to `deploy.py` if it is optional. For grouped roles, gate each task on a nested role feature setting (for example, `host.data.get("workstation", {}).get("backup", {}).get("enabled", False)`).
5. Keep credentials in the encrypted secrets document and update `secrets.json.gpg.example` with placeholders when the schema changes. `files/scripts/gpg-vault` is the interactive workflow for maintaining that encrypted file; keep its command help and [Secrets management](secrets.md) documentation in sync when changing it.
6. Document configuration keys, prerequisites, side effects and recovery considerations.
7. Run pre-commit and test a dry run against a disposable or non-production target.

## Task design conventions

- Keep each task focused on one system concern or service.
- Prefer `host.data.get("key", default)` for optional configuration.
- Validate externally supplied values before constructing operations.
- Use pyinfra facts and conditional operations to avoid unnecessary changes.
- Make ownership, group and permissions explicit for sensitive files.
- Avoid overwriting existing private keys or user data unless explicitly intended.
- Handle service reloads/restarts only when the relevant configuration changes.
- Never log private keys, passwords, tokens or full credential URLs.

## Documentation conventions

- Use relative links between documents in this repository.
- Include runnable examples, but use reserved/example values rather than real host details.
- Distinguish task inclusion conditions from settings consumed inside a task.
- Document whether a task installs software, writes configuration, starts services or changes firewall/network state.
- Update the README and the relevant `docs/` reference when behavior changes.

## Pull request checklist

- [ ] Configuration defaults and feature gates match the implementation.
- [ ] No real credentials, private keys, host-specific identifiers or personal data were added.
- [ ] Operations have been reviewed for privilege, destructive effects and remote lockout risk.
- [ ] Dry-run output has been reviewed on a suitable target.
- [ ] `pre-commit run --all-files` passes.
- [ ] `uv run pytest tests/ -v` passes.
- [ ] README and relevant documentation have been updated.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for repository contribution guidance.

The tmux task schedules plugin installation and updates as pyinfra operations after the `tmux-plugin-manager` package operation. It verifies both plugin-manager scripts at execution time and only runs plugin management when the package or tmux configuration changes. This avoids invoking commands during deployment preparation, before queued package installation has executed, and avoids reporting changes on an unchanged second deployment.
