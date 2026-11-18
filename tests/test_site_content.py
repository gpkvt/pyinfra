"""Regression tests for published documentation content."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_uses_plain_markdown_for_technical_content():
    """The homepage has no custom landing-page or dated promotional sections."""
    homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "# gpkvt/pyinfra" in homepage
    assert "## Repository contents" in homepage
    assert "## Deployment" in homepage
    assert '<div class="site-hero"' not in homepage
    assert '<section class="changelog-section"' not in homepage
    assert "Changelog: changelog.md" in config


def test_changelog_page_matches_repository_changelog():
    """Keep the website changelog synchronized with the repository source."""
    source = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    page = (ROOT / "docs" / "changelog.md").read_text(encoding="utf-8")

    assert page == source.replace("(docs/releasing.md)", "(releasing.md)")
    assert "Changelog: changelog.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
