#!/bin/sh
set -eu

: "${CADDY_UID:?CADDY_UID is required}"
: "${CADDY_GID:?CADDY_GID is required}"

DEHYDRATED_CONFIG=/etc/pyinfra-caddy/dehydrated.conf

# Prepare persistent state and issue certificates as the unprivileged service user.
setpriv --reuid="$CADDY_UID" --regid="$CADDY_GID" --clear-groups -- \
    mkdir -p /var/lib/dehydrated/certs /var/lib/dehydrated/accounts \
    /var/lib/dehydrated/chains /var/lib/dehydrated/private

setpriv --reuid="$CADDY_UID" --regid="$CADDY_GID" --clear-groups -- \
    dehydrated --cron --accept-terms --keep-going --config "$DEHYDRATED_CONFIG"

# Keep only NET_BIND_SERVICE in the non-root process capability sets.
exec setpriv \
    --reuid="$CADDY_UID" \
    --regid="$CADDY_GID" \
    --clear-groups \
    --inh-caps=+net_bind_service \
    --ambient-caps=+net_bind_service \
    -- caddy run --config /etc/pyinfra-caddy/Caddyfile
