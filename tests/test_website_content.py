"""Regression tests for the concise project website and its key distinctions."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOMEPAGE = ROOT / "docs" / "index.md"
UPSTREAM = ROOT / "docs" / "upstream.md"
TASKS = ROOT / "docs" / "tasks-overview.md"
DOCKER = ROOT / "docs" / "docker.md"
MKDOCS = ROOT / "mkdocs.yml"


def test_homepage_explains_repository_and_highlights_docker():
    homepage = HOMEPAGE.read_text(encoding="utf-8")

    for phrase in (
        "A PRACTICAL PYINFRA DEPLOYMENT",
        "This repository is an opinionated collection",
        "Docker, without hidden storage",
        "Host bind mounts",
        "systemd user services",
        "Upstream pyinfra page",
    ):
        assert phrase in homepage


def test_upstream_page_distinguishes_engine_from_deployment_repository():
    upstream = UPSTREAM.read_text(encoding="utf-8")

    assert "pyinfra-dev/pyinfra" in upstream
    assert "This repository, `gpkvt/pyinfra`" in upstream
    assert "Python deploys" in upstream
    assert "Connectors" in upstream


def test_task_overview_covers_all_major_task_families():
    tasks = TASKS.read_text(encoding="utf-8")

    for phrase in ("System foundations", "Docker applications", "Network &amp; services", "Desktop &amp; hardware"):
        assert phrase in tasks


def test_docker_guide_keeps_storage_and_lifecycle_guarantees_visible():
    docker = DOCKER.read_text(encoding="utf-8")

    for phrase in ("~/.docker/", "Host bind mounts only", "systemd", "Docker-managed named volumes are not used"):
        assert phrase in docker


def test_new_pages_are_in_navigation():
    navigation = MKDOCS.read_text(encoding="utf-8")

    assert "Upstream pyinfra: upstream.md" in navigation
    assert "Tasks: tasks-overview.md" in navigation
