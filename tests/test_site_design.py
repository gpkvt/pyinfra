"""Regression tests for the product-style documentation website."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MKDOCS = ROOT / "mkdocs.yml"
HOMEPAGE = ROOT / "docs" / "index.md"
STYLESHEET = ROOT / "docs" / "stylesheets" / "extra.css"


def test_mkdocs_uses_product_style_navigation_and_typography():
    """The published documentation uses the shared product navigation."""
    config = MKDOCS.read_text(encoding="utf-8")

    assert "navigation.tabs" in config
    assert "navigation.tabs.sticky" in config
    assert "navigation.footer" in config
    assert "text: Manrope" in config
    assert "code: DM Mono" in config
    assert "stylesheets/extra.css" in config
    assert "Upstream pyinfra: upstream.md" in config
    assert "Docker: docker.md" in config


def test_homepage_contains_concise_project_sections():
    """The homepage explains the repository, Docker focus and upstream engine."""
    homepage = HOMEPAGE.read_text(encoding="utf-8")

    for section in (
        "A PRACTICAL PYINFRA DEPLOYMENT",
        "What this repository is",
        "Docker, without hidden storage",
        "How it fits together",
        "The engine: upstream pyinfra",
        "Find your way",
    ):
        assert section in homepage


def test_stylesheet_supports_responsive_and_accessible_navigation():
    """Navigation and landing components remain usable on smaller screens."""
    stylesheet = STYLESHEET.read_text(encoding="utf-8")

    assert ".md-tabs__link--active" in stylesheet
    assert ".md-typeset .landing a:focus-visible" in stylesheet
    assert ".site-hero" in stylesheet
    assert ".site-cards" in stylesheet
    assert "@media (max-width: 760px)" in stylesheet
    assert "@media (prefers-reduced-motion: reduce)" in stylesheet
