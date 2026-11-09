# Development

This guide covers local development, validation and the conventions used when extending the automation.

## Development environment

Create and activate a virtual environment, then install the runtime and development tools:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyinfra pre-commit pylint
pre-commit install
```

The repository does not currently define a pinned Python dependency file, so install versions compatible with the pyinfra version used by your environment. Consider recording tested dependencies when reproducibility becomes a project requirement.

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

1. Identify the host configuration required by the feature.
2. Add or update a focused task module under `tasks/`.
3. Add static payloads to `files/` or parameterized Jinja2 templates to `templates/`.
4. Add the task's inclusion condition to `deploy.py` if it is optional.
5. Keep credentials in the encrypted secrets document and update `secrets.json.gpg.example` with placeholders when the schema changes.
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
- [ ] README and relevant documentation have been updated.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for repository contribution guidance.
