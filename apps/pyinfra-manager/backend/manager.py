"""Local, non-networked control plane for the Pyinfra Manager desktop app.

The backend never evaluates host configuration. It parses Python syntax only,
keeps real configuration out of Git, and defaults every deployment to dry-run.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILES = {
    "local": ("group_data/@local.py.example", "group_data/@local.py"),
    "workstation": ("group_data/workstation.py.example", "group_data/workstation.py"),
}
WORKSTATION_TASKS = {
    "backup": "tasks/workstation/backup.py",
    "power": "tasks/workstation/power.py",
    "hardware": "tasks/workstation/hardware.py",
    "storage": "tasks/workstation/storage.py",
    "peripherals": "tasks/workstation/peripherals.py",
    "desktop": "tasks/workstation/desktop.py",
    "maintenance": "tasks/workstation/maintenance.py",
    "limusic": "tasks/workstation/limusic.py",
    "cosmic": "tasks/workstation/cosmic/deploy.py",
}


class ManagerError(Exception):
    """An expected, user-displayable manager error."""


def _safe_config_path(key: str) -> Path:
    if key not in CONFIG_FILES:
        raise ManagerError(f"Unknown configuration file: {key}")
    _, relative = CONFIG_FILES[key]
    path = ROOT / relative
    if path.is_symlink():
        raise ManagerError(f"Refusing to follow symlink: {relative}")
    if path.parent.resolve() != (ROOT / "group_data").resolve():
        raise ManagerError("Configuration path escaped group_data")
    return path


def ensure_config_files() -> dict[str, str]:
    """Create ignored local files from tracked examples, without overwriting."""
    result = {}
    for key, (example, _) in CONFIG_FILES.items():
        target = _safe_config_path(key)
        if not target.exists():
            source = ROOT / example
            if not source.is_file():
                raise ManagerError(f"Missing example configuration: {example}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o600)
        result[key] = str(target)
    return result


def read_config(key: str) -> str:
    path = _safe_config_path(key)
    if not path.is_file():
        raise ManagerError(
            f"{path.name} does not exist. Initialize local configuration first."
        )
    return path.read_text(encoding="utf-8")


def validate_config(source: str, filename: str = "<configuration>") -> None:
    """Validate Python syntax without importing or executing the file."""
    try:
        ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise ManagerError(
            f"Python syntax error at line {exc.lineno}, column {exc.offset}: {exc.msg}"
        ) from exc


def save_config(key: str, source: str) -> bool:
    """Validate and atomically save an allowlisted local config with a backup."""
    validate_config(source, key)
    path = _safe_config_path(key)
    if not path.is_file():
        raise ManagerError("Initialize local configuration before editing it")
    old = path.read_text(encoding="utf-8")
    if old == source:
        return False

    backup = path.with_suffix(path.suffix + ".bak")
    if backup.exists():
        raise ManagerError(f"Backup already exists; move it before saving: {backup.name}")
    shutil.copy2(path, backup)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(source)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def _literal_includes(tree: ast.AST) -> set[str]:
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "include" or not node.args:
            continue
        value = node.args[0]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            found.add(value.value)
    return found


def discover_tasks() -> list[dict[str, object]]:
    """Discover task modules from deploy.py and the workstation feature map."""
    source = (ROOT / "deploy.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="deploy.py")
    included = _literal_includes(tree)
    included.update(WORKSTATION_TASKS.values())
    tasks = []
    for relative in sorted(included):
        if not relative.startswith("tasks/") or not relative.endswith(".py"):
            continue
        path = ROOT / relative
        if not path.is_file():
            continue
        tasks.append({
            "path": relative,
            "name": path.stem.replace("_", " ").title(),
            "group": "Workstation" if relative.startswith("tasks/workstation/") else (
                "Core" if relative in {
                    "tasks/apt.py", "tasks/hosts.py", "tasks/sudo.py",
                    "tasks/system.py", "tasks/ssh_keys.py", "tasks/git.py",
                    "tasks/fonts.py", "tasks/scripts.py", "tasks/mc.py",
                } else "Optional"
            ),
            "included_by_default": relative in _literal_includes(tree),
            "available": True,
        })
    return tasks


def configured_hosts() -> list[str]:
    """Read inventory host names from its literal _all_hosts dictionary."""
    tree = ast.parse((ROOT / "inventory.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_all_hosts"
            for target in node.targets
        ):
            value = node.value
            if isinstance(value, ast.Dict):
                return [
                    key.value for key in value.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                ]
    raise ManagerError("Could not discover literal _all_hosts in inventory.py")


def run_deployment(host: str, apply: bool = False) -> dict[str, object]:
    """Run the repository deployment for one inventory target."""
    if host not in configured_hosts():
        raise ManagerError(f"Unknown inventory host: {host}")
    command = [
        "uv", "run", "pyinfra", "inventory.py", "deploy.py",
        "--diff", "--limit", host,
    ]
    if not apply:
        command.insert(5, "--dry")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "dry_run": not apply,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Pyinfra Manager local backend")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("catalog")
    sub.add_parser("hosts")
    sub.add_parser("init-config")
    read = sub.add_parser("read-config")
    read.add_argument("key", choices=CONFIG_FILES)
    validate = sub.add_parser("validate-config")
    validate.add_argument("key", choices=CONFIG_FILES)
    validate.add_argument("file", type=Path)
    run = sub.add_parser("run")
    run.add_argument("host")
    run.add_argument("--apply", action="store_true", help="Apply changes; default is dry-run")
    args = parser.parse_args()

    try:
        if args.action == "catalog":
            result = discover_tasks()
        elif args.action == "hosts":
            result = configured_hosts()
        elif args.action == "init-config":
            result = ensure_config_files()
        elif args.action == "read-config":
            result = read_config(args.key)
        elif args.action == "validate-config":
            validate_config(args.file.read_text(encoding="utf-8"), args.key)
            result = {"valid": True}
        else:
            result = run_deployment(args.host, args.apply)
        print(result if isinstance(result, str) else json.dumps(result, indent=2))
        return 0 if not isinstance(result, dict) or result.get("returncode", 0) == 0 else 1
    except (ManagerError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
