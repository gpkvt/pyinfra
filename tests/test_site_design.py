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


def test_homepage_contains_product_landing_sections():
    """The homepage introduces the toolkit, workflow, install and docs."""
    homepage = HOMEPAGE.read_text(encoding="utf-8")

    for section in (
        "Infrastructure,",
        "THE TOOLKIT",
        "HOW IT WORKS",
        "GET STARTED",
        "DOCUMENTATION",
        "PROJECT HISTORY",
        "Make infrastructure",
    ):
        assert section in homepage


def test_stylesheet_supports_responsive_and_accessible_navigation():
    """Navigation and landing components remain usable on smaller screens."""
    stylesheet = STYLESHEET.read_text(encoding="utf-8")

    assert ".md-tabs__link--active" in stylesheet
    assert ".md-typeset .landing a:focus-visible" in stylesheet
    assert "@media (max-width: 760px)" in stylesheet
    assert "@media (prefers-reduced-motion: reduce)" in stylesheet
