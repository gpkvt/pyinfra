# pylint: disable=E0401, C0301
"""Deploy MDMesh, the self-hosted Android device-management server.

MDMesh is Android-only. Its official release assets are pinned to the configured
`docker.mdmesh.version`, or resolved from the latest stable GitHub release when
set to `"latest"`; database credentials and the initial administrator password
are read from encrypted deployment secrets.
"""

import re
import shlex

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server

from tasks.docker import deploy_docker_service, ensure_numeric_directory
from common import command_output_text

mdmesh = host.data.get("docker", {}).get("mdmesh", {})
mdmesh_secrets = secrets.get("docker", {}).get("mdmesh", {})  # pylint: disable=undefined-variable
username = host.data.get("username", "root")
usergroup = host.data.get("usergroup", "root")
homedir = host.data.get("homedir", f"/home/{username}")

version = mdmesh.get("version", "latest")
if version == "latest":
    release_repo = mdmesh.get("github_repo", "MDMesh-app/MDMesh")
    release_url = f"https://api.github.com/repos/{release_repo}/releases/latest"
    release_query = (
        "python3 -c "
        + shlex.quote(
            "import json, urllib.request; "
            f"request = urllib.request.Request({release_url!r}, "
            "headers={'User-Agent': 'pyinfra-mdmesh-task'}); "
            "print(json.load(urllib.request.urlopen(request, timeout=15))['tag_name'])"
        )
    )
    release_tag = command_output_text(host.get_fact(Command, release_query, _sudo=False)).strip()
    match = re.fullmatch(r"v?(\d+\.\d+\.\d+)", release_tag)
    if not match:
        raise ValueError(
            f"Unable to resolve a stable MDMesh release from {release_url}: {release_tag!r}"
        )
    version = match.group(1)
elif not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise ValueError(
        "docker.mdmesh.version must be 'latest' or a pinned semantic version (for example '0.5.0')"
    )

domain = mdmesh.get("domain")
if not isinstance(domain, str) or not re.fullmatch(
    r"(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}",
    domain,
):
    raise ValueError("docker.mdmesh.domain must be a valid public DNS hostname")

port = mdmesh.get("port", 8030)
if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
    raise ValueError("docker.mdmesh.port must be an integer between 1 and 65535")

