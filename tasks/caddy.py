# pylint: disable=C0301, E0401, C0116, E1101
"""Deploy Caddy, its Sablier module and Dehydrated in Docker."""

import re
import shlex
from copy import deepcopy

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.facts.server import Command
from pyinfra.operations import apt, files, server

CADDY_VERSION = "2.11.2"
PLUGIN_VERSION = "v1.0.2"
IMAGE = f"pyinfra/caddy-sablier:{CADDY_VERSION}"

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
def configure_caddy():
    docker_config = host.data.get("docker", {})
    if not docker_config:
        raise ValueError("Caddy Docker deployment requires Docker to be configured")
    api_token = secrets.get("dehydrated", {}).get("hetzner_api_token")
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
    for path in (root, build_dir, f"{root}/dehydrated", f"{root}/data", f"{root}/config"):
        files.directory(
            name=f"Create Caddy directory {path}",
            path=path, user=username, group=usergroup, mode="750",
        )

    caddy_conf = build_sablier_caddy_config(
        host.data.get("caddy_config", {}), docker_config, sablier_options,
    )
    caddyfile = files.template(
        name="Deploy Caddyfile",
        src="templates/Caddyfile.j2",
        dest=f"{root}/Caddyfile",
        user=username, group=usergroup, mode="640",
        caddy_conf=caddy_conf, _sudo=False,
    )
    domains_file = files.template(
        name="Deploy Dehydrated certificate definitions",
        src="templates/caddy/domains.txt.j2",
        dest=f"{root}/domains.txt",
        user=username, group=usergroup, mode="640",
        domain_lines=domain_lines, _sudo=False,
    )
    dehydrated_config = files.template(
        name="Deploy Dehydrated configuration",
        src="templates/dehydrated_config.j2",
        dest=f"{root}/dehydrated.conf",
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
    compose = files.template(
        name="Deploy Caddy Docker Compose configuration",
        src="templates/docker/caddy/docker-compose.yml.j2",
        dest=f"{root}/docker-compose.yml",
        user=username, group=usergroup, mode="640",
        homedir=homedir, uid=uid, gid=gid, image=IMAGE, _sudo=False,
    )

    build_changed = dockerfile.did_change or entrypoint.did_change or hook.did_change
    image_present = host.get_fact(
        Command,
        f"docker image inspect {shlex.quote(IMAGE)} >/dev/null 2>&1 && echo present || echo absent",
    ).strip() == "present"
    server.shell(
        name="Build Caddy image with Sablier plugin and Dehydrated",
        commands=[f"docker build --tag {shlex.quote(IMAGE)} {shlex.quote(build_dir)}"],
        _sudo=False, _if=lambda: build_changed or not image_present,
    )

    host_active = host.get_fact(
        Command, "systemctl is-active caddy.service 2>/dev/null || true"
    ).strip() == "active"
    host_enabled = host.get_fact(
        Command, "systemctl is-enabled caddy.service 2>/dev/null || true"
    ).strip() == "enabled"
    server.shell(
        name="Stop host Caddy before binding container ports",
        commands=["systemctl disable --now caddy.service"],
        _sudo=True, _if=lambda: host_active or host_enabled,
    )

    container_running = host.get_fact(
        Command, "docker inspect -f '{{.State.Running}}' caddy 2>/dev/null || true"
    ).strip() == "true"
    recreate = (
        compose.did_change or build_changed or domains_file.did_change
        or dehydrated_config.did_change or env_file.did_change
        or not container_running
    )
    server.shell(
        name="Start Caddy and Dehydrated containers",
        commands=[
            f"docker compose -f {shlex.quote(root + '/docker-compose.yml')} up -d --build"
            + (" --force-recreate" if env_file.did_change else "")
        ],
        _sudo=False, _if=lambda: recreate,
    )
    server.shell(
        name="Renew certificates after domain or Dehydrated configuration changes",
        commands=[
            "docker exec caddy dehydrated --cron --accept-terms --keep-going --config /etc/dehydrated/config",
            "docker exec caddy caddy reload --config /etc/caddy/Caddyfile",
        ],
        _sudo=False,
        _if=lambda: (domains_file.did_change or dehydrated_config.did_change) and container_running,
    )
    server.shell(
        name="Reload Caddy after Caddyfile changes",
        commands=["docker exec caddy caddy reload --config /etc/caddy/Caddyfile"],
        _sudo=False,
        _if=lambda: caddyfile.did_change and container_running and not recreate,
    )

    apt.packages(
        name="Remove obsolete host Caddy and Dehydrated packages",
        packages=["caddy", "dehydrated"], present=False, _sudo=True,
    )
    legacy_build_artifacts = host.get_fact(
        Command,
        "if [ -e /usr/local/bin/caddy-sablier ] || [ -e /usr/local/bin/xcaddy ] || [ -d /opt/go1.25.4 ]; then echo present; else echo absent; fi",
    ).strip() == "present"
    server.shell(
        name="Remove obsolete host-built Caddy artifacts",
        commands=[
            "rm -f /usr/local/bin/caddy-sablier /usr/local/bin/xcaddy",
            "rm -rf /opt/go1.25.4",
        ],
        _sudo=True,
        _if=lambda: legacy_build_artifacts,
    )
    override_present = host.get_fact(
        Command, "test -f /etc/systemd/system/caddy.service.d/override.conf && echo yes || echo no"
    ).strip() == "yes"
    server.shell(
        name="Remove obsolete host Caddy systemd override",
        commands=[
            "rm -f /etc/systemd/system/caddy.service.d/override.conf",
            "rmdir --ignore-fail-on-non-empty /etc/systemd/system/caddy.service.d",
            "systemctl daemon-reload",
        ],
        _sudo=True, _if=lambda: override_present,
    )


if host.data.get("caddy_config"):
    configure_caddy()
