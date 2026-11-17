"""Regression tests for the manually dispatched desktop build."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-desktop-app.yml"


def test_desktop_build_is_manual_only():
    """Desktop builds run only when explicitly dispatched."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "'on':\n  workflow_dispatch:" in workflow
    assert "  push:" not in workflow
    assert "  pull_request:" not in workflow


def test_desktop_build_checks_and_packages_the_linux_application():
    """The workflow validates Rust sources and uploads the release bundle."""
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "runs-on: ubuntu-24.04" in workflow
    assert "cargo fmt" in workflow
    assert "cargo clippy" in workflow
    assert "cargo build" in workflow
    assert "apps/pyinfra-manager/target/release/pyinfra-manager" in workflow
    assert "org.pyinfra.Manager.desktop" in workflow
    assert "org.pyinfra.Manager.metainfo.xml" in workflow
    assert "uses: actions/upload-artifact@v6" in workflow
    assert "name: pyinfra-manager-linux-x86_64" in workflow
    assert "retention-days: 14" in workflow
