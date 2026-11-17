"""Regression tests for the GitHub Pages publishing workflow."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


def test_pages_workflow_builds_html_and_publishes_to_gh_pages():
    """MkDocs output is built strictly and deployed from the generated site."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "run: mkdocs build --strict" in workflow
    assert "uses: actions/upload-artifact@v6" in workflow
    assert "name: documentation-site" in workflow
    assert "uses: peaceiris/actions-gh-pages@v4" in workflow
    assert "publish_branch: gh-pages" in workflow
    assert "publish_dir: ./site" in workflow
    assert "github_token: ${{ secrets.GITHUB_TOKEN }}" in workflow


def test_pages_workflow_does_not_publish_pull_request_builds():
    """Pull requests validate the site without changing the published branch."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "if: github.event_name != 'pull_request'" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "    permissions:\n      contents: write" in workflow
    assert "    needs: build" in workflow
    assert "workflow_dispatch:" in workflow


def test_homepage_section_headings_are_markdown_inside_html():
    """Homepage section headings are parsed by md_in_html, not emitted as text."""
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    homepage = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")

    assert "  - md_in_html" in config
    headings = (
        "Everything you need to manage your Linux environment.",
        "A workflow you can reason about.",
        "Go deeper.",
    )
    assert homepage.count('<div class="section-head" markdown>') == len(headings)
    for heading in headings:
        assert f"## {heading}" in homepage
        assert f"<h2>{heading}</h2>" not in homepage
