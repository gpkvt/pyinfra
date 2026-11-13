"""Keep CI coverage inventory synchronized with every task and utility."""

import ast
import json
import shutil
import subprocess
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
        if kind not in {"deployment", "helper", "utility"}
    }

    assert not invalid, f"Unsupported CI coverage kinds: {invalid}"
    assert coverage.get("tasks/homepage_config.py") == "helper"
    assert all(
        kind == "deployment"
        for path, kind in coverage.items()
        if path.startswith("tasks/") and path != "tasks/homepage_config.py"
    )
    assert all(
        kind == "utility"
        for path, kind in coverage.items()
        if path.startswith("files/scripts/")
    )


def test_deployment_modules_import_pyinfra():
    coverage = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for relative_path, kind in coverage.items():
        if kind != "deployment":
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
