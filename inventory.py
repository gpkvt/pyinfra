"""
Define host configurations and derive the production host list.

The `_all_hosts` dictionary contains SSH connection settings and privilege
escalation options for each configured host. The special `@local` entry
represents the local execution environment.

Hosts listed in `disabled_hosts` are excluded from the `production` list.
The resulting list contains `(hostname, options)` tuples for all enabled
hosts.

Attributes:
    disabled_hosts (set[str]): Hostnames excluded from production.
    _all_hosts (dict): Configuration options for all hosts, including SSH
        connection details and sudo settings.
    production (list[tuple[str, dict]]): Enabled production hosts and their
        corresponding configuration options.
"""

disabled_hosts = {
	"dns",
	"dmz"
}

_all_hosts = {
    "@local": {
        "_sudo": True,
    },
    "dns": {
        "ssh_port": 22,
        "ssh_hostname": "dns",
        "ssh_user": "root",
        "_sudo": True,
    },
    "dmz": {
        "ssh_port": 22,
        "ssh_hostname": "dmz",
        "ssh_user": "root",
        "_sudo": True,
    },
}

production = [
    (hostname, options)
    for hostname, options in _all_hosts.items()
    if hostname not in disabled_hosts
]
