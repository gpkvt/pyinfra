"""Regression tests for the prominent task documentation hub."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_task_hub_highlights_all_major_task_categories():
    """The task landing page links directly to each task-reference section."""
    page = (ROOT / "docs" / "tasks-overview.md").read_text(encoding="utf-8")

    assert "Core system tasks" in page
    assert "Optional features" in page
    assert "Desktop &amp; hardware" in page
    assert "Docker services" in page
    assert "task-reference/#core-tasks" in page
    assert "task-reference/#optional-tasks" in page
    assert "task-reference/#workstation-role-tasks" in page
    assert "task-reference/#docker-services" in page


def test_task_hub_styles_are_registered():
    """The responsive task hub stylesheet is loaded by MkDocs."""
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "stylesheets/task-hub.css" in config
