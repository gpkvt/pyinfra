"""Regression tests for the technical documentation website."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MKDOCS = ROOT / "mkdocs.yml"
HOMEPAGE = ROOT / "docs" / "index.md"
STYLESHEET = ROOT / "docs" / "stylesheets" / "extra.css"


def test_mkdocs_uses_documentation_navigation_and_system_theme():
    """The site uses standard documentation navigation and light/dark schemes."""
    config = MKDOCS.read_text(encoding="utf-8")

    assert "navigation.tabs" in config
    assert "navigation.footer" in config
    assert 'scheme: default' in config
    assert 'scheme: slate' in config
    assert "Overview: index.md" in config
    assert "Docker: docker.md" in config
    assert "Configuration: configuration.md" in config
    assert "Upstream pyinfra: upstream.md" in config
    assert "Manrope" not in config
    assert "DM Mono" not in config


def test_homepage_is_a_technical_repository_overview():
    """The homepage documents scope, requirements, execution and storage."""
    homepage = HOMEPAGE.read_text(encoding="utf-8")

    for section in (
        "# gpkvt/pyinfra",
        "## Repository contents",
        "## Requirements",
        "## Deployment",
        "## Docker storage and lifecycle",
        "## Upstream pyinfra",
        "## Reference",
    ):
        assert section in homepage

    assert "site-hero" not in homepage
    assert "terminal-window" not in homepage
    assert "Infrastructure, without surprises" not in homepage


def test_stylesheet_contains_documentation_styles_not_landing_page_artwork():
    """Styles focus on docs, tables and technical page introductions."""
    stylesheet = STYLESHEET.read_text(encoding="utf-8")

    assert ".md-content__inner" in stylesheet
    assert ".docker-stats" in stylesheet
    assert ".page-intro {" in stylesheet
    assert ".page-intro-grid {" in stylesheet
    assert ".site-hero" not in stylesheet
    assert ".terminal-window" not in stylesheet
    assert "@media (max-width: 600px)" in stylesheet
