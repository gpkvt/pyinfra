#!/bin/sh
set -eu

DEHYDRATED_CONFIG=/etc/pyinfra-caddy/dehydrated.conf
CADDYFILE=/etc/pyinfra-caddy/Caddyfile

certificate_fingerprint() {
    find /var/lib/dehydrated/certs -type f -name fullchain.pem -print0 \
        | sort -z | xargs -0 -r sha256sum | sha256sum
}

before="$(certificate_fingerprint)"
if dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"; then
    after="$(certificate_fingerprint)"
    if [ "$before" != "$after" ]; then
        caddy reload --config "$CADDYFILE"
    fi
else
    echo "[caddy-renew] Dehydrated renewal failed" >&2
    exit 1
fi
