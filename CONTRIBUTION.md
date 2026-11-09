# Contributing

Thank you for considering contributing to this repo\!

Contributions of all kinds are welcome, including bug fixes, infrastructure improvements, new deployment tasks, configuration enhancements, documentation updates, and suggestions.

This document describes the development workflow and guidelines for contributing to this repository.

## Table of Contents

- Getting Started
- Development Environment
- Repository Structure
- Contribution Guidelines
- Coding Guidelines
- Infrastructure and Deployment Tasks
- Configuration and Secrets
- Testing and Validation
- Submitting Changes
- Reporting Issues
- License

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork:bash

   ```bash
   git clone https://github.com/<your-username>/pyinfra.git
   cd pyinfra
   ```

3. Add the original repository as an upstream remote:bash

   ```bash
   git remote add upstream https://github.com/gpkvt/pyinfra.git
   ```

4. Create a dedicated branch for your changes:bash

   ```bash
   git checkout -b feature/your-feature
   ```

Keep your changes focused and avoid combining unrelated modifications in a single contribution.

## Development Environment

The project is primarily intended for Debian-based Linux systems and uses Python 3 and pyinfra for infrastructure automation.

### Prerequisites

- Python 3
- Git
- OpenSSH
- pyinfra
- sudo privileges where required

### Set up a virtual environment

bash

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

bash

```bash
pip install pyinfra
```

Install the development tools:

bash

```bash
pip install pre-commit pylint
```

Enable the repository's pre-commit hooks:

bash

```bash
pre-commit install
```

You are now ready to work on the project.

## Repository Structure

Understanding the repository structure helps keep contributions consistent with the existing architecture.

| Directory / File | Purpose |
| --- | --- |
| `deploy.py` | Main deployment entry point |
| `inventory.py` | Defines deployment targets and SSH settings |
| `common.py` | Shared configuration and initialization |
| `group_data/` | Host-specific configuration |
| `tasks/` | Modular pyinfra deployment tasks |
| `files/` | Scripts, dotfiles, and configuration files |
| `templates/` | Jinja2 templates |
| `.github/` | GitHub-related configuration |
| `.pre-commit-config.yaml` | Development checks |

When adding functionality, use the existing directory structure and conventions wherever possible.

## Contribution Guidelines

### General principles

Contributions should follow these principles:

- **Configuration-driven:** Prefer configuration options over hardcoded host-specific behavior.
- **Modular:** Keep individual services and system components in separate deployment modules.
- **Conditional:** Optional functionality should only be deployed when enabled and its prerequisites are available.
- **Idempotent:** Operations should converge towards the desired state without unnecessary changes.
- **Secure:** Handle credentials, private keys, and sensitive configuration carefully.
- **Reusable:** Prefer shared templates, helper functions, and configuration structures over duplicated logic.
- **Minimal:** Avoid introducing unnecessary dependencies or unrelated changes.

### What to contribute

Examples of useful contributions include:

- Bug fixes and reliability improvements.
- New system configuration tasks.
- Additional Docker or Docker Compose services.
- Improvements to networking, firewall, and VPN configuration.
- SSH and user environment enhancements.
- COSMIC desktop configuration.
- AppArmor profiles and security improvements.
- Better error handling and deployment diagnostics.
- Documentation and configuration examples.

Before implementing a larger feature, consider opening an issue to discuss the proposed approach.

## Coding Guidelines

### Python

- Follow the existing coding style.
- Use meaningful variable, function, and module names.
- Keep functions and deployment tasks focused.
- Avoid unnecessary complexity and duplicated code.
- Use existing shared functionality where appropriate.
- Handle missing or optional configuration values gracefully.
- Avoid hardcoding hostnames, usernames, paths, or credentials when these belong in configuration.
- Ensure new code passes Pylint checks.

### pyinfra tasks

Deployment operations should follow pyinfra's declarative approach.

When creating or modifying tasks:

- Use appropriate pyinfra operations rather than unnecessary shell commands.
- Prefer idempotent operations.
- Avoid making assumptions about the target system.
- Account for optional configuration and missing prerequisites.
- Keep task dependencies and execution order clear.
- Avoid unnecessary changes to systems when the desired state is already satisfied.
- Consider the impact of operations on existing installations.

### Templates and configuration files

- Keep templates reusable and readable.
- Use configuration variables instead of embedding host-specific values.
- Follow the existing Jinja2 template conventions.
- Validate YAML and JSON files.
- Avoid unnecessary formatting changes to unrelated files.

