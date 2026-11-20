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
from pyinfra.facts.files import Directory
from pyinfra.operations import files, server

from tasks.docker import deploy_docker_service, ensure_numeric_directory
from common import command_output_text

def deploy_mdmesh():  # pylint: disable=R0912,R0914,R0915
    """Schedule MDMesh deployment when its required public domain is configured."""
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

    # MDMesh must remain available for Android device check-ins and database
    # initialization. Sablier lazy-start/idle-stop is not supported.
    mdmesh["sablier"] = {"enabled": False}

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
        directory_path = f"{root}/{directory}"
        # MDMesh containers may change the owner/mode of runtime storage.
        # Establish the expected owner only on initial creation; do not
        # repeatedly overwrite legitimate container-managed metadata.
        files.directory(
            name=f"Create MDMesh {directory} directory",
            path=directory_path,
            user=username,
            group=usergroup,
            mode="750",
            _if=lambda directory_path=directory_path: not host.get_fact(
                Directory, path=directory_path
            ),
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
        schema_ready=$(docker compose exec -T postgres psql -U mdmesh -d mdmesh -Atqc \\
            "SELECT to_regclass('public.settings') IS NOT NULL AND to_regclass('public.devices') IS NOT NULL" \\
            2>/dev/null || true)
        [ "$schema_ready" = "t" ] && break
        [ "$attempt" -lt 120 ] || {{ echo "MDMesh settings/devices schema did not initialize" >&2; exit 1; }}
        sleep 5
    done
    set -a
    . ./.env
    set +a
    ADMIN_EMAIL={shlex.quote(admin_email)}
    # shellcheck disable=SC1091
    . {shlex.quote(bootstrap)}/db.sh
    PSQL=(docker compose exec -T postgres psql -U mdmesh -d mdmesh)
    state=$(mdm_db_state)
    case "$state" in
        fresh)
            mdm_seed "$ADMIN_EMAIL" {shlex.quote(bootstrap + "/hmdm_init.en.sql")} "$ADMIN_PASSWORD" "$(openssl rand -hex 16)"
            # Enrollment defaults are part of first-time database creation only.
            mdm_post_seed {shlex.quote(bootstrap + "/post_seed.sql")}
            ;;
        seeded)
            # A previous run may have committed seed SQL but stopped before
            # mdm_seed wrote the configured password. Repair only this first-login
            # state; passwordreset=false means an administrator has changed it.
            admin_hash=$(mdm_pwhash "$ADMIN_PASSWORD")
            admin_state=$(mdm_psql -c "SELECT CASE WHEN email = '$ADMIN_EMAIL' THEN 't' ELSE 'f' END || '/' || CASE WHEN passwordreset THEN 't' ELSE 'f' END || '/' || CASE WHEN password = '$admin_hash' THEN 't' ELSE 'f' END FROM users WHERE login='admin'" | tr -d '[:space:]')
            case "$admin_state" in
                t/t/f)
                    reset_token=$(openssl rand -hex 16)
                    printf '%s\\n' "UPDATE users SET password='$admin_hash', passwordresettoken='$reset_token' WHERE login='admin' AND email='$ADMIN_EMAIL' AND passwordreset=true;" | mdm_psql
                    ;;
                t/t/t|t/f/t|t/f/f)
                    ;;
                *)
                    echo "MDMesh administrator record is missing or has an unexpected email/state; refusing to overwrite it" >&2
                    exit 1
                    ;;
            esac
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
    """
    database_state_script = f"""#!/usr/bin/env bash
    set -euo pipefail
    cd {shlex.quote(root)}
    # The _if predicate runs before the bootstrap operation. Wait here (not only
    # inside bootstrap_command) for PostgreSQL and both tables used by mdm_db_state;
    # otherwise a normal first-start Liquibase migration looks like an unknown state.
    for attempt in $(seq 1 120); do
        if docker compose exec -T postgres pg_isready -U mdmesh -d mdmesh >/dev/null 2>&1; then
            schema_ready=$(docker compose exec -T postgres psql -U mdmesh -d mdmesh -Atqc \\
                "SELECT to_regclass('public.settings') IS NOT NULL AND to_regclass('public.devices') IS NOT NULL" \\
                2>/dev/null || true)
            [ "$schema_ready" = "t" ] && break
        fi
        [ "$attempt" -lt 120 ] || {{ echo unavailable; exit 0; }}
        sleep 5
    done
    set -a
    . ./.env
    set +a
    . {shlex.quote(bootstrap)}/db.sh
    PSQL=(docker compose exec -T postgres psql -U mdmesh -d mdmesh)
    mdm_db_state
    """
    database_state_check = f"bash -c {shlex.quote(database_state_script)}"

    def mdmesh_needs_initialization():
        # Seed only a fresh database. A seeded database must not re-enter the
        # bootstrap operation because an administrator password changed or
        # enrollment settings were edited after initial setup.
        state = command_output_text(
            host.get_fact(Command, database_state_check, _sudo=False)
        ).strip()
        # Only a confirmed fresh database may enter the initialization
        # operation. Existing or inconsistent databases are left untouched;
        # unknown states fail closed rather than being treated as fresh.
        if state == "fresh":
            return True
        if state in {"seeded", "inconsistent"}:
            return False
        raise RuntimeError(
            f"Unable to determine MDMesh database state: {state!r}"
        )

    server.shell(
        name="Initialize MDMesh database and enrollment defaults",
        # pyinfra executes shell commands through /bin/sh; run this Bash-specific script explicitly with Bash.
        commands=[f"bash -c {shlex.quote(bootstrap_command)}"],
        _sudo=False,
        _if=mdmesh_needs_initialization,
    )


# MDMesh is optional; a missing domain means no deployment is requested.
if host.data.get("docker", {}).get("mdmesh", {}).get("domain"):
    deploy_mdmesh()
