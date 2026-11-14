"""Keep CI coverage inventory synchronized with every task and utility."""

import ast
import builtins
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".github" / "ci" / "task_coverage.json"


def _discovered_files(directory, suffixes=None):
    paths = (ROOT / directory).rglob("*")
    return {
        path.relative_to(ROOT).as_posix()
        for path in paths
        if path.is_file()
        and (suffixes is None or path.suffix in suffixes)
        and "__pycache__" not in path.parts
    }


def test_every_task_and_utility_has_an_explicit_coverage_entry():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    discovered = _discovered_files("tasks", {".py"})
    discovered |= _discovered_files("files/scripts")

    missing = discovered - coverage.keys()
    stale = coverage.keys() - discovered

    assert not missing, f"Missing CI coverage entries: {sorted(missing)}"
    assert not stale, f"Stale CI coverage entries: {sorted(stale)}"


def test_coverage_entries_use_supported_execution_kinds():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    invalid = {
        path: kind
        for path, kind in coverage.items()
        if kind not in {"deployment", "dispatcher", "helper", "utility"}
    }

    assert not invalid, f"Unsupported CI coverage kinds: {invalid}"
    assert coverage.get("tasks/homepage_config.py") == "helper"
    assert coverage.get("tasks/workstation/cosmic/config.py") == "helper"
    assert all(
        kind == "deployment"
        for path, kind in coverage.items()
        if path.startswith("tasks/")
        and path not in {
            "tasks/homepage_config.py",
            "tasks/workstation/cosmic/config.py",
            "tasks/docker/linkwarden_bookmarks.py",
            "tasks/workstation/cosmic/deploy.py",
            "tasks/docker_container.py",
        }
    )
    assert coverage.get("tasks/workstation/cosmic/deploy.py") == "dispatcher"
    assert coverage.get("tasks/docker_container.py") == "dispatcher"
    assert all(
        kind == "utility"
        for path, kind in coverage.items()
        if path.startswith("files/scripts/")
        or path == "tasks/docker/linkwarden_bookmarks.py"
    )


def test_deployment_modules_and_dispatchers_import_pyinfra():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for relative_path, kind in coverage.items():
        if kind not in {"deployment", "dispatcher"}:
            continue

        source = (ROOT / relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative_path)
        imports_pyinfra = any(
            isinstance(node, ast.Import)
            and any(alias.name == "pyinfra" or alias.name.startswith("pyinfra.")
                    for alias in node.names)
            or isinstance(node, ast.ImportFrom)
            and (node.module == "pyinfra" or (node.module or "").startswith("pyinfra."))
            for node in ast.walk(tree)
        )
        assert imports_pyinfra, (
            f"{relative_path} is classified as a deployment but does not "
            "import the pyinfra API"
        )


