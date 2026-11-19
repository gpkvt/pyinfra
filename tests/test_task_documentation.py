"""Regression tests for the technical task overview."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_task_overview_links_to_every_major_category():
    """The overview routes readers to the task, Docker and workstation references."""
    page = (ROOT / "docs" / "tasks-overview.md").read_text(encoding="utf-8")

    for category in (
        "System foundations",
        "Docker applications",
        "Network and services",
        "Workstation",
    ):
        assert f"| {category} |" in page

    for target in (
        "[Core task reference](tasks/#core-tasks)",
        "[Optional task reference](tasks/#optional-tasks)",
        "[Docker guide](docker/)",
        "[Workstation features](feature-reference/#workstation-role-features)",
    ):
        assert target in page


def test_task_overview_uses_shared_documentation_styles():
    """The site includes the shared styling used by documentation pages."""
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    stylesheet = (
        ROOT / "docs" / "stylesheets" / "extra.css"
    ).read_text(encoding="utf-8")

    assert "stylesheets/extra.css" in config
    assert ".page-intro {" in stylesheet
