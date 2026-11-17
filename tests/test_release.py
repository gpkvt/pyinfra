"""Regression tests for the guarded release helper."""

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/publish-release.sh"


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
    assert "git fetch origin '+refs/heads/main:refs/remotes/origin/main' --tags" in script
    assert 'git merge-base --is-ancestor origin/main HEAD' in script
    assert 'git rev-parse HEAD' in script
    assert 'git rev-parse origin/main' in script
    assert 'git show-ref --verify --quiet' in script
    assert 'git ls-remote --tags origin' in script
    assert 'unable to check whether the release tag exists remotely' in script
    assert 'Create and push this release tag?' in script
    assert 'git tag -a' in script
    assert 'git push origin' in script
    assert 'the local tag was retained' in script.lower()


def test_release_documentation_uses_the_helper_and_manual_publication():
    """Document guarded tag creation and manual GitHub Release publication."""
    docs = (ROOT / "docs/releasing.md").read_text()

    assert './scripts/publish-release.sh v1.2.3' in docs
    assert 'local `main` exactly matches the fetched `origin/main`' in docs
    assert 'Create the GitHub Release manually' in docs
    assert 'Merging a pull request does not' in docs
    assert 'workflow' not in docs.lower()
