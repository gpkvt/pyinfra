"""Regression tests for GitHub Pages publishing."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


def test_pages_workflow_publishes_on_every_main_push_and_manually():
    """Every main update and explicit dispatch rebuild the published site."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "'on':\n  push:\n    branches:\n      - main\n  workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "run: mkdocs build --strict" in workflow
    assert "uses: peaceiris/actions-gh-pages@v4" in workflow
    assert "publish_branch: gh-pages" in workflow
    assert "publish_dir: ./site" in workflow
    assert "force_orphan: true" in workflow


def test_pages_workflow_serializes_publications_without_cancelling_them():
    """A newer main push must not cancel an active site publication."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "group: pages-publish" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "    permissions:\n      contents: write" in workflow
    assert "git push origin --delete gh-pages" not in workflow
