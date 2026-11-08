# Development

## Code quality tooling

The project uses **pre-commit** to validate Python code and configuration
files, and enforces **pylint** linting (a pylint check suite also runs in the
repository's GitHub CI, shown by the `linting: pylint` badge).

### Setup

```bash
# Inside the virtual environment:
pip install pre-commit
pre-commit install

# Run all checks
pre-commit run --all-files

# Run individual checks
pre-commit run <hook-id>
```

> The exact hook list in `.pre-commit-config.yaml` could not be extracted at
> documentation time. Read `.pre-commit-config.yaml` for the authoritative set
> of hooks (expected: pyinfra-aware Python checks, pylint, and general
> file/hygiene hooks).

## Working on the project

- **Add/change a feature**: edit the relevant module in `tasks/`, expose any
  needed switch in `group_data/`, and gate inclusion in `deploy.py` following
  the existing `host.data.get(...)` pattern.
- **Add a host**: extend `inventory.py` and create matching `group_data/`
  variables (see `docs/configuration.md`).
- **Handle secrets**: extend `secrets.json.gpg.example` (structure only!) and
  consume via `builtins.secrets` — never hardcode credentials in tasks or
  group data (explicitly called out in `group_data/@local.py`).
- **Defaults**: default values for optional settings are determined by the
  consuming deployment modules — keep `group_data/` lean.

## Contribution guidelines

- Run `pre-commit run --all-files` before committing; CI enforces the same
  checks (including pylint).
- Keep task modules self-contained and idempotent (standard pyinfra practice).
- Document new configuration variables in the corresponding section of
  `group_data/<host>.py` and, if user-facing, in this documentation.

## Repository conventions recap

- Branch: `main`
- License: see repository (license badge on GitHub)
- CI: GitHub check suites for branch protection, including pylint
