#!/bin/sh
set -eu

DEHYDRATED_CONFIG=/etc/pyinfra-caddy/dehydrated.conf
CADDYFILE=/etc/pyinfra-caddy/Caddyfile

mkdir -p /var/lib/dehydrated/certs /var/lib/dehydrated/accounts \
    /var/lib/dehydrated/chains /var/lib/dehydrated/private

# The first cron run also registers the ACME account and issues missing certs.
dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"

certificate_fingerprint() {
    find /var/lib/dehydrated/certs -type f -name fullchain.pem -print0 \
        | sort -z | xargs -0 -r sha256sum | sha256sum
}

renew_loop() {
    while :; do
        sleep 43200
        before="$(certificate_fingerprint)"
        if dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"; then
            after="$(certificate_fingerprint)"
            if [ "$before" != "$after" ]; then
                caddy reload --config "$CADDYFILE"
            fi
        else
            echo "[caddy-entrypoint] Dehydrated renewal failed; will retry on the next cycle" >&2
        fi
    done
}

caddy run --config "$CADDYFILE" &
CADDY_PID=$!
renew_loop &
RENEW_PID=$!

cleanup() {
    trap - EXIT INT TERM
    kill "$RENEW_PID" "$CADDY_PID" 2>/dev/null || true
    wait "$RENEW_PID" 2>/dev/null || true
    wait "$CADDY_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' INT TERM

# Keep the container lifecycle tied to Caddy; if it exits, Docker restarts it.
wait "$CADDY_PID"
