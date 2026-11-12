#!/bin/sh
set -eu

DEHYDRATED_CONFIG=/etc/dehydrated/config
CADDYFILE=/etc/caddy/Caddyfile

mkdir -p /var/lib/dehydrated/certs /var/lib/dehydrated/accounts \
    /var/lib/dehydrated/chains /var/lib/dehydrated/private

# The first cron run also registers the ACME account and issues missing certs.
dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"

caddy run --config "$CADDYFILE" &
CADDY_PID=$!

shutdown() {
    kill "$CADDY_PID" 2>/dev/null || true
    wait "$CADDY_PID" 2>/dev/null || true
}
trap shutdown INT TERM

certificate_fingerprint() {
    find /var/lib/dehydrated/certs -type f -name fullchain.pem -print0 \
        | sort -z | xargs -0 -r sha256sum | sha256sum
}

while kill -0 "$CADDY_PID" 2>/dev/null; do
    sleep 43200 &
    SLEEP_PID=$!
    wait "$SLEEP_PID" || true
    if ! kill -0 "$CADDY_PID" 2>/dev/null; then
        break
    fi
    before="$(certificate_fingerprint)"
    dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"
    after="$(certificate_fingerprint)"
    if [ "$before" != "$after" ]; then
        caddy reload --config "$CADDYFILE"
    fi
done

wait "$CADDY_PID"
