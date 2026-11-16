"""Regression tests for pinned runtime dependencies."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cyclopts_pin_matches_pyinfra_dependency_range():
    """Keep cyclopts on the supported 4.x line required by pyinfra."""
    requirements = (ROOT / "requirements.txt").read_text().splitlines()

    cyclopts = next(
        requirement for requirement in requirements
        if requirement.startswith("cyclopts==")
    )

    assert cyclopts == "cyclopts==4.25.3"


def test_python_dateutil_pin_matches_pyinfra_dependency_range():
    """Keep python-dateutil below 3 as required by pyinfra."""
    requirements = (ROOT / "requirements.txt").read_text().splitlines()

    dateutil = next(
        requirement for requirement in requirements
        if requirement.startswith("python-dateutil==")
    )

    assert dateutil == "python-dateutil==2.9.0.post0"
