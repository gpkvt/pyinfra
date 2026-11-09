# AI Usage Policy

This document describes the use of artificial intelligence (AI) tools in the development, maintenance, and documentation of this repository.

## Purpose

AI tools may be used to assist with development, improve productivity, explore implementation approaches, generate documentation, and support maintenance.

The use of AI is intended to complement human development and review, not replace them.

The repository maintainer remains responsible for the correctness, security, quality, and behavior of all committed changes, regardless of whether AI tools were involved.

## Areas of AI Usage

AI tools may be used for the following activities:

- **Code development:** Generating, improving, refactoring, and reviewing Python and Bash code.
- **Infrastructure automation:** Exploring pyinfra tasks, deployment strategies, and system configuration approaches.
- **Documentation:** Drafting and improving README files, technical documentation, contribution guidelines, and changelogs.
- **Troubleshooting:** Investigating errors, interpreting logs, and suggesting possible solutions.
- **Code quality:** Identifying potential bugs, improving readability, and assisting with linting and testing.
- **Security reviews:** Identifying potential security weaknesses and suggesting mitigations.
- **Configuration:** Assisting with APT repositories, SSH, system settings, firewall rules, udev, USBGuard, and other configuration files.

## Human Review and Responsibility

AI-generated content must not be considered correct or secure by default.

Before committing AI-assisted changes, the maintainer is responsible for:

- Reviewing the generated code and configuration.
- Verifying commands, parameters, APIs, and dependencies.
- Checking compatibility with supported operating systems and software versions.
- Testing changes where reasonably possible.
- Reviewing security implications and potential side effects.
- Ensuring that changes follow the project's conventions and intended behavior.

AI-generated changes must meet the same quality standards as manually written contributions.

## Security and Sensitive Information

Particular care must be taken when using AI tools for infrastructure-related development.

The following information must not be submitted to external AI services unless explicitly authorized and covered by appropriate data protection measures:

- Passwords and authentication credentials.
- SSH private keys.
- GPG private keys and passphrases.
- API tokens and access tokens.
- Production secrets and sensitive configuration values.
- Personal information and confidential infrastructure details.

AI-generated code involving security-sensitive functionality requires additional scrutiny.

This includes, but is not limited to:

- SSH authentication and key management.
- Privilege escalation and sudoers configuration.
- Firewall and network access rules.
- USBGuard and udev rules.
- AppArmor and other security policies.
- Shell command execution and privilege handling.
- Secret storage and encryption.

## Testing and Validation

AI-generated code and configuration must be validated before being used on production systems.

Depending on the nature of the change, validation may include:

- Python syntax and linting checks.
- pyinfra dry-run execution.
- Shell syntax checks.
- Reviewing generated commands and configuration files.
- Testing against disposable virtual machines or test environments.
- Verifying idempotency and repeatability.
- Checking for unintended system modifications.

A successful AI-generated response or code review does not constitute proof that a change works correctly.

## Transparency

AI assistance does not need to be attributed for every minor contribution, such as grammar corrections, formatting, or routine code suggestions.

For substantial AI-generated contributions, maintainers and contributors are encouraged to disclose the use of AI in the relevant commit, pull request, or contribution description.

AI tools must not be presented as human contributors or reviewers.

## Contributions

Contributors may use AI tools when submitting changes, provided that:

- They understand the submitted code and its behavior.
- They take responsibility for the correctness and security of their contributions.
- They verify that generated content does not introduce licensing or attribution problems.
- They do not submit confidential information or secrets to unauthorized AI services.
- They follow the project's contribution guidelines.

The project maintainers reserve the right to request clarification, modifications, or additional testing for AI-assisted contributions.

## Guiding Principle

AI is a development aid, not an authority.

All changes must be understandable, reviewable, testable, and appropriate for their intended use, regardless of how they were created.
