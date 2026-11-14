# pylint: disable=C0301, E0401, C0116, E1101
"""Deploy Caddy, its Sablier module and Dehydrated in Docker."""

import builtins
import re
import shlex
from copy import deepcopy

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from common import command_output_text, compose_configuration_matches, initialize
from tasks.homepage_config import homepage_api_exclusions

def required_version(config, key, setting):
    """Return an explicitly configured software version or fail clearly."""
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{setting} must be explicitly configured as a non-empty string")
    return value.strip()



def build_sablier_caddy_config(caddy_config, docker_config, options):
    """Wrap only configured Docker reverse proxies in Sablier routes."""
    result = deepcopy(caddy_config)
    if not options.get("enabled", False):
        return result

    duration = options.get("default_duration", "60m")
    timeout = options.get("blocking_timeout", "15m")
    default_strategy = options.get("strategy", "dynamic")
    default_theme = options.get("default_theme", "ghost")
    refresh_frequency = options.get("refresh_frequency", "5s")

    homepage_exclusions = homepage_api_exclusions(options.get("homepage_services", []))

    def wrap_routes(service, port, service_options):
        sablier_options = service_options.get("sablier", {})
        if not sablier_options.get("enabled", True):
            return
        group = sablier_options.get("group", service)
        strategy = sablier_options.get("strategy", default_strategy)
        sablier_route = {
            "group": group,
            "session_duration": sablier_options.get("session_duration", duration),
        }
        if strategy == "dynamic":
            sablier_route["dynamic"] = {
                "display_name": sablier_options.get(
                    "display_name", service.replace("-", " ").title()
                ),
                "theme": sablier_options.get("theme", default_theme),
                "show_details": str(sablier_options.get("show_details", True)).lower(),
                "refresh_frequency": sablier_options.get(
                    "refresh_frequency", refresh_frequency
                ),
            }
        elif strategy == "blocking":
            sablier_route["blocking"] = {
                "timeout": sablier_options.get("blocking_timeout", timeout),
            }
        else:
            raise ValueError(f"Unsupported Sablier strategy for {service}: {strategy}")

        for address, directives in result.items():
            upstream = directives.get("reverse_proxy")
            if upstream != f"127.0.0.1:{int(port)}":
                continue
            hostname = address.split(":", 1)[0].strip("[]").lower()
            api_paths = homepage_exclusions.get(hostname, [])
            route = {}
            if api_paths:
                route["@homepage_api"] = {"path": " ".join(api_paths)}
                route["handle @homepage_api"] = {
                    "reverse_proxy": upstream,
                }
            route["sablier http://127.0.0.1:10000"] = deepcopy(sablier_route)
            route["reverse_proxy"] = upstream
            directives.pop("reverse_proxy")
            directives["route"] = route

    for service, service_options in docker_config.items():
        # The primary published port and any additional *_port entries are
        # defined alongside each service in group_data/@local.py.
        ports = [
            value
            for key, value in service_options.items()
            if (key == "port" or key.endswith("_port")) and value is not None
        ]
        for port in ports:
            wrap_routes(service, port, service_options)
    return result


def build_domains_file(certificates):
    """Validate certificate definitions and return one domains.txt line per certificate."""
    if not isinstance(certificates, list) or not certificates:
        raise ValueError("dehydrated_domains must contain at least one certificate definition")
    pattern = re.compile(
        r"^(?:\*\.)?[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
    )
    seen = set()
    lines = []
    for index, names in enumerate(certificates, start=1):
        if not isinstance(names, (list, tuple)) or not names:
            raise ValueError(f"Certificate definition {index} must be a non-empty list of domain names")
        normalized = []
        for name in names:
            if not isinstance(name, str):
                raise ValueError(f"Certificate definition {index} contains a non-string domain")
            name = name.strip().lower()
            if not pattern.fullmatch(name):
                raise ValueError(f"Invalid domain name in dehydrated_domains: {name!r}")
            if name in seen:
                raise ValueError(f"Domain appears in more than one certificate definition: {name}")
            seen.add(name)
            normalized.append(name)
        lines.append(" ".join(normalized))
    return lines


if not hasattr(__import__("builtins"), "homedir"):
    initialize(host)


