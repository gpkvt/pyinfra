FROM caddy:2.11.2-builder AS builder
RUN xcaddy build v2.11.2 --with github.com/sablierapp/sablier-caddy-plugin@v1.0.2

FROM caddy:2.11.2
USER root
RUN apk add --no-cache bash curl jq bind-tools openssl coreutils ca-certificates \
    && curl -fsSL https://raw.githubusercontent.com/dehydrated-io/dehydrated/v0.7.2/dehydrated \
       -o /usr/local/bin/dehydrated \
    && chmod 0755 /usr/local/bin/dehydrated \
    && printf '0 3 * * * /usr/local/bin/renew.sh\n' > /etc/crontabs/caddy \
    && chown caddy:caddy /etc/crontabs/caddy \
    && chmod 0600 /etc/crontabs/caddy
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY hook.sh /etc/dehydrated/hook.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY renew.sh /usr/local/bin/renew.sh
RUN chmod 0755 /etc/dehydrated/hook.sh /usr/local/bin/entrypoint.sh /usr/local/bin/renew.sh
USER caddy
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
