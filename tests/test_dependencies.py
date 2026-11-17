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
