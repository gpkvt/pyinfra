# pylint: disable=C0301, E0401, C0115, E0602

"""
Configure dehydrated and manage Let's Encrypt certificate renewal using pyinfra.

This module deploys the dehydrated configuration and hook script, then checks whether any existing certificates are approaching expiration. Certificate renewal is triggered only when at least one certificate expires within the next 30 days.

Configuration: secrets (dict): Decrypted secrets containing dehydrated configuration. Expected structure: dehydrated: hetzner_api_token: Hetzner DNS API token.

Facts: CertNeedsRenewal: Custom pyinfra fact that checks certificates under /var/lib/dehydrated/certs/ using OpenSSL.

    Returns:
        bool: True if at least one certificate expires within
        30 days, otherwise False.

Operations:

1. Deploy the dehydrated configuration to `/etc/dehydrated/config`,
   provided a Hetzner API token is available.
2. Deploy the dehydrated hook script to `/etc/dehydrated/hook.sh`.
3. Check whether any existing certificates need renewal.
4. Run dehydrated in cron mode to renew certificates when necessary.

File permissions:

- Configuration: root:root, mode 0600.
- Hook script: root:root, mode 0750.

Notes:

- Configuration deployment is skipped when the Hetzner API token
  is unavailable.
- Certificate expiration is checked using OpenSSL's `-checkend`
  option with a 2,592,000-second (30-day) threshold.
- Renewal runs with sudo and a timeout of 600 seconds.
- The renewal operation is skipped when all existing certificates
  are valid for more than 30 days.

"""

from pyinfra import host
from pyinfra.operations import server, files
from pyinfra.api import FactBase

if not hasattr(__import__('builtins'), 'homedir'):
    from common import initialize
    initialize(host)

class CertNeedsRenewal(FactBase):
    command = """
        for cert in "/var/lib/dehydrated/certs/*/fullchain.pem"; do
            [ -f "$cert" ] || continue

            if ! openssl x509 -checkend 2592000 -noout -in "$cert" >/dev/null 2>&1; then
                echo true
                exit 0
            fi
        done

        echo false
    """

    def process(self, output):
        return output[-1].strip() == "true"

files.template(
    name="Configure dehydrated",
    src="templates/dehydrated_config.j2",
    dest="/etc/dehydrated/config",
    user="root",
    group="root",
    mode="600",
    hetzner_api_token=secrets.get("dehydrated", {}).get("hetzner_api_token"),
    _sudo=True,
    _if=lambda: bool(secrets.get("dehydrated", {}).get("hetzner_api_token"))
)

files.put(
    name="Deploy dehydrated hook",
    src="files/dehydrated_hook.sh",
    dest="/etc/dehydrated/hook.sh",
    user="root",
    group="root",
    mode="750",
    _sudo=True,
)

server.shell(
    name="Renew Let's Encrypt certificates",
    commands=[
        "/usr/bin/dehydrated --cron --config /etc/dehydrated/config"
    ],
    _sudo=True,
    _timeout=600,
    _if=lambda: host.get_fact(CertNeedsRenewal),
)
