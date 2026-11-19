"""Regression tests for dependency manifest consistency and pyinfra compatibility."""

import re
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version


ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ("pyproject.toml", "requirements.txt", "requirements-dev.txt")
# pyinfra 3.11.1 dependency constraints; review when upgrading pyinfra.
PYINFRA_REQUIREMENTS = {
    "cyclopts": SpecifierSet(">=4,<5"),
    "python-dateutil": SpecifierSet(">2,<3"),
}


def test_python_dependency_versions_are_consistent_and_pyinfra_compatible():
    """All pinned versions agree and satisfy pyinfra 3.11.1 requirements."""
    versions_by_manifest = {}
    for filename in MANIFESTS:
        content = (ROOT / filename).read_text(encoding="utf-8")
        pins = {}
        for package in ("pyinfra", *PYINFRA_REQUIREMENTS):
            matches = re.findall(
                rf"\\b{re.escape(package)}==([0-9][0-9A-Za-z.+-]*)",
                content,
            )
            assert len(matches) == 1, f"{filename}: expected one {package} pin"
            pins[package] = Version(matches[0])
        versions_by_manifest[filename] = pins

    reference = versions_by_manifest["pyproject.toml"]
    assert reference["pyinfra"] == Version("3.11.1")
    for filename, pins in versions_by_manifest.items():
        assert pins == reference, f"{filename}: dependency pins differ"
        for package, supported in PYINFRA_REQUIREMENTS.items():
            assert pins[package] in supported, (
                f"{filename}: {package}=={pins[package]} is incompatible "
                f"with pyinfra=={pins['pyinfra']}"
            )


def test_dependabot_excludes_incompatible_major_dependency_updates():
    """Ignore major updates until pyinfra supports them."""
    config = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    for package in PYINFRA_REQUIREMENTS:
        assert f"- dependency-name: {package}" in config
    assert config.count("- version-update:semver-major") >= len(PYINFRA_REQUIREMENTS)
