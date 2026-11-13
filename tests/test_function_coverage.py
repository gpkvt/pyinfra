"""Enforce a reviewed behavioral-test mapping for every task function."""

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "tests" / "function_coverage.json"


def _qualified_functions(tree):
    discovered = set()

    def visit(node, parents=()):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = ".".join((*parents, child.name))
                discovered.add(qualified)
                visit(child, (*parents, child.name))
            elif isinstance(child, ast.ClassDef):
                visit(child, (*parents, child.name))
            else:
                visit(child, parents)

    visit(tree)
    return discovered


def test_every_task_and_python_utility_function_has_behavioral_test_mapping():
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    discovered = set()

    for directory in ("tasks", "files/scripts"):
        for path in (ROOT / directory).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            relative = path.relative_to(ROOT).as_posix()
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            discovered.update(
                f"{relative}:{name}" for name in _qualified_functions(tree)
            )

    missing = discovered - coverage.keys()
    stale = coverage.keys() - discovered
    assert not missing, f"Functions without behavioral test mappings: {sorted(missing)}"
    assert not stale, f"Stale function coverage mappings: {sorted(stale)}"


def test_function_coverage_mappings_reference_asserting_pytest_cases():
    coverage = json.loads(COVERAGE.read_text(encoding="utf-8"))
    tests = {}

    for path in (ROOT / "tests").glob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                tests.setdefault(node.name, []).append(node)

    referenced = {
        test_name
        for test_names in coverage.values()
        for test_name in test_names
    }
    missing = referenced - tests.keys()
    assert not missing, f"Mapped pytest tests do not exist: {sorted(missing)}"

    without_assertions = [
        name for name in sorted(referenced)
        if not any(
            isinstance(node, ast.Assert)
            for test in tests[name]
            for node in ast.walk(test)
        )
    ]
    assert not without_assertions, (
        "Behavioral test mappings must reference tests with assertions: "
        f"{without_assertions}"
    )
