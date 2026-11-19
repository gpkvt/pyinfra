"""Regression tests for repository workflow policy and feature coverage."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FEATURE_REFERENCE = ROOT / "docs" / "feature-reference.md"
MKDOCS = ROOT / "mkdocs.yml"
DEPLOY = ROOT / "deploy.py"


def test_repository_does_not_define_github_actions_workflows():
    """Avoid unintentionally restoring automatic or manual GitHub Actions jobs."""
    assert not list(WORKFLOWS.glob("*.yml"))
    assert not list(WORKFLOWS.glob("*.yaml"))


def test_feature_reference_covers_every_task_python_module():
    """The feature reference indexes every Python module below tasks/."""
    reference = FEATURE_REFERENCE.read_text(encoding="utf-8")
    modules = sorted((ROOT / "tasks").rglob("*.py"))

    missing = [
        path.relative_to(ROOT).as_posix()
        for path in modules
        if path.relative_to(ROOT).as_posix() not in reference
    ]

    assert not missing, f"Undocumented task modules: {missing}"


def test_feature_reference_documents_static_deploy_includes():
    """Every literal task include in deploy.py appears in the feature index."""
    tree = ast.parse(DEPLOY.read_text(encoding="utf-8"))
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
    reference = FEATURE_REFERENCE.read_text(encoding="utf-8")

    missing = sorted(path for path in includes if path not in reference)
    assert not missing, f"Undocumented deploy includes: {missing}"


def test_feature_reference_is_in_mkdocs_navigation():
    """The complete feature index is reachable from the published site."""
    navigation = MKDOCS.read_text(encoding="utf-8")
    assert "Feature reference: feature-reference.md" in navigation
