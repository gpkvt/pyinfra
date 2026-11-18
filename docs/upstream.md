# Upstream pyinfra

## The engine behind this repository

[pyinfra](https://pyinfra.com/) is an open-source infrastructure automation tool. The upstream project is maintained separately at [pyinfra-dev/pyinfra on GitHub](https://github.com/pyinfra-dev/pyinfra), with its own releases, documentation and community.

**This repository, `gpkvt/pyinfra`, is a deployment configuration built on top of that engine.** It contains inventory, host data, reusable task modules, templates, scripts and application-specific integration. It is not the upstream engine source tree.

## What upstream pyinfra provides

- **Python deploys:** write automation as normal Python code.
- **Inventory and data:** select hosts and organize them into groups with shared or host-specific values.
- **Operations and facts:** describe desired state and inspect the current target state.
- **Connectors:** execute locally or connect to remote systems, including SSH and supported container targets.
- **Preview and execution:** inspect planned changes with `--dry`, then execute operations.
- **Extensibility:** use Python packages and custom operations for project-specific behavior.

Upstream declarative operations compare current and desired state and only emit commands when needed. Imperative commands are also available, but they run when explicitly requested.

## How this repository uses it

| Upstream concept | This repository |
| --- | --- |
| Inventory | `inventory.py` selects local and remote targets |
| Host/group data | `group_data/` holds machine and role configuration |
| Deploy code | `deploy.py` selects baseline and optional task modules |
| Operations | `tasks/` manages packages, files, services and applications |
| Templates and assets | `templates/` and `files/` provide deployed content |
| Secrets | GPG-encrypted JSON supplies credentials to selected tasks |

## Learn from upstream

- [Official website](https://pyinfra.com/)
- [Documentation](https://docs.pyinfra.com/)
- [Getting started](https://docs.pyinfra.com/en/3.x/getting-started.html)
- [Operations](https://docs.pyinfra.com/en/3.x/using-operations.html)
- [Connectors](https://docs.pyinfra.com/en/3.x/connectors.html)
- [Upstream source code](https://github.com/pyinfra-dev/pyinfra)

The project targets Python 3.12+ and Debian/Ubuntu hosts; those are choices made by this repository, not a statement of upstream pyinfra's full platform support.
