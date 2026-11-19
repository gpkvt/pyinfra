"""Regression tests for safe CI workflows and documentation coverage."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
FEATURE_REFERENCE = ROOT / "docs" / "feature-reference.md"
MKDOCS = ROOT / "mkdocs.yml"
DEPLOY = ROOT / "deploy.py"


CHECK_COMMANDS = {
    "pytest.yml": "uv run pytest tests/ -v",
    "pre-commit.yml": "pre-commit run --all-files",
    "docs.yml": "mkdocs build --strict",
}


def test_actions_workflows_run_validation_on_prs_and_main():
    """Checks run on PRs and main without deploying or publishing."""
    found = {path.name for path in WORKFLOWS.glob("*.yml")}
    found.update(path.name for path in WORKFLOWS.glob("*.yaml"))
    assert found == set(CHECK_COMMANDS) | {"publish-pages.yml"}

    for filename, command in CHECK_COMMANDS.items():
        workflow = (WORKFLOWS / filename).read_text(encoding="utf-8")
        assert "'on':" in workflow
        assert "  push:\n    branches:\n      - main" in workflow
        assert "  pull_request:" in workflow
        assert "  workflow_dispatch:" in workflow
        assert "permissions:\n  contents: read" in workflow
        assert "uses: actions/checkout@v7" in workflow
        assert "uses: actions/setup-python@v7" in workflow
        assert "python-version: '3.12'" in workflow
        assert command in workflow
        assert "peaceiris/actions-gh-pages" not in workflow
        assert "pyinfra inventory.py deploy.py" not in workflow


def test_pages_publication_is_manual_and_builds_main_before_publishing():
    """Publication requires explicit dispatch and a main-branch checkout."""
    workflow = (WORKFLOWS / "publish-pages.yml").read_text(encoding="utf-8")
    assert "'on':\n  workflow_dispatch:" in workflow
    assert "  push:" not in workflow
    assert "  pull_request:" not in workflow
    assert "    permissions:\n      contents: write" in workflow
    assert "  contents: read" in workflow
    assert "ref: main" in workflow
    assert "group: pages-publish" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "run: mkdocs build --strict" in workflow
    assert "uses: peaceiris/actions-gh-pages@v4" in workflow
    assert "publish_branch: gh-pages" in workflow
    assert "publish_dir: ./site" in workflow


def test_readme_badges_link_to_main_branch_check_results():
    """Every validation workflow has a live GitHub Actions status badge."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for filename in CHECK_COMMANDS:
        url = f"https://github.com/gpkvt/pyinfra/actions/workflows/{filename}"
        assert f"{url}/badge.svg?branch=main" in readme
        assert f"]({url})" in readme


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