### Shell scripts

- Make scripts safe to execute repeatedly where possible.
- Use clear error handling.
- Avoid exposing secrets through command-line arguments or log output.
- Quote variables appropriately.
- Document non-obvious behavior.

## Infrastructure and Deployment Tasks

Changes to deployment tasks can affect real systems.

Before submitting infrastructure-related changes:

1. Review the operations being executed.
2. Consider whether the operations are idempotent.
3. Check how the task behaves when optional configuration is missing.
4. Consider permissions and privilege escalation requirements.
5. Verify that existing functionality is not unintentionally affected.
6. Document new configuration options and prerequisites.

Whenever possible, validate changes against a disposable test machine or a non-production environment.

Do not assume that a successful deployment on one host guarantees compatibility with every supported Debian-based system.

## Configuration and Secrets

This repository separates ordinary configuration from sensitive information.

When contributing configuration changes:

- Put host-specific settings in the appropriate `group_data/` file.
- Follow existing configuration naming and organization.
- Provide sensible defaults where appropriate.
- Make optional features configurable.
- Update example configuration files when introducing new settings.
- Document new dependencies and required configuration values.

### Security requirements

**Never commit real credentials or private keys.**

In particular:

- Do not commit `secrets.json`.
- Do not commit `secrets.json.gpg`.
- Do not include API tokens, passwords, private keys, or authenticated repository URLs in examples.
- Use placeholder values in documentation and example files.
- Keep the secrets structure documented in `secrets.json.gpg.example` up to date when necessary.
- Ensure sensitive files retain restrictive permissions.

If you discover accidentally committed credentials, report the exposure and rotate the affected credentials. Removing a secret from a subsequent commit does not remove it from Git history.

## Testing and Validation

The project uses pre-commit to validate Python code and configuration files.

Before submitting a pull request, run the available checks.

### Run all checks

bash

```bash
pre-commit run --all-files
```

### Run individual checks

Python linting:

bash

```bash
pre-commit run pylint --all-files
```

YAML validation:

bash

```bash
pre-commit run check-yaml --all-files
```

JSON formatting:

bash

```bash
pre-commit run pretty-format-json --all-files
```

### Deployment validation

For changes affecting deployment behavior, review the proposed changes using:

bash

```bash
pyinfra inventory.py deploy.py --sudo --diff
```

The `--diff` option helps inspect intended changes before applying them.

Where practical, test deployment behavior on an isolated or disposable system before applying changes to production infrastructure.

If a particular change cannot be tested safely or locally, explain the limitation in the pull request.

## Submitting Changes

### Commit changes

Keep commits focused and write descriptive commit messages.

Examples:

text

```text
Add Docker service configuration
Fix WireGuard configuration handling
Improve SSH client template
Update contribution documentation
```

### Keep your branch up to date

Before submitting your pull request:

bash

```bash
git fetch upstream
git rebase upstream/main
```

Resolve any conflicts and rerun the relevant checks.

### Push your branch

bash

```bash
git push origin feature/your-feature
```

### Open a pull request

Create a pull request against the `main` branch of the original repository:

<https://github.com/gpkvt/pyinfra/pulls>

A good pull request should include:

- **Description:** Explain what the change does and why it is needed.
- **Motivation:** Reference the related issue or describe the problem being addressed.
- **Implementation:** Summarize the important technical changes.
- **Testing:** Describe the checks and deployment validation performed.
- **Configuration:** Document any new or modified configuration options.
- **Compatibility:** Mention relevant platform requirements or potential breaking changes.

Keep pull requests focused and reasonably small to make reviewing easier.

## Reporting Issues

Bug reports and feature requests are welcome.

Please use the GitHub issue tracker:

<https://github.com/gpkvt/pyinfra/issues>

When reporting a bug, include as much relevant information as possible:

- A clear description of the problem.
- Steps to reproduce it.
- Expected and actual behavior.
- Relevant error messages or logs, with sensitive information removed.
- Relevant configuration details, with credentials and private data redacted.
- Python and pyinfra versions.
- Operating system and distribution information.

For feature requests, describe the intended use case and explain how the proposed functionality would fit into the existing configuration-driven architecture.

Do not publish exploitable security vulnerabilities or sensitive infrastructure details in public issues. Contact the repository maintainer privately instead.

## License

By contributing to this repository, you agree that your contributions are made available under the project's existing license.

This project is licensed under the **MIT License**. See LICENSE for details.

---

Thank you for helping\!
