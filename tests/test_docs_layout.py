"""Regression tests for the shared documentation page layout."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

INTRO_PAGES = (
    "architecture.md",
    "configuration.md",
    "deployment.md",
    "development.md",
    "secrets.md",
    "system.md",
    "samba.md",
    "templates.md",
)


def test_technical_pages_have_consistent_introductions():
    """Every technical guide starts with a concise, structured introduction."""
    for page in INTRO_PAGES:
        content = (DOCS / page).read_text()
        assert '<div class="page-intro" markdown>' in content, page
        assert '<div class="page-intro-grid">' in content, page
        assert content.count("page-intro-item") >= 3, page


def test_shared_page_intro_styles_are_responsive():
    """The shared intro component has desktop and mobile layouts."""
    stylesheet = (DOCS / "stylesheets" / "extra.css").read_text()
    assert ".page-intro {" in stylesheet
    assert ".page-intro-grid {" in stylesheet
    assert "@media (max-width: 760px)" in stylesheet
    assert "@media (max-width: 480px)" in stylesheet