def test_python_utility_sources_compile():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for relative_path, kind in coverage.items():
        if kind != "utility" or not relative_path.endswith(".py"):
            continue

        source = (ROOT / relative_path).read_text(encoding="utf-8")
        compile(source, relative_path, "exec")


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash is unavailable")
def test_shell_utilities_pass_bash_syntax_validation():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for relative_path, kind in coverage.items():
        if kind != "utility" or relative_path.endswith(".py"):
            continue

        result = subprocess.run(
            ["bash", "-n", str(ROOT / relative_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"{relative_path} failed bash -n:\\n{result.stderr}"
        )



def test_dispatchers_include_child_task_modules():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for relative_path, kind in coverage.items():
        if kind != "dispatcher":
            continue

        tree = ast.parse(
            (ROOT / relative_path).read_text(encoding="utf-8"),
            filename=relative_path,
        )
        includes = {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "include"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
        assert includes, f"{relative_path} does not include any child tasks"



@pytest.mark.parametrize(
    "relative_path",
    [
        path
        for path, kind in json.loads(MANIFEST.read_text(encoding="utf-8")).items()
        if kind in {"deployment", "dispatcher"}
    ],
)
def test_every_task_module_evaluates_in_a_pyinfra_context(
    pyinfra_task_harness, monkeypatch, relative_path
):  # pylint: disable=R0912
    """Evaluate every deployable module, including nested service tasks."""
    module_path = relative_path.removeprefix("tasks/")
    calls_before = len(pyinfra_task_harness.calls)
    includes_before = len(pyinfra_task_harness.included)
    if relative_path.startswith("tasks/docker/"):
        monkeypatch.delitem(sys.modules, "tasks.docker", raising=False)
        service = Path(relative_path).stem
        docker_config = {service: {}}
        if service == "ci-smoke":
            docker_config[service] = {
                "image": "alpine:3.21",
                "app_services": ["smoke"],
            }

        monkeypatch.setattr(
            builtins,
            "secrets",
            {
                "docker": {
                    "appflowy": {
                        "postgres_password": "a" * 40,
                        "admin_password": "b" * 40,
                        "jwt_secret": "c" * 40,
                        "minio_access_key": "d" * 20,
                        "minio_secret_key": "e" * 40,
                    },
                    "firefly-iii": {
                        "database_password": "ci-database",
                        "mysql_root_password": "ci-mysql-root",
                        "app_key": "base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                        "cron_token": "f" * 32,
                    },
                    "linkwarden": {
                        "postgres_password": "ci-linkwarden-db",
                        "nextauth_secret": "ci-linkwarden-nextauth",
                        "meili_master_key": "ci-linkwarden-meili",
                    },
                    "miniflux": {
                        "postgres_password": "ci-miniflux-db",
                        "admin_username": "ci-admin",
                        "admin_password": "ci-miniflux-admin",
                    },
                    "paperless": {
                        "postgres_password": "ci-postgres",
                        "secret_key": "ci-paperless-secret",
                    },
                    "snipe-it": {
                        "database_password": "ci-database",
                        "mysql_root_password": "ci-mysql-root",
                        "app_key": "base64:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
                    },
                    "timetagger": {"credentials": "ci:$2a$08$fake-hash"},
                }
            },
            raising=False,
        )
        pyinfra_task_harness.load(
            module_path,
            {
                "docker": docker_config,
                "docker_sablier": {"enabled": False},
                "docker_power_monitor": False,
            },
        )
    else:
        data = {}
        if relative_path == "tasks/caddy.py":
            monkeypatch.delitem(sys.modules, "tasks.docker", raising=False)
            monkeypatch.setattr(
                builtins,
                "secrets",
                {"dehydrated": {"hetzner_api_token": "ci-dummy-token"}},
                raising=False,
            )
            data = {
                "caddy_config": {"ci.invalid": {"respond": "CI"}},
                "docker": {"ci-smoke": {"app_services": ["smoke"]}},
                "docker_sablier": {"enabled": False},
                "dehydrated_domains": [["ci.invalid"]],
                "username": "tester",
                "usergroup": "tester",
                "homedir": "/home/tester",
            }
        elif relative_path.startswith("tasks/workstation/cosmic/"):
            monkeypatch.delitem(sys.modules, "tasks.workstation.cosmic.config", raising=False)
            data = {
                "workstation": {
                    "cosmic": {
                        "enabled": True,
                        "appearance": {"enabled": True},
                        "window_management": {"enabled": True, "autotile": False},
                        "input": {"enabled": True, "default": "()"},
                        "shortcuts": {"enabled": True, "ron": "{}"},
                        "dock": {"enabled": True},
                        "panel": {"enabled": True},
                        "workspaces": {"enabled": True, "ron": "[]"},
                        "config_files": {
                            "custom": {"src": "files", "dest": ".config/cosmic/custom"}
                        },
                    }
                },
                "username": "tester",
                "usergroup": "tester",
                "homedir": "/home/tester",
            }
        elif relative_path == "tasks/cron.py":
            data = {
                "username": "tester",
                "cron_jobs": [{
                    "name": "ci-coverage",
                    "command": "/usr/bin/true",
                    "minute": "0",
                    "hour": "0",
                }],
            }
        elif relative_path == "tasks/docker_container.py":
            data = {"docker": {"ci-smoke": {"app_services": ["smoke"]}}}
        elif relative_path == "tasks/proton.py":
            data = {
                "proton": {
                    "mail": True,
                    "bridge": False,
                    "vpn": False,
                    "pass": False,
                    "flatpak": False,
                    "drive_cli": True,
                }
            }
        elif relative_path == "tasks/docker_sablier.py":
            data = {"docker_sablier": {"enabled": True}}
        elif relative_path == "tasks/samba.py":
            data = {"samba": {"enabled": True, "allowed_networks": ["192.168.1.0/24"]}}
        elif relative_path == "tasks/hosts.py":
            data = {"hostnames": {"127.0.0.1": ["localhost"]}}
        elif relative_path == "tasks/ssh_keys.py":
            data = {
                "username": "tester",
                "usergroup": "tester",
                "ssh_authorized_keys": {
                    "tester": ["ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestFixture ci"]
                },
            }
        elif relative_path == "tasks/sudo.py":
            data = {"sudoers_rules": ["tester ALL=(ALL) NOPASSWD: /usr/bin/true"]}
        elif relative_path == "tasks/vscodium.py":
            data = {
                "username": "tester",
                "vscodium": {"extensions": ["Vendor.Extension"]},
            }
        elif relative_path.startswith("tasks/workstation/"):
            feature = Path(relative_path).stem
            config = {"enabled": True}
            if feature == "peripherals":
                config["printing"] = True
            data = {"workstation": {feature: config}}
        pyinfra_task_harness.load(module_path, data)

    assert (
        len(pyinfra_task_harness.calls) > calls_before
        or len(pyinfra_task_harness.included) > includes_before
    ), f"{relative_path} scheduled no deployment operation or child task"
