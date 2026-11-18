"""Regression tests for the technical project website and its key distinctions."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "docs" / "index.md"
UPSTREAM = ROOT / "docs" / "upstream.md"
TASKS = ROOT / "docs" / "tasks-overview.md"
DOCKER = ROOT / "docs" / "docker.md"
MKDOCS = ROOT / "mkdocs.yml"


def test_homepage_explains_repository_scope_and_execution():
    homepage = HOMEPAGE.read_text(encoding="utf-8")

    for phrase in (
        "deployment configuration for Debian and Ubuntu systems",
        "upstream pyinfra automation tool",
        "## Repository contents",
        "## Requirements",
        "## Deployment",
        "pyinfra inventory.py deploy.py --dry --diff",
        "Docker-managed named volumes are not used",
    ):
        assert phrase in homepage


def test_upstream_page_distinguishes_engine_from_deployment_repository():
    upstream = UPSTREAM.read_text(encoding="utf-8")

    assert "pyinfra-dev/pyinfra" in upstream
    assert "This repository, `gpkvt/pyinfra`" in upstream
    assert "Inventory" in upstream
    assert "Operations" in upstream
    assert "Connectors" in upstream


def test_task_overview_covers_all_major_task_families():
    tasks = TASKS.read_text(encoding="utf-8")

    for phrase in (
        "System foundations",
        "Docker applications",
        "Network and services",
        "Workstation",
        "Sablier on-demand startup",
    ):
        assert phrase in tasks


def test_docker_guide_keeps_storage_and_lifecycle_guarantees_visible():
    docker = DOCKER.read_text(encoding="utf-8")

    for phrase in (
        "~/.docker/",
        "Host bind mounts only",
        "systemd",
        "Docker-managed named volumes are not used",
    ):
        assert phrase in docker


def test_navigation_includes_project_references():
    navigation = MKDOCS.read_text(encoding="utf-8")

    for entry in (
        "Overview: index.md",
        "Tasks: tasks-overview.md",
        "Docker: docker.md",
        "Configuration: configuration.md",
        "Upstream pyinfra: upstream.md",
        "Changelog: changelog.md",
    ):
        assert entry in navigation
