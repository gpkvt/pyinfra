#!/bin/sh
set -eu

DEHYDRATED_CONFIG=/etc/pyinfra-caddy/dehydrated.conf

mkdir -p /var/lib/dehydrated/certs /var/lib/dehydrated/accounts \
    /var/lib/dehydrated/chains /var/lib/dehydrated/private

# Register the ACME account and issue any missing certificates before Caddy starts.
dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"

exec caddy run --config /etc/pyinfra-caddy/Caddyfile
