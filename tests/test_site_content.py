"""Regression tests for published documentation content."""

from datetime import datetime
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_section_headings_are_markdown_inside_html():
    """Homepage section headings are parsed by md_in_html, not emitted as text."""
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    assert "  - md_in_html" in config
    headings = (
        "Everything you need to manage your Linux environment.",
        "A workflow you can reason about.",
        "Go deeper.",
        "What's new in pyinfra.",
    )
    assert homepage.count('<div class="section-head" markdown>') == len(headings)
    assert homepage.count('<div class="section-kicker" markdown>') == len(headings)
    for heading in headings:
        assert f"## {heading}" in homepage
        assert f"<h2>{heading}</h2>" not in homepage


def test_changelog_page_matches_repository_changelog():
    """Keep the website changelog synchronized with the repository source."""
    source = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    page = (ROOT / "docs" / "changelog.md").read_text(encoding="utf-8")

    assert page == source.replace("(docs/releasing.md)", "(releasing.md)")
    assert "  - Changelog: changelog.md" in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def test_homepage_highlights_match_latest_changelog_entry():
    """Keep the homepage's dated highlights grounded in the newest changelog entry."""
    source = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    latest = re.search(
        r"^## \[(\d{2}\.\d{2}\.\d{4})\](.*?)(?=^## \[|\Z)",
        source,
        re.MULTILINE | re.DOTALL,
    )
    assert latest is not None

    date = datetime.strptime(latest.group(1), "%d.%m.%Y")
    displayed_date = date.strftime("%d %B %Y").lstrip("0")
    section = re.search(
        r'<section class="changelog-section" markdown>(.*?)</section>',
        homepage,
        re.DOTALL,
    )
    assert section is not None
    assert displayed_date in section.group(1)
    assert 'href="changelog/"' in section.group(1)

    highlights = (
        "Added a native COSMIC desktop manager",
        "Added configurable AdGuard Home web UI port handling",
        "Improved desktop-manager checkout discovery",
        "Fixed deployment initialization",
    )
    for highlight in highlights:
        assert highlight in latest.group(2)
        assert highlight in section.group(1)
