# Upstream pyinfra

## Project relationship

[pyinfra](https://pyinfra.com/) is an open-source infrastructure automation tool maintained separately in the [pyinfra-dev/pyinfra repository](https://github.com/pyinfra-dev/pyinfra).

This repository, `gpkvt/pyinfra`, contains deployment configuration built on that tool. It is not the upstream engine source tree and does not define upstream pyinfra behavior.

## Upstream concepts used here

- **Inventory** selects target hosts and organizes them into groups.
- **Host and group data** supplies configuration values to deploy code.
- **Deploys** compose Python code into a deployment.
- **Facts** inspect the current state of target systems.
- **Operations** describe changes to files, packages, services and other resources.
- **Connectors** provide local and remote execution mechanisms.
- **Dry runs** display the planned operations before execution.

The upstream documentation describes the supported interfaces and behavior in detail.

## Mapping to this repository

| Upstream concept | Location in this repository |
| --- | --- |
| Inventory | `inventory.py` |
| Host and group data | `group_data/` |
| Deploy code | `deploy.py` |
| Operations and custom task logic | `tasks/` |
| Templates and deployed assets | `templates/` and `files/` |
| Encrypted credentials | GPG-encrypted secrets data |

## Upstream documentation

- [Project website](https://pyinfra.com/)
- [Documentation](https://docs.pyinfra.com/)
- [Getting started](https://docs.pyinfra.com/en/3.x/getting-started.html)
- [Operations](https://docs.pyinfra.com/en/3.x/using-operations.html)
- [Connectors](https://docs.pyinfra.com/en/3.x/connectors.html)
- [Source code](https://github.com/pyinfra-dev/pyinfra)

The Python version and target operating systems listed in this repository's requirements describe this deployment configuration. They should not be interpreted as a complete statement of upstream pyinfra's platform support.
