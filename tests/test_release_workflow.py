"""Regression tests for GitHub release automation."""

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/publish-release.sh"


def test_release_workflow_checks_out_repository_before_publishing():
    """Release notes generation has a local Git repository and complete history."""
    workflow = (ROOT / ".github/workflows/release.yml").read_text()

    checkout = workflow.index("uses: actions/checkout@v4")
    validation = workflow.index("Validate version tag")
    release = workflow.index("Create GitHub release")

    assert checkout < validation < release
    assert "fetch-depth: 0" in workflow


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


def test_release_helper_is_executable_and_has_valid_bash_syntax():
    """The documented helper is executable and parses before anyone runs it."""
    assert SCRIPT.stat().st_mode & 0o111
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_release_helper_checks_release_preconditions_and_remote_tag():
    """Refuse unsafe release states before creating an immutable tag."""
    script = SCRIPT.read_text()

    assert 'git branch --show-current' in script
    assert 'git status --porcelain' in script
    assert 'grep -Eq' in script
    assert 'git fetch origin main --tags' in script
    assert 'git rev-parse HEAD' in script
    assert 'git rev-parse origin/main' in script
    assert 'git show-ref --verify --quiet' in script
    assert 'git ls-remote --tags origin' in script
    assert 'unable to check whether the release tag exists remotely' in script
    assert 'Create and push this release tag?' in script
    assert 'git tag -a' in script
    assert 'git push origin' in script
    assert 'the local tag was retained' in script


def test_release_documentation_uses_the_helper_and_describes_workflow():
    """Document the guarded tag-push process rather than manual tag commands."""
    docs = (ROOT / "docs/releasing.md").read_text()

    assert './scripts/publish-release.sh v1.2.3' in docs
    assert 'local `main` exactly matches the fetched `origin/main`' in docs
    assert 'does not' in docs
    assert 'Merging a pull request does not' in docs
