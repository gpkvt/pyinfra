# Development

## Code quality tooling

The project uses **pre-commit** to validate Python code and configuration files, and enforces **pylint** linting (a pylint check suite also runs in the repository's GitHub CI, shown by the `linting: pylint` badge).

### Setup

Inside the virtual environment:

bash

```bash
pip install pre-commit
pre-commit install
```

Run all checks:

bash

```bash
pre-commit run --all-files
```

Run an individual hook:

bash

```bash
pre-commit run <hook-id> --all-files
```

### Configured hooks

The authoritative hook configuration is `.pre-commit-config.yaml`.

| Hook | Purpose |
| --- | --- |
| `check-added-large-files` | Rejects files larger than 2000 KB |
| `check-yaml` | Validates YAML files |
| `check-json` | Validates JSON files |
| `pretty-format-json` | Formats JSON with two-space indentation |
| `trailing-whitespace` | Removes trailing whitespace |
| `end-of-file-fixer` | Ensures files end with a newline |
| `check-merge-conflict` | Detects merge conflict markers |
| `pylint` | Lints Python files |
| `yamllint` | Lints YAML files |
| `jsonlint` | Applies JSON formatting checks |

Pylint uses the project's configured disabled-message list. YAML linting runs in strict mode.

## Working on the project

- **Add/change a feature**: edit the relevant module in `tasks/`, expose any needed switch in `group_data/`, and gate inclusion in `deploy.py` following the existing `host.data.get(...)` pattern.
- **Add a host**: extend `inventory.py` and create matching `group_data/` variables (see `docs/configuration.md`).
- **Handle secrets**: extend `secrets.json.gpg.example` (structure only\!) and consume via `builtins.secrets` — never hardcode credentials in tasks or group data.
- **Defaults**: default values for optional settings are determined by the consuming deployment modules — keep `group_data/` lean.

## Contribution guidelines

- Run `pre-commit run --all-files` before committing; CI enforces the same checks (including pylint).
- Keep task modules self-contained and idempotent (standard pyinfra practice).
- Document new configuration variables in the corresponding section of `group_data/<host>.py` and, if user-facing, in this documentation.
- Update the relevant documentation when adding, removing or changing deployment tasks.
- Keep secrets and personal credentials out of committed configuration files.

See CONTRIBUTING.md for details.

## Repository conventions recap

- Branch: `main`
- License: see repository (license badge on GitHub)
- CI: GitHub check suites for branch protection, including pylint