@deploy("Configure Caddy Docker container")
def configure_caddy():  # pylint: disable=R0914
    docker_config = host.data.get("docker", {})
    if not docker_config:
        raise ValueError("Caddy Docker deployment requires Docker to be configured")
    api_token = builtins.secrets.get("dehydrated", {}).get("hetzner_api_token")
    if not api_token:
        raise ValueError("secrets.dehydrated.hetzner_api_token is required for DNS-01 certificates")

    domain_lines = build_domains_file(host.data.get("dehydrated_domains"))
    caddy_versions = host.data.get("caddy_versions", {})
    caddy_version = required_version(caddy_versions, "version", "caddy_versions.version")
    plugin_version = required_version(
        caddy_versions, "sablier_plugin", "caddy_versions.sablier_plugin"
    )
    dehydrated_version = required_version(
        caddy_versions, "dehydrated", "caddy_versions.dehydrated"
    )
    image = f"pyinfra/caddy-sablier:{caddy_version}"
    sablier_options = host.data.get("docker_sablier", {})
    username = host.data.get("username", "root")
    usergroup = host.data.get("usergroup", "root")
    homedir = host.data.get("homedir", f"/home/{username}")
    uid = command_output_text(host.get_fact(Command, f"id -u {shlex.quote(username)}")).strip()
    gid = command_output_text(host.get_fact(Command, f"id -g {shlex.quote(usergroup)}")).strip()

    root = f"{homedir}/.docker/caddy"
    build_dir = f"{root}/build"
    for path in (root, build_dir, f"{root}/config-files", f"{root}/dehydrated", f"{root}/data", f"{root}/config"):
        files.directory(
            name=f"Create Caddy directory {path}",
            path=path, user=username, group=usergroup, mode="750",
        )

    caddy_conf = build_sablier_caddy_config(
        host.data.get("caddy_config", {}), docker_config, {
            **sablier_options,
            "homepage_services": host.data.get("docker", {}).get("homepage", {}).get("services", []),
        },
    )
    files.template(
        name="Deploy Caddyfile",
        src="templates/Caddyfile.j2",
        dest=f"{root}/config-files/Caddyfile",
        user=username, group=usergroup, mode="640",
        caddy_conf=caddy_conf, _sudo=False,
    )
    domains_file = files.template(
        name="Deploy Dehydrated certificate definitions",
        src="templates/caddy/domains.txt.j2",
        dest=f"{root}/config-files/domains.txt",
        user=username, group=usergroup, mode="640",
        domain_lines=domain_lines, _sudo=False,
    )
    dehydrated_config = files.template(
        name="Deploy Dehydrated configuration",
        src="templates/dehydrated_config.j2",
        dest=f"{root}/config-files/dehydrated.conf",
        user=username, group=usergroup, mode="640", _sudo=False,
    )
    env_file = files.template(
        name="Deploy Hetzner DNS API environment",
        src="templates/caddy/hetzner.env.j2",
        dest=f"{root}/hetzner.env",
        user=username, group=usergroup, mode="600",
        api_token=api_token, _sudo=False,
    )
    dockerfile = files.template(
        name="Deploy Caddy Dockerfile",
        src="templates/caddy/Dockerfile.j2",
        dest=f"{build_dir}/Dockerfile",
        user=username, group=usergroup, mode="640",
        caddy_version=caddy_version,
        sablier_plugin_version=plugin_version,
        dehydrated_version=dehydrated_version,
        _sudo=False,
    )
    entrypoint = files.put(
        name="Deploy Caddy container entrypoint",
        src="files/caddy/entrypoint.sh",
        dest=f"{build_dir}/entrypoint.sh",
        user=username, group=usergroup, mode="750", _sudo=False,
    )
    hook = files.put(
        name="Deploy Hetzner DNS challenge hook",
        src="files/dehydrated_hook.sh",
        dest=f"{build_dir}/hook.sh",
        user=username, group=usergroup, mode="750", _sudo=False,
    )
    renew_script = files.put(
        name="Deploy Dehydrated renewal script",
        src="files/caddy/renew.sh",
        dest=f"{build_dir}/renew.sh",
        user=username, group=usergroup, mode="750", _sudo=False,
    )
    compose = files.template(
        name="Deploy Caddy Docker Compose configuration",
        src="templates/docker/caddy/docker-compose.yml.j2",
        dest=f"{root}/docker-compose.yml",
        user=username, group=usergroup, mode="640",
        homedir=homedir, uid=uid, gid=gid, image=image, _sudo=False,
    )

    renewal_service = files.template(
        name="Deploy Caddy certificate renewal service",
        src="templates/caddy/dehydrated-renew.service.j2",
        dest=f"{homedir}/.config/systemd/user/caddy-renew.service",
        user=username, group=usergroup, mode="644", uid=uid, gid=gid, _sudo=False,
    )
    renewal_timer = files.template(
        name="Deploy Caddy certificate renewal timer",
        src="templates/caddy/dehydrated-renew.timer.j2",
        dest=f"{homedir}/.config/systemd/user/caddy-renew.timer",
        user=username, group=usergroup, mode="644", _sudo=False,
    )
    current_uid = command_output_text(host.get_fact(Command, "id -u", _sudo=False)).strip()
    if not uid.isdigit():
        raise RuntimeError(f"Unable to determine UID for systemd user {username!r}")
    if current_uid == uid:
        systemctl_user = (
            f"env XDG_RUNTIME_DIR=/run/user/{uid} "
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus "
            "systemctl --user"
        )
    elif current_uid == "0":
        systemctl_user = (
            f"runuser -u {shlex.quote(username)} -- env "
            f"XDG_RUNTIME_DIR=/run/user/{uid} "
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus "
            "systemctl --user"
        )
    else:
        raise RuntimeError(
            f"Cannot manage systemd user {username!r} (UID {uid}) "
            f"from unprivileged UID {current_uid}"
        )
    def renewal_timer_active():
        return command_output_text(host.get_fact(
            Command,
            f"{systemctl_user} is-active caddy-renew.timer || true",
            _sudo=False,
        )).strip() == "active"
    server.shell(
        name="Enable daily Caddy certificate renewal",
        commands=[
            f"{systemctl_user} daemon-reload",
            f"{systemctl_user} enable --now caddy-renew.timer",
        ],
        _sudo=False,
        _if=lambda: (
            renewal_service.did_change() or renewal_timer.did_change()
            or not renewal_timer_active()
        ),
    )

    def build_changed():
        return (
            dockerfile.did_change() or entrypoint.did_change()
            or hook.did_change() or renew_script.did_change()
        )
    def image_present():
        return command_output_text(host.get_fact(
            Command,
            f"docker image inspect {shlex.quote(image)} >/dev/null 2>&1 && echo present || echo absent",
        )).strip() == "present"
    build_image = server.shell(
        name="Build Caddy image with Sablier plugin and Dehydrated",
        commands=[f"docker build --tag {shlex.quote(image)} {shlex.quote(build_dir)}"],
        _sudo=False, _if=lambda: build_changed() or not image_present(),
    )

    def container_running():
        return command_output_text(host.get_fact(
            Command, "docker inspect -f '{{.State.Running}}' caddy 2>/dev/null || true"
        )).strip() == "true"

    def container_healthy():
        return command_output_text(host.get_fact(
            Command, "docker inspect -f '{{.State.Health.Status}}' caddy 2>/dev/null || true"
        )).strip() == "healthy"
    def recreate():
        return (
            compose.did_change() or build_changed() or build_image.did_change()
            or domains_file.did_change() or dehydrated_config.did_change()
            or env_file.did_change()
            or not container_running() or not container_healthy()
            or not compose_configuration_matches(
                host, f"docker compose -f {shlex.quote(root + '/docker-compose.yml')}"
            )
        )
    start_caddy = server.shell(
        name="Start Caddy and Dehydrated containers",
        commands=[
            f"docker compose -f {shlex.quote(root + '/docker-compose.yml')} up -d --force-recreate"
        ],
        _sudo=False, _if=recreate,
    )
    server.shell(
        name="Wait for Caddy container health",
        commands=[
            "for attempt in $(seq 1 60); do "
            "status=$(docker inspect -f '{{.State.Health.Status}}' caddy 2>/dev/null || true); "
            "if [ \"$status\" = healthy ]; then exit 0; fi; "
            "sleep 5; "
            "done; "
            "docker logs caddy; "
            "echo 'Caddy did not become healthy within 5 minutes' >&2; exit 1"
        ],
        _sudo=False, _if=start_caddy.did_change,
    )
    # Track the last Caddyfile that was successfully validated and reloaded.
    # This survives pyinfra runs, so a skipped/failed reload is retried even
    # when files.template reports no change on the next deployment.
    def caddyfile_loaded():
        return command_output_text(host.get_fact(
            Command,
            "docker exec --user "
            + f"{uid}:{gid} caddy sh -ec "
            + "'current=$(sha256sum /etc/pyinfra-caddy/Caddyfile | cut -d \" \" -f1); "
            + "previous=$(cat /config/.pyinfra-caddyfile.sha256 2>/dev/null || true); "
            + "[ \"$current\" = \"$previous\" ] && printf match || printf drift'",
        )).strip() == "match"
    server.shell(
        name="Validate and reload Caddy when deployed configuration is unacknowledged",
        commands=[
            f"docker exec --user {uid}:{gid} caddy sh -ec "
            + "'caddy validate --config /etc/pyinfra-caddy/Caddyfile "
            + "&& caddy reload --config /etc/pyinfra-caddy/Caddyfile "
            + "&& sha256sum /etc/pyinfra-caddy/Caddyfile | cut -d \" \" -f1 "
            + "> /config/.pyinfra-caddyfile.sha256.tmp "
            + "&& mv /config/.pyinfra-caddyfile.sha256.tmp "
            + "/config/.pyinfra-caddyfile.sha256'"
        ],
        _sudo=False,
        _if=lambda: not caddyfile_loaded(),
    )



if host.data.get("caddy_config"):
    configure_caddy()
