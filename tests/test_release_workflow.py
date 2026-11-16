"""Regression tests for GitHub release automation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_uses_version_tags_and_publishes_github_releases():
    """Only version tags trigger releases, using the least required permission."""
    workflow = (ROOT / ".github/workflows/release.yml").read_text()

    assert "tags:" in workflow
    assert "- 'v*'" in workflow
    assert "workflow_dispatch:" in workflow
    assert "inputs:" in workflow
    assert "tag:" in workflow
    assert "contents: write" in workflow
    assert "gh release create" in workflow
    assert "--verify-tag" in workflow
    assert "--generate-notes" in workflow
    assert "GH_TOKEN: ${{ github.token }}" in workflow
    assert "inputs.tag || github.ref_name" in workflow


def test_release_workflow_rejects_non_semver_tags():
    """Reject tags that merely begin with v but are not version numbers."""
    workflow = (ROOT / ".github/workflows/release.yml").read_text()

    assert "Validate version tag" in workflow
    assert "v[0-9]+" in workflow
    assert "Invalid release tag" in workflow