admin_email = mdmesh.get("admin_email", f"admin@{domain}")
if not isinstance(admin_email, str) or not re.fullmatch(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", admin_email):
    raise ValueError("docker.mdmesh.admin_email must be a valid email address")

required_secrets = ("database_password", "hash_secret", "admin_password")
missing_secrets = [key for key in required_secrets if not mdmesh_secrets.get(key)]
if missing_secrets:
    raise ValueError(
        "MDMesh requires encrypted secrets under docker.mdmesh: " + ", ".join(missing_secrets)
    )

for key in required_secrets:
    value = mdmesh_secrets[key]
    if not isinstance(value, str) or len(value) < 32 or any(
        char in value for char in ("\n", "\r", "\x00", "'", "\\")
    ):
        raise ValueError(
            f"MDMesh secret {key!r} must contain at least 32 characters and "
            "must not contain quotes, backslashes or line breaks"
        )

image_owner = mdmesh.get("image_owner", "mdmesh-app")
if not isinstance(image_owner, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", image_owner):
    raise ValueError("docker.mdmesh.image_owner must be a lowercase container registry owner")

github_repo = mdmesh.get("github_repo", "MDMesh-app/MDMesh")
if not isinstance(github_repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", github_repo):
    raise ValueError("docker.mdmesh.github_repo must use owner/repository format")

# An always-on MDM must not be paused by Sablier after an idle timeout.
# An explicit per-service setting may opt in, but the safe default is disabled.
mdmesh.setdefault("sablier", {"enabled": False})

trusted_proxies = mdmesh.get("trusted_proxies", ["127.0.0.1/32", "::1/128"])
if not isinstance(trusted_proxies, (list, tuple)) or not all(
    isinstance(item, str) and item.strip() for item in trusted_proxies
):
    raise ValueError("docker.mdmesh.trusted_proxies must be a list of non-empty proxy CIDRs")

root = f"{homedir}/.docker/mdmesh"
bootstrap = f"{root}/bootstrap"

# PostgreSQL 14's official image runs as UID/GID 999.
ensure_numeric_directory(f"{root}/postgres", 999, 999, "700")
for directory in ("server", "caddy/data", "caddy/config", "backups", "bootstrap"):
    files.directory(
        name=f"Create MDMesh {directory} directory",
        path=f"{root}/{directory}",
        user=username,
        group=usergroup,
        mode="750",
    )

# Keep the bootstrap SQL and helper functions on the same signed release as the images.
release_root = f"https://raw.githubusercontent.com/MDMesh-app/MDMesh/refs/tags/v{version}"
for source, destination in (
    ("install/lib/db.sh", f"{bootstrap}/db.sh"),
    ("install/sql/hmdm_init.en.sql", f"{bootstrap}/hmdm_init.en.sql"),
    ("install/sql/post_seed.sql", f"{bootstrap}/post_seed.sql"),
):
    files.download(
        name=f"Download MDMesh {source.rsplit('/', 1)[-1]}",
        src=f"{release_root}/{source}",
        dest=destination,
        user=username,
        group=usergroup,
        mode="640",
        _sudo=False,
    )

deploy_docker_service(
    service="mdmesh",
    description="MDMesh Android Device Management",
    homedir=homedir,
    compose_services=["postgres", "server", "caddy", "supervisor"],
    app_services=["server", "caddy", "supervisor"],
    username=username,
    usergroup=usergroup,
    version=version,
    image_owner=image_owner,
    domain=domain,
    port=port,
    trusted_proxies=trusted_proxies,
    github_repo=github_repo,
    private_env={
        "DB_PASSWORD": mdmesh_secrets["database_password"],
        "HASH_SECRET": mdmesh_secrets["hash_secret"],
        "ADMIN_PASSWORD": mdmesh_secrets["admin_password"],
        "SERVER_VERSION": version,
        "WEB_VERSION": version,
        "SUPERVISOR_VERSION": version,
        "CURRENT_VERSION": version,
    },
)

# Seed only a genuinely fresh database. Existing installations are never reset,
# and an inconsistent database is rejected rather than overwritten.
bootstrap_command = f"""#!/usr/bin/env bash
set -euo pipefail
cd {shlex.quote(root)}
for attempt in $(seq 1 120); do
    if docker compose exec -T postgres pg_isready -U mdmesh -d mdmesh >/dev/null 2>&1; then
        break
    fi
    [ "$attempt" -lt 120 ] || {{ echo "MDMesh PostgreSQL did not become ready" >&2; exit 1; }}
    sleep 5
done
for attempt in $(seq 1 120); do
    state=$(docker compose exec -T postgres psql -U mdmesh -d mdmesh -Atqc \\
        "SELECT to_regclass('public.settings') IS NOT NULL" 2>/dev/null || true)
    [ "$state" = "t" ] && break
    [ "$attempt" -lt 120 ] || {{ echo "MDMesh database schema did not initialize" >&2; exit 1; }}
    sleep 5
done
set -a
. ./.env
set +a
# shellcheck disable=SC1091
. {shlex.quote(bootstrap)}/db.sh
PSQL=(docker compose exec -T postgres psql -U mdmesh -d mdmesh)
state=$(mdm_db_state)
case "$state" in
    fresh)
        mdm_seed {shlex.quote(admin_email)} {shlex.quote(bootstrap + "/hmdm_init.en.sql")} "$ADMIN_PASSWORD" "$(openssl rand -hex 16)"
        ;;
    seeded)
        ;;
    inconsistent)
        echo "MDMesh database is inconsistent; refusing to seed or overwrite existing data" >&2
        exit 1
        ;;
    *)
        echo "Unable to determine MDMesh database state" >&2
        exit 1
        ;;
esac
mdm_post_seed {shlex.quote(bootstrap + "/post_seed.sql")}
"""
post_seed_check = (
    f"cd {shlex.quote(root)} && docker compose exec -T postgres "
    "psql -U mdmesh -d mdmesh -Atqc "
    "'SELECT count(*) FROM settings "
    "WHERE createnewdevices AND newdeviceconfigurationid IS NOT NULL "
    "AND NOT EXISTS (SELECT 1 FROM configurations WHERE qrcodekey IN "
    "('6fb9c8dc81483173a0c0e9f8b2e46be1','8e6ca072ddb926a1af61578dfa9fc334',"
    "'350e0fb7fc3f4b7fe61cac75fd43818f')) "
    "AND NOT EXISTS (SELECT 1 FROM applications WHERE pkg IN "
    "('com.hmdm.launcher','com.hmdm.pager','com.hmdm.phoneproxy',"
    "'com.hmdm.emuilauncherrestarter'))' "
    "2>/dev/null"
)
server.shell(
    name="Initialize MDMesh database and enrollment defaults",
    commands=[bootstrap_command],
    _sudo=False,
    _if=lambda: command_output_text(host.get_fact(Command, post_seed_check, _sudo=False)).strip() != "1",
)
