"""Regression tests for manually dispatching the CI workflow."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_can_be_started_manually():
    """Keep push and pull request triggers while allowing manual runs."""
    workflow = (ROOT / ".github/workflows/idempotency.yml").read_text()

    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
