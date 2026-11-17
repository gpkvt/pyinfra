# Development

<div class="page-intro" markdown>
  <div class="page-intro-copy">
    <span class="page-eyebrow">BUILD AND VALIDATE SAFELY</span>
    <p class="page-lead">Set up the development environment, run the project checks and follow the conventions used when extending pyinfra tasks.</p>
  </div>
  <div class="page-intro-grid">
  <div class="page-intro-item"><strong>uv</strong><span>Reproducible environment</span></div>
  <div class="page-intro-item"><strong>pytest</strong><span>Task regression coverage</span></div>
  <div class="page-intro-item"><strong>pre-commit</strong><span>Lint and quality checks</span></div>
  </div>
</div>


This guide covers local development, validation and the conventions used when extending the automation.

## Development environment

The project requires Python 3.12 or newer. Runtime dependencies are declared in `pyproject.toml` and mirrored in `requirements.txt`; development tools are in the `dev` dependency group. `uv.lock` is intentionally ignored by Git and is generated locally by uv, so it is not a repository-pinned lockfile.

Install [uv](https://docs.astral.sh/uv/) if it is not already available, then synchronize the environment:

```bash
uv sync --dev
pre-commit install
```

Activate the created virtual environment when running commands interactively:

```bash
source .venv/bin/activate
```

After changing dependencies in `pyproject.toml`, run `uv lock` and `uv sync --dev` to refresh the local environment. When adding or changing runtime dependencies, also update `requirements.txt`, because the deployment CI job installs from that file. Prefer `uv add PACKAGE` for runtime dependencies and `uv add --dev PACKAGE` for development dependencies.

## Makefile shortcuts

The repository root includes a `Makefile` for common development and deployment commands. Run `make help` to list the targets.

| Target | Purpose |
| --- | --- |
| `make sync` | Run `uv sync --dev`. |
| `make hooks` | Install the pre-commit Git hooks. |
| `make lint` | Run all pre-commit hooks against tracked files. |
| `make test` | Run the pytest suite. |
| `make compile` | Check Python and shell syntax, to check syntax. |
| `make check` | Run lint, tests and syntax checks. |
| `make dry-run` | Preview deployment with `--dry --diff`. |
| `make deploy` | Apply the deployment with `--diff`. |

Deployment targets are deliberately limited to `@local` by default. Select another target explicitly, for example:

```bash
make dry-run TARGET_ARGS="--limit hostname"
make deploy TARGET_ARGS="--limit hostname"
```

You can also override `INVENTORY`, `DEPLOY`, `UV`, `PYTHON`, `PYTEST`, `PRE_COMMIT` or `PYINFRA` when using a different executable or deployment entry point. Review the preview before running `make deploy`; the Makefile does not replace the deployment safety checks described below.

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

The tests stub pyinfra host, fact and operation APIs. They check task-module evaluation and selected helper behavior without connecting to or changing a real host. Run these checks locally before submitting a pull request. The repository no longer runs automated GitHub Actions checks.

The coverage inventory in `.github/ci/task_coverage.json` enumerates every Python task module and every file under `files/scripts/`. The `tests/test_task_coverage.py` checks that the inventory cannot silently omit new or removed files, that every task module is explicitly classified, and that Python and shell utility sources pass syntax validation. It also evaluates every deployment module in a mocked pyinfra context with safe fixtures and requires each module to schedule at least one operation; dispatchers must include at least one child task. The `helper` classification is reserved for shared code that does not itself schedule pyinfra operations. These module smoke tests validate deployment preparation and operation scheduling, not changes on a live host. Use a disposable target for any real deployment validation. A separate behavioral coverage map in `tests/function_coverage.json` links every Python function in `tasks/` and `files/scripts/` to one or more pytest cases. `tests/test_function_coverage.py` compares that map against the AST-discovered function inventory and verifies that mapped tests exist and assert results or expected exceptions. Keep the map synchronized when adding, removing or renaming functions. The mapping is an inventory guard, not a substitute for reviewing whether each test asserts the function's expected outputs, side effects and no-op behavior.

## Deployment validation

The project does not run automated deployment checks. For infrastructure changes, validate task behavior with the mocked pytest suite, then review a pyinfra dry run against a disposable or otherwise recoverable target before applying changes. A second deployment against an already-converged target should report no changes. Do not use production hosts as test targets.

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
- `host.get_fact(Command, ...)` returns a list of output lines, not a string. Use `common.command_output_text()` before applying string methods or comparing complete command output.
- Do not branch on an operation's `.changed` state during task preparation. Use `OperationMeta.did_change` callbacks or `any_changed()` in `_if` conditions so dependent operations are evaluated during execution.
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

See [CONTRIBUTING.md](https://github.com/gpkvt/pyinfra/blob/main/CONTRIBUTING.md) for repository contribution guidance.

The tmux task schedules plugin installation and updates as pyinfra operations after the `tmux-plugin-manager` package operation. It verifies both plugin-manager scripts at execution time and only runs plugin management when the package or tmux configuration changes. This avoids invoking commands during deployment preparation, before queued package installation has executed, and avoids reporting changes on an unchanged second deployment.


## Releases

This repository publishes GitHub Releases from semantic-version tags; it is
not packaged for PyPI. Follow the [release guide](releasing.md) to prepare the
changelog, tag a release commit and publish the generated release notes.
