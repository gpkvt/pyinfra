# Security Policy

## Supported Versions

pyinfra currently maintains the `main` branch as its primary development branch.

Security fixes are applied to `main`. Since there are currently no formal releases, no guarantees are made regarding security support for older commits or unofficial builds.

Users are encouraged to use the latest commit from `main`.

## Reporting a Vulnerability

If you discover a security vulnerability in pyinfra, please report it responsibly.

**Please do not report security issues through public GitHub issues or discussions.**

Instead, use [GitHub's private vulnerability](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately) reporting feature:

1. Visit the pyinfra Security page.
2. Select **Report a vulnerability**.
3. Provide a detailed description of the vulnerability and steps to reproduce it.

If private vulnerability reporting is unavailable, contact the project maintainers privately through GitHub before disclosing the issue publicly.

## What to Include

When reporting a vulnerability, please include as much of the following information as possible:

- A description of the vulnerability and its potential impact.
- The affected commit or branch.
- Steps to reproduce the issue.
- A proof of concept, if available.
- Relevant logs, error messages, or stack traces.
- Any suggested mitigations or fixes.

Please avoid including actual credentials, private keys, access tokens, or other sensitive production data in your report.

## Scope

Security reports concerning the following areas are particularly relevant:

- **Arbitrary ommand execution:** Unsafe command construction, shell injection, or arbitrary command execution.
- **SSH and authentication:** Authentication bypasses, credential exposure, or insecure handling of SSH connections.
- **Privilege escalation:** Unexpected privilege escalation or unintended execution with elevated permissions.
- **Secret handling:** Exposure of passwords, tokens, private keys, or other sensitive information.
- **File operations:** Path traversal, unintended file access, or unsafe file manipulation.
- **Connectors:** Security vulnerabilities in SSH, Docker, local execution, and other supported connectors.
- **Inventory and configuration:** Unsafe handling of untrusted inventory data, configuration, or user-supplied input.
- **Dependency vulnerabilities:** Vulnerabilities in dependencies that meaningfully affect pyinfra.

## Disclosure Process

The pyinfra maintainers aim to follow a coordinated vulnerability disclosure process:

1. Acknowledge receipt of the report.
2. Investigate and assess the reported vulnerability.
3. Work with the reporter to understand and address the issue.
4. Prepare and apply a security fix where appropriate.
5. Publish a security advisory when appropriate.

Please allow the maintainers reasonable time to investigate and address reported vulnerabilities before making them public.

## Disclosure Expectations

We ask security researchers to:

- Avoid exploiting vulnerabilities beyond what is necessary to demonstrate their impact.
- Avoid accessing, modifying, or deleting data belonging to others.
- Avoid disrupting production systems or services.
- Keep vulnerability details confidential until a coordinated disclosure is agreed upon.

We appreciate responsible security research and contributions that help make pyinfra safer for everyone.
