"""Behavioral tests for Mullvad Browser extension reconciliation."""

import hashlib

import pytest


def test_mullvad_extension_downloads_when_source_marker_is_missing(
    pyinfra_task_harness,
):
    url = "https://addons.example.invalid/example.xpi"
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad",
        "mullvad_extensions": {
            "Example": {"id": "example@example.invalid", "url": url},
        },
    })

    download = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Download Example"
    )
    marker = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Record Example source URL"
    )
    preferences = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Manage Mullvad Browser preferences"
    )

    command = download["commands"][0]
    assert url in command
    assert "--retry 3 --retry-all-errors" in command
    assert "--connect-timeout 20 --max-time 300" in command
    assert "mv " in command
    assert "keeping the existing extension" in command
    assert "then echo 'Downloaded Example'" in command
    assert "else rm -f" in command
    assert "files" not in command
    assert marker["dest"].endswith(".xpi.source-sha256")
    assert preferences["dest"] == "/opt/mullvad/user.js"


def test_mullvad_extension_skips_download_when_source_is_unchanged(
    pyinfra_task_harness,
):
    url = "https://addons.example.invalid/example.xpi"
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get_fact(fact, _command=None, **_kwargs):
        if fact.__name__ == "Command":
            return source_hash
        if fact.__name__ == "File":
            return True
        return None

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad",
        "mullvad_extensions": {
            "Example": {"id": "example@example.invalid", "url": url},
        },
    })

    assert not any(
        (namespace == "files" and name == "download")
        or (namespace == "server" and name == "shell"
            and kwargs.get("name") == "Download Example")
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )
    assert not any(
        namespace == "files" and name == "put"
        and kwargs.get("name") == "Record Example source URL"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


@pytest.mark.parametrize(
    "extension",
    [
        {"id": "../escape", "url": "https://addons.example.invalid/example.xpi"},
        {"id": "example@example.invalid", "url": "http://addons.example.invalid/example.xpi"},
        {
            "id": "example@example.invalid",
            "url": "https://user:pass@addons.example.invalid/example.xpi",
        },
    ],
)
def test_mullvad_extension_rejects_invalid_id_or_url(
    pyinfra_task_harness, extension,
):
    with pytest.raises(ValueError):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_extensions": {"Example": extension},
        })


def test_mullvad_extensions_rejects_non_dictionary_configuration(
    pyinfra_task_harness,
):
    with pytest.raises(ValueError, match="must be a dictionary"):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_extensions": ["not-a-dictionary"],
        })
