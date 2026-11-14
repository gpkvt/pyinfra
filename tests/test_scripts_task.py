"""Tests for deploying user scripts and system-wide command links."""

from conftest import ROOT


def test_scripts_are_synced_without_sudo_and_links_use_sudo(pyinfra_task_harness):
    """User-owned scripts stay in home while /usr/local/bin links use privilege."""
    pyinfra_task_harness.load("scripts.py", {
        "username": "tester",
        "usergroup": "users",
    })

    sync = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "sync"
    )
    assert sync["src"] == "files/scripts/"
    assert sync["dest"] == "/home/tester/scripts/"
    assert sync["delete"] is False
    assert sync["user"] == "tester"
    assert sync["group"] == "users"
    assert sync["mode"] == "750"
    assert sync["_sudo"] is False

    expected = {
        str(path.relative_to(ROOT / "files/scripts"))
        for path in (ROOT / "files/scripts").rglob("*")
        if path.is_file()
    }
    links = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "link"
    ]

    assert len(links) == len(expected)
    assert {
        kwargs["target"].removeprefix("/home/tester/scripts/")
        for kwargs in links
    } == expected
    assert all(kwargs["_sudo"] is True for kwargs in links)
    assert all(kwargs["path"].startswith("/usr/local/bin/") for kwargs in links)
