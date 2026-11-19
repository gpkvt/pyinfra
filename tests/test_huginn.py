"""Huginn deployment, security and idempotency regression tests."""

import builtins
import json
import sys
import types

import pytest

from conftest import ROOT


SECRETS = {
    "postgres_password": "a" * 32,
    "app_secret_token": "b" * 64,
    "seed_password": "c" * 32,
    "invitation_code": "d" * 32,
}


def load_huginn(pyinfra_task_harness, monkeypatch, config=None, secrets=None):
    """Load the task with a stub for the shared Compose helper."""
    calls = []
    docker_module = types.ModuleType("tasks.docker")
    docker_module.ensure_numeric_directory = (
        lambda *args: calls.append(("directory", args))
    )
    docker_module.deploy_docker_service = (
        lambda **kwargs: calls.append(("deploy", kwargs))
    )
    monkeypatch.setitem(sys.modules, "tasks.docker", docker_module)
    monkeypatch.setattr(
        builtins, "secrets",
        {"docker": {"huginn": SECRETS if secrets is None else secrets}},
        raising=False,
    )
    pyinfra_task_harness.load("docker/huginn.py", {
        "username": "tester",
        "usergroup": "tester",
        "homedir": "/home/tester",
        "docker": {
            "huginn": (
                {"domain": "huginn.example.com"}
                if config is None else config
            ),
        },
    })
    return calls


def test_huginn_provisions_host_storage_and_private_env(pyinfra_task_harness, monkeypatch):
    """Secrets stay in a protected .env; the database uses a host bind mount."""
    calls = load_huginn(pyinfra_task_harness, monkeypatch)
    assert calls[0] == (
        "directory", ("/home/tester/.docker/huginn/postgres", 70, 70, "700")
    )
    options = calls[1][1]
    assert options["service"] == "huginn"
    assert options["compose_services"] == ["db", "web", "threaded"]
    assert options["app_services"] == ["web", "threaded"]
    assert options["port"] == 8028
    assert options["domain"] == "huginn.example.com"
    assert options["enable_smokescreen"] == "true"
    assert options["private_env"] == {
        "HUGINN_POSTGRES_PASSWORD": SECRETS["postgres_password"],
        "HUGINN_APP_SECRET_TOKEN": SECRETS["app_secret_token"],
        "HUGINN_SEED_PASSWORD": SECRETS["seed_password"],
        "HUGINN_INVITATION_CODE": SECRETS["invitation_code"],
    }


def test_huginn_allows_explicit_overrides(pyinfra_task_harness, monkeypatch):
    """The host port and security options are explicitly configurable."""
    calls = load_huginn(pyinfra_task_harness, monkeypatch, {
        "domain": "automation.example.com",
        "port": 8123,
        "seed_username": "huginn_admin",
        "image": "ghcr.io/huginn/huginn-single-process:pinned",
        "postgres_image": "postgres:16-alpine",
        "enable_smokescreen": False,
    })
    options = calls[1][1]
    assert options["port"] == 8123
    assert options["seed_username"] == "huginn_admin"
    assert options["enable_smokescreen"] == "false"
    assert options["image"].endswith(":pinned")


@pytest.mark.parametrize("config, error", [
    ({}, "docker.huginn.domain"),
    ({"domain": "https://huginn.example.com"}, "docker.huginn.domain"),
    ({"domain": "huginn.example.com", "port": True}, "docker.huginn.port"),
    ({"domain": "huginn.example.com", "port": 65536}, "docker.huginn.port"),
    ({"domain": "huginn.example.com", "seed_username": "bad name"}, "seed_username"),
    ({"domain": "huginn.example.com", "enable_smokescreen": "true"}, "enable_smokescreen"),
])
def test_huginn_rejects_invalid_host_data(
    pyinfra_task_harness, monkeypatch, config, error,
):
    """Refuse invalid options before any deployment is scheduled."""
    with pytest.raises(ValueError, match=error):
        load_huginn(pyinfra_task_harness, monkeypatch, config=config)


@pytest.mark.parametrize("missing", SECRETS)
def test_huginn_requires_each_secret(pyinfra_task_harness, monkeypatch, missing):
    """Refuse partially configured encrypted secrets."""
    values = {name: value for name, value in SECRETS.items() if name != missing}
    with pytest.raises(ValueError, match=missing):
        load_huginn(pyinfra_task_harness, monkeypatch, secrets=values)


def test_huginn_rejects_unsafe_secret(pyinfra_task_harness, monkeypatch):
    """Prevent accidental multi-line credentials and malformed .env values."""
    values = {**SECRETS, "postgres_password": "bad\nvalue"}
    with pytest.raises(ValueError, match="postgres_password"):
        load_huginn(pyinfra_task_harness, monkeypatch, secrets=values)


def test_huginn_compose_keeps_credentials_out_of_templates():
    """Use placeholders and host bind mounts, never literal secrets."""
    template = (
        ROOT / "templates/docker/huginn/docker-compose.yml.j2"
    ).read_text(encoding="utf-8")
    assert '"127.0.0.1:{{ port }}:3000"' in template
    assert "{{ homedir }}/.docker/huginn/postgres:/var/lib/postgresql/data" in template
    assert "condition: service_healthy" in template
    assert "command: /scripts/init bin/threaded.rb" in template
    assert "ENABLE_SMOKESCREEN: \"{{ enable_smokescreen }}\"" in template
    for name in (
        "HUGINN_POSTGRES_PASSWORD",
        "HUGINN_APP_SECRET_TOKEN",
        "HUGINN_SEED_PASSWORD",
        "HUGINN_INVITATION_CODE",
    ):
        assert "${" + name + ":?}" in template
    for value in SECRETS.values():
        assert value not in template


def test_huginn_secrets_example_has_required_placeholders():
    """The encrypted secrets schema documents every required value."""
    sample = json.loads((ROOT / "secrets.json.gpg.example").read_text())
    values = sample["hosts"]["@local"]["docker"]["huginn"]
    assert set(values) == set(SECRETS)
    assert all(value.startswith("REPLACE_") for value in values.values())
