# pylint: disable=C0301, E0401, C0116, E1101

"""Install and configure Caddy, optionally with the Sablier handler."""

from copy import deepcopy

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server, systemd

CADDY_VERSION = "v2.11.2"
PLUGIN_VERSION = "v1.0.2"
GO_VERSION = "1.25.4"
XCADDY_VERSION = "v0.4.5"

SERVICE_PORTS = {
    "miniflux": 8005, "timetagger": 8010, "grav": 8015,
    "forgejo": 3000, "portainer": 9000, "tasmoadmin": 8016,
    "vaultwarden": 8018, "homepage": 8020, "nocodb": 8019,
    "linkwarden": 8021, "paperless": 8022, "firefly-iii": 8023,
    "snipe-it": 8025,
}


def build_sablier_caddy_config(caddy_config, docker_config, options):
    """Wrap only configured Docker reverse proxies in Sablier routes."""
    result = deepcopy(caddy_config)
    if not options.get("enabled", False):
        return result

    duration = options.get("default_duration", "60m")
    timeout = options.get("blocking_timeout", "5m")

    def wrap_routes(service, port, service_options):
        sablier_options = service_options.get("sablier", {})
        if not sablier_options.get("enabled", True):
            return
        group = sablier_options.get("group", service)
        for directives in result.values():
            if directives.get("reverse_proxy") != f"127.0.0.1:{int(port)}":
                continue
            route = {
                "sablier http://127.0.0.1:10000": {
                    "group": group,
                    "session_duration": sablier_options.get("session_duration", duration),
                    "blocking": {
                        "timeout": sablier_options.get("blocking_timeout", timeout),
                    },
                },
                "reverse_proxy": directives.pop("reverse_proxy"),
            }
            if "header" in directives:
                route["header"] = directives.pop("header")
            directives["route"] = route

    for service, default_port in SERVICE_PORTS.items():
        if service in docker_config:
            service_options = docker_config[service]
            wrap_routes(
                service,
                service_options.get("port", default_port),
                service_options,
            )

    # Firefly's FinTS endpoint belongs to the same Compose/systemd unit.
    firefly = docker_config.get("firefly-iii", {})
    if firefly:
        wrap_routes(
            "firefly-iii",
            firefly.get("fints_port", 8024),
            firefly,
        )
    return result


if not hasattr(__import__("builtins"), "homedir"):
    from common import initialize
    initialize(host)


@deploy("Configure Caddy")
def configure_caddy():
    sablier_options = host.data.get("docker_sablier", {})
    sablier_enabled = bool(sablier_options.get("enabled", False))

    apt.packages(name="Install Caddy", packages=["caddy"], _sudo=True)

    custom_binary_changed = False
    if sablier_enabled:
        check = (
            "if [ -x /usr/local/bin/caddy-sablier ] && "
            "/usr/local/bin/caddy-sablier version 2>&1 | grep -q '2.11.2' && "
            "/usr/local/bin/caddy-sablier list-modules 2>/dev/null | "
            "grep -qx 'http.handlers.sablier'; then echo ready; else echo missing; fi"
        )
        custom_binary_changed = host.get_fact(Command, check).strip() != "ready"
        server.shell(
            name="Build Caddy with the Sablier handler",
            commands=[f"""set -euo pipefail
arch="$(dpkg --print-architecture)"
case "$arch" in
    amd64) goarch=amd64 ;;
    arm64) goarch=arm64 ;;
    *) echo "Unsupported architecture: $arch" >&2; exit 1 ;;
esac
if [ ! -x /opt/go{GO_VERSION}/bin/go ]; then
    tmp="$(mktemp -d)"
    curl -fsSL "https://go.dev/dl/go{GO_VERSION}.linux-$goarch.tar.gz" | tar -xz -C "$tmp"
    install -d /opt
    rm -rf "/opt/go{GO_VERSION}"
    mv "$tmp/go" "/opt/go{GO_VERSION}"
    rmdir "$tmp"
fi
export PATH="/opt/go{GO_VERSION}/bin:$PATH"
export GOBIN=/usr/local/bin
go install github.com/caddyserver/xcaddy/cmd/xcaddy@{XCADDY_VERSION}
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cd "$tmp"
xcaddy build {CADDY_VERSION} --with github.com/sablierapp/sablier-caddy-plugin@{PLUGIN_VERSION}
install -m 0755 caddy /usr/local/bin/caddy-sablier
"""],
            _sudo=True,
            _if=lambda: custom_binary_changed,
        )

    caddy_conf = build_sablier_caddy_config(
        host.data.get("caddy_config", {}),
        host.data.get("docker", {}),
        sablier_options,
    )
    config_file = files.template(
        name="Deploy Caddy configuration file",
        src="templates/Caddyfile.j2",
        dest="/etc/caddy/Caddyfile",
        user="caddy",
        group="root",
        mode="640",
        caddy_conf=caddy_conf,
        _sudo=True,
    )

    override_changed = False
    if sablier_enabled:
        files.directory(
            name="Create Caddy systemd override directory",
            path="/etc/systemd/system/caddy.service.d",
            user="root",
            group="root",
            mode="755",
            _sudo=True,
        )
        override = files.template(
            name="Configure Caddy to use the Sablier-enabled binary",
            src="templates/caddy/override.conf.j2",
            dest="/etc/systemd/system/caddy.service.d/override.conf",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
        )
        override_changed = override.did_change
    else:
        override_present = host.get_fact(
            Command,
            "test -f /etc/systemd/system/caddy.service.d/override.conf && echo present || echo absent",
        ).strip() == "present"
        if override_present:
            server.shell(
                name="Remove the Sablier Caddy override",
                commands=[
                    "rm -f /etc/systemd/system/caddy.service.d/override.conf",
                    "rmdir --ignore-fail-on-non-empty /etc/systemd/system/caddy.service.d",
                    "systemctl daemon-reload",
                ],
                _sudo=True,
                _if=lambda: override_present,
            )
            override_changed = True

    systemd.service(
        name="Ensure Caddy is enabled and running",
        service="caddy",
        enabled=True,
        running=True,
        _sudo=True,
    )

    if custom_binary_changed or override_changed:
        server.shell(
            name="Restart Caddy after binary or service override changes",
            commands=["systemctl daemon-reload", "systemctl restart caddy"],
            _sudo=True,
            _if=lambda: custom_binary_changed or override_changed,
        )
    else:
        server.shell(
            name="Reload Caddy configuration",
            commands=[
                (
                    "/usr/local/bin/caddy-sablier validate --config /etc/caddy/Caddyfile "
                    "&& systemctl reload caddy"
                    if sablier_enabled
                    else "systemctl reload caddy"
                ),
            ],
            _sudo=True,
            _if=lambda: config_file.did_change,
        )


configure_caddy()
