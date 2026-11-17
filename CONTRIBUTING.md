# Contributing

Thank you for considering contributing to pyinfra. Contributions are welcome,
including task improvements, configuration changes, documentation, tests and
bug reports.

## Development environment

The project requires Python 3.12 or newer. Runtime dependencies are declared
in `pyproject.toml`; development tools are in its `dev` dependency group.
Use [uv](https://docs.astral.sh/uv/) to create the reproducible local
environment:

```bash
uv sync --dev
pre-commit install
```

Activate the environment when running tools interactively:

```bash
source .venv/bin/activate
```

After changing dependencies, update the local environment with `uv lock`
and `uv sync --dev`. When adding or changing a runtime dependency, also
update `requirements.txt`, which is used by the deployment CI job.

## Repository structure

| Path | Purpose |
| --- | --- |
| `deploy.py` | Main deployment entry point and feature gates |
| `inventory.py` | Deployment targets and connection settings |
| `common.py` | Shared initialization and secrets loading |
| `group_data/` | Host-specific and inventory-group configuration |
| `tasks/` | Modular pyinfra task modules |
| `files/` | Scripts, dotfiles and static assets |
| `templates/` | Jinja2 configuration templates |
| `apps/pyinfra-manager/` | Native COSMIC desktop deployment manager |
| `vscode/gpg-vault/` | VS Code extension for GPG-based vault workflows |
| `.github/` | CI workflows and coverage inventories |
| `tests/` | Mocked task and helper regression tests |

## Contribution principles

- **Configuration-driven:** prefer explicit configuration over hard-coded
  host-specific behavior.
- **Modular:** keep tasks focused on one system concern or service.
- **Conditional:** include optional functionality only when its feature gate
  and prerequisites are satisfied.
- **Idempotent:** a second run against an already-correct host must not report
  changes or repeat unnecessary work.
- **Secure:** keep credentials and private keys out of ordinary configuration,
  source code, logs and command-line arguments.
- **Minimal:** avoid unrelated changes and unnecessary dependencies.

For task changes, use pyinfra operations and facts where practical. Check
whether an operation is needed before scheduling it, use execution-time
callbacks or `_if=` conditions for dependent work, and avoid service
restarts unless relevant configuration changed. Consider privilege,
ownership, permissions, remote lockout and destructive effects.

## Configuration and secrets

- Put host-specific settings in `group_data/<host>.py` and shared role
  settings in the appropriate group-data file.
- Update the tracked `.example` file whenever the configuration schema
  changes. Add an inline comment explaining every example configuration
  option, including nested options.
- Keep credentials, private keys, tokens and other sensitive values in the
  encrypted secrets workflow. Do not commit `secrets.json`, decrypted
  secrets, real credentials or private host identifiers.
- Update `secrets.json.gpg.example` and [Secrets management](docs/secrets.md)
  when the encrypted schema or vault workflow changes.
- Document feature gates, defaults, prerequisites, side effects and recovery
  considerations.

If credentials are accidentally committed, report the exposure and rotate
them. Removing a value in a later commit does not remove it from Git history.

## Validation

Run the configured hooks and regression tests:

```bash
pre-commit run --all-files
uv run pytest tests/ -v
```

The test suite mocks pyinfra host, fact and operation APIs; it does not deploy
to a real host. The CI workflow also checks task-module coverage and performs
a two-pass idempotency deployment against an isolated GitHub Actions runner.
See [Development](docs/development.md) for the complete check inventory.

For deployment-related changes, review a dry run against a disposable or
otherwise recoverable target before applying anything:

```bash
pyinfra inventory.py deploy.py --limit @local --dry --diff
```

A dry run is a review aid, not a substitute for backups or testing. Never
assume that a successful run on one host proves compatibility with every
supported Debian or Ubuntu release.

## Pull requests

1. Keep the change focused and create a dedicated branch.
2. Include or update tests for changed behavior.
3. Update the README, relevant documentation and tracked configuration
   examples.
4. Review the complete diff for secrets, host-specific data and unintended
   formatting changes.
5. Report checks that could not be run and explain any remaining risks.

Use descriptive commit and pull request titles. For larger changes, open an
issue first to discuss the approach. See [Development](docs/development.md)
and the [task reference](docs/tasks.md) for project conventions.

## Reporting issues

Include the affected platform, relevant command output and a minimal
reproduction. Redact credentials, private keys, tokens, public IPs when
sensitive, and other identifying host details.

## License

By contributing, you agree that your contributions are provided under the
project's [MIT License](LICENSE).
