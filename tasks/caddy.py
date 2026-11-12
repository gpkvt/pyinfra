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

from tasks.homepage_config import homepage_api_exclusions

CADDY_VERSION = "2.11.2"
PLUGIN_VERSION = "v1.0.2"
IMAGE = f"pyinfra/caddy-sablier:{CADDY_VERSION}"



def build_sablier_caddy_config(caddy_config, docker_config, options):
    """Wrap only configured Docker reverse proxies in Sablier routes."""
    result = deepcopy(caddy_config)
    if not options.get("enabled", False):
        return result

    duration = options.get("default_duration", "60m")
    timeout = options.get("blocking_timeout", "15m")

    homepage_exclusions = homepage_api_exclusions(options.get("homepage_services", []))

    def wrap_routes(service, port, service_options):
        sablier_options = service_options.get("sablier", {})
        if not sablier_options.get("enabled", True):
            return
        group = sablier_options.get("group", service)
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
            route["sablier http://127.0.0.1:10000"] = {
                "group": group,
                "session_duration": sablier_options.get("session_duration", duration),
                "blocking": {
                    "timeout": sablier_options.get("blocking_timeout", timeout),
                },
            }
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
    from common import initialize
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
    sablier_options = host.data.get("docker_sablier", {})
    username = host.data.get("username", "root")
    usergroup = host.data.get("usergroup", "root")
    homedir = host.data.get("homedir", f"/home/{username}")
    uid = host.get_fact(Command, f"id -u {shlex.quote(username)}").strip()
    gid = host.get_fact(Command, f"id -g {shlex.quote(usergroup)}").strip()

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
    caddyfile = files.template(
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
    dockerfile = files.put(
        name="Deploy Caddy Dockerfile",
        src="files/caddy/Dockerfile",
        dest=f"{build_dir}/Dockerfile",
        user=username, group=usergroup, mode="640", _sudo=False,
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
        homedir=homedir, uid=uid, gid=gid, image=IMAGE, _sudo=False,
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
    current_uid = (host.get_fact(Command, "id -u", _sudo=False) or "").strip()
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
    renewal_timer_status = host.get_fact(
        Command, f"{systemctl_user} is-active caddy-renew.timer", _sudo=False
    ) or ""
    renewal_timer_active = renewal_timer_status.strip() == "active"
    server.shell(
        name="Enable daily Caddy certificate renewal",
        commands=[
            f"{systemctl_user} daemon-reload",
            f"{systemctl_user} enable --now caddy-renew.timer",
        ],
        _sudo=False,
        _if=lambda: (
            renewal_service.did_change() or renewal_timer.did_change()
            or not renewal_timer_active
        ),
    )

    def build_changed():
        return (
            dockerfile.did_change() or entrypoint.did_change()
            or hook.did_change() or renew_script.did_change()
        )
    image_present = host.get_fact(
        Command,
        f"docker image inspect {shlex.quote(IMAGE)} >/dev/null 2>&1 && echo present || echo absent",
    ).strip() == "present"
    server.shell(
        name="Build Caddy image with Sablier plugin and Dehydrated",
        commands=[f"docker build --tag {shlex.quote(IMAGE)} {shlex.quote(build_dir)}"],
        _sudo=False, _if=lambda: build_changed() or not image_present,
    )

    container_running = host.get_fact(
        Command, "docker inspect -f '{{.State.Running}}' caddy 2>/dev/null || true"
    ).strip() == "true"
    container_healthy = host.get_fact(
        Command, "docker inspect -f '{{.State.Health.Status}}' caddy 2>/dev/null || true"
    ).strip() == "healthy"
    def recreate():
        return (
            compose.did_change() or build_changed()
            or domains_file.did_change() or dehydrated_config.did_change()
            or env_file.did_change()
            or not container_running or not container_healthy
        )
    server.shell(
        name="Start Caddy and Dehydrated containers",
        commands=[
            f"docker compose -f {shlex.quote(root + '/docker-compose.yml')} up -d"
            + (" --force-recreate" if container_running and not container_healthy else "")
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
        _sudo=False, _if=recreate,
    )
    server.shell(
        name="Reload Caddy after Caddyfile changes",
        commands=[
            f"docker exec --user {uid}:{gid} caddy "
            "caddy reload --config /etc/pyinfra-caddy/Caddyfile"
        ],
        _sudo=False,
        _if=lambda: caddyfile.did_change() and container_running and not recreate(),
    )



if host.data.get("caddy_config"):
    configure_caddy()
