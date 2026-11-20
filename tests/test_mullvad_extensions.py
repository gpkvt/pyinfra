"""Behavioral tests for Mullvad Browser extension reconciliation."""

import hashlib
import subprocess

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
    assert "retrying on the next deployment' >&2; false; fi" in command
    assert download["_ignore_errors"] is True
    assert download["_sudo"] is True
    assert "/opt/mullvad/extensions/example@example.invalid.xpi.source-sha256" in command
    assert hashlib.sha256(url.encode("utf-8")).hexdigest() in command
    assert preferences["dest"] == "/opt/mullvad/user.js"


def test_mullvad_extension_skips_download_when_source_is_unchanged(
    pyinfra_task_harness,
):
    """One privileged fact identifies an already-current XPI."""
    url = "https://addons.example.invalid/example.xpi"
    source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
    queries = []

    def get_fact(fact, command="", **kwargs):
        queries.append((fact.__name__, command, kwargs))
        if fact.__name__ == "Command":
            return "example@example.invalid"
        return None

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad",
        "mullvad_extensions": {
            "Example": {"id": "example@example.invalid", "url": url},
        },
    })

    assert len(queries) == 1
    assert queries[0][0] == "Command"
    assert queries[0][2] == {"_sudo": True}
    assert "test -s /opt/mullvad/extensions/example@example.invalid.xpi" in queries[0][1]
    assert source_hash in queries[0][1]
    assert not any(
        namespace == "server" and name == "shell"
        and kwargs.get("name") == "Download Example"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_mullvad_checks_multiple_extensions_with_one_remote_fact(
    pyinfra_task_harness,
):
    """Unchanged XPIs skip downloads while missing ones are still installed."""
    urls = {
        "First": "https://addons.example.invalid/first.xpi",
        "Second": "https://addons.example.invalid/second.xpi",
        "Third": "https://addons.example.invalid/third.xpi",
    }
    queries = []

    def get_fact(fact, command="", **kwargs):
        queries.append((fact.__name__, command, kwargs))
        return "first@example.invalid\nthird@example.invalid"

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad",
        "mullvad_extensions": {
            name: {"id": f"{name.lower()}@example.invalid", "url": url}
            for name, url in urls.items()
        },
    })

    assert len(queries) == 1
    assert queries[0][2] == {"_sudo": True}
    for url in urls.values():
        assert hashlib.sha256(url.encode("utf-8")).hexdigest() in queries[0][1]
    downloads = [
        kwargs["name"] for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name", "").startswith("Download ")
    ]
    assert downloads == ["Download Second"]


def test_mullvad_batch_query_executes_against_real_local_files(
    pyinfra_task_harness, tmp_path,
):
    """The generated shell command recognizes current and stale XPIs."""
    profile = tmp_path / "profile"
    extension_dir = profile / "extensions"
    extension_dir.mkdir(parents=True)
    current_url = "https://addons.example.invalid/current.xpi"
    stale_url = "https://addons.example.invalid/stale.xpi"
    current_xpi = extension_dir / "current@example.invalid.xpi"
    current_xpi.write_bytes(b"valid xpi contents")
    (extension_dir / "current@example.invalid.xpi.source-sha256").write_text(
        hashlib.sha256(current_url.encode("utf-8")).hexdigest() + "\n",
        encoding="utf-8",
    )
    stale_xpi = extension_dir / "stale@example.invalid.xpi"
    stale_xpi.write_bytes(b"old xpi contents")
    (extension_dir / "stale@example.invalid.xpi.source-sha256").write_text(
        "outdated hash\n", encoding="utf-8"
    )

    calls = []

    def get_fact(fact, command="", **kwargs):
        assert fact.__name__ == "Command"
        assert kwargs == {"_sudo": True}
        calls.append(command)
        return subprocess.run(
            ["sh", "-c", command], check=True, capture_output=True, text=True,
        ).stdout

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": str(profile),
        "mullvad_extensions": {
            "Current": {"id": "current@example.invalid", "url": current_url},
            "Stale": {"id": "stale@example.invalid", "url": stale_url},
        },
    })
    assert len(calls) == 1
    downloads = [
        kwargs["name"] for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name", "").startswith("Download ")
    ]
    assert downloads == ["Download Stale"]


def test_mullvad_skips_remote_check_without_extensions(pyinfra_task_harness):
    """Do not query the host when no Mullvad XPIs are configured."""
    queries = []
    pyinfra_task_harness.host.get_fact = lambda *_args, **_kwargs: queries.append(True)
    pyinfra_task_harness.load("mullvad_extensions.py", {"mullvad_extensions": {}})
    assert not queries


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


def test_mullvad_rejects_duplicate_extension_ids(pyinfra_task_harness):
    """Two configured extensions cannot overwrite the same XPI/marker."""
    with pytest.raises(ValueError, match="Duplicate Mullvad extension ID"):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_extensions": {
                "First": {
                    "id": "shared@example.invalid",
                    "url": "https://addons.example.invalid/first.xpi",
                },
                "Second": {
                    "id": "shared@example.invalid",
                    "url": "https://addons.example.invalid/second.xpi",
                },
            },
        })


def test_mullvad_extensions_rejects_non_dictionary_configuration(
    pyinfra_task_harness,
):
    with pytest.raises(ValueError, match="must be a dictionary"):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_extensions": ["not-a-dictionary"],
        })
