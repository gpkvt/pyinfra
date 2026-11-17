"""Regression tests for dependency manifest consistency."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_python_dependency_versions_are_consistent_and_pyinfra_compatible():
    """All dependency manifests pin versions supported by pyinfra."""
    manifests = {
        "pyproject.toml": ROOT / "pyproject.toml",
        "requirements.txt": ROOT / "requirements.txt",
        "requirements-dev.txt": ROOT / "requirements-dev.txt",
    }
    expected = {
        "cyclopts": "4.25.3",
        "python-dateutil": "2.9.0.post0",
    }

    for name, path in manifests.items():
        content = path.read_text(encoding="utf-8")
        for package, version in expected.items():
            assert f"{package}=={version}" in content, (
                f"{name} must pin {package}=={version}"
            )


def test_cosmic_ci_checks_formatting_lints_and_all_targets():
    """The main CI workflow catches Rust formatting and lint regressions."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    normalized = " ".join(workflow.split())

    assert "components: rustfmt, clippy" in workflow
    assert "cargo fmt --manifest-path apps/pyinfra-manager/Cargo.toml --all -- --check" in normalized
    assert "cargo clippy --manifest-path apps/pyinfra-manager/Cargo.toml --all-targets -- -D warnings" in normalized
    assert "cargo check --manifest-path apps/pyinfra-manager/Cargo.toml --all-targets" in normalized


def test_idempotency_workflow_checks_smoke_container_after_second_run():
    """The smoke service must survive both deployment passes."""
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "Run deployment again and check for changes" in workflow
    assert "Verify Docker smoke container remains running" in workflow
    assert "Deployment is idempotent: second run made no changes." in workflow


def test_desktop_build_has_bounded_execution_time():
    """The dedicated desktop release build cannot hang indefinitely."""
    workflow = DESKTOP_WORKFLOW.read_text(encoding="utf-8")

    assert "timeout-minutes: 60" in workflow
    assert "cargo fmt" in workflow
    assert "cargo clippy" in workflow
    assert "cargo build" in workflow
