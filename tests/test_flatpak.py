"""Focused tests for Flatpak remote selection and deployment behavior."""

import pytest


@pytest.mark.parametrize(
    ("refs", "expected"),
    [
        (
            [
                "app.org.example.App/x86_64/stable",
                "runtime.org.example.Codecs/x86_64/stable",
            ],
            ["app.org.example.App", "runtime.org.example.Codecs"],
        ),
        (
            [
                "app/org.example.App/x86_64/stable",
                "runtime/org.example.Codecs/x86_64/stable",
            ],
            ["org.example.App", "org.example.Codecs"],
        ),
        (
            ["org.example.App", "org.example.Codecs"],
            ["org.example.App", "org.example.Codecs"],
        ),
    ],
)
def testflatpak_ref_ids_normalizes_application_and_runtime_refs(
    pyinfra_task_harness, refs, expected
):
    """Both app and runtime refs resolve to their configured Flatpak IDs."""
    module = pyinfra_task_harness.load("flatpak.py")
    assert module.flatpak_ref_ids(refs) == expected


@pytest.mark.parametrize(
    ("package", "available", "expected"),
    [
        ("app.one", {"flathub": {"app.one"}, "other": {"app.one"}}, "flathub"),
        ("app.one", {"other": {"app.one"}}, "other"),
    ],
)
def test_flatpak_remote_selection_prefers_flathub_or_sole_match(
    pyinfra_task_harness, package, available, expected
):
    """Flathub wins duplicate refs; a sole alternative remote remains usable."""
    module = pyinfra_task_harness.load("flatpak.py")
    assert module.select_flatpak_remote(package, available) == expected


def test_flatpak_remote_selection_rejects_ambiguous_non_flathub_refs(
    pyinfra_task_harness,
):
    """Multiple non-Flathub matches fail clearly instead of prompting."""
    module = pyinfra_task_harness.load("flatpak.py")
    with pytest.raises(ValueError, match="multiple non-Flathub remotes"):
        module.select_flatpak_remote(
            "app.one",
            {"remote-a": {"app.one"}, "remote-b": {"app.one"}},
        )


def test_flatpak_remote_selection_rejects_unavailable_packages(
    pyinfra_task_harness,
):
    """An unavailable app or runtime is reported before scheduling installation."""
    module = pyinfra_task_harness.load("flatpak.py")
    with pytest.raises(ValueError, match="unavailable from configured remotes"):
        module.select_flatpak_remote("runtime.missing", {"flathub": {"runtime.other"}})


def _install_calls(harness):
    return [
        call[2] for call in harness.calls
        if call[0] == "flatpak" and call[1] == "packages"
    ]


def test_flatpak_task_discovers_both_ref_types_and_prefers_flathub(
    pyinfra_task_harness,
):
    """Remote discovery includes apps and runtimes and selects Flathub consistently."""
    pyinfra_task_harness.host.data["flatpak_packages"] = [
        "org.example.App",
        "org.example.Codecs",
    ]
    fact_commands = []

    def get_fact(fact, **kwargs):
        command = kwargs.get("command", "")
        if command:
            fact_commands.append(command)
        if fact.__name__ == "FlatpakRemotes":
            return ["flathub", "other"]
        if command == "flatpak list --user --columns=ref":
            return []
        if command.endswith(" flathub"):
            return [
                "app/org.example.App/x86_64/stable",
                "runtime/org.example.Codecs/x86_64/stable",
            ]
        if command.endswith(" other"):
            return [
                "app/org.example.App/x86_64/stable",
                "runtime/org.example.Codecs/x86_64/stable",
            ]
        if fact.__name__ == "FlatpakUpdates":
            return []
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("flatpak.py")

    installs = _install_calls(pyinfra_task_harness)
    assert len(installs) == 1
    assert installs[0]["packages"] == ["org.example.App", "org.example.Codecs"]
    assert installs[0]["remote"] == "flathub"
    assert installs[0]["user"] is True
    assert "flatpak list --user --columns=ref" in fact_commands
    assert (
        "flatpak remote-ls --user --columns=ref flathub" in fact_commands
    )
    assert (
        "flatpak remote-ls --user --columns=ref other" in fact_commands
    )


def test_flatpak_task_skips_installed_runtime_refs(pyinfra_task_harness):
    """An installed runtime is not scheduled for installation again."""
    pyinfra_task_harness.host.data["flatpak_packages"] = ["org.example.Codecs"]

    def get_fact(fact, **kwargs):
        command = kwargs.get("command", "")
        if fact.__name__ == "FlatpakRemotes":
            return ["flathub"]
        if command == "flatpak list --user --columns=ref":
            return ["org.example.Codecs/x86_64/stable"]
        if command.endswith(" flathub"):
            return ["runtime/org.example.Codecs/x86_64/stable"]
        if fact.__name__ in {"FlatpakUpdates", "FlatpakSystemUpdates"}:
            return []
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("flatpak.py")
    assert _install_calls(pyinfra_task_harness) == []


def test_flatpak_facts_are_user_scoped(pyinfra_task_harness):
    """Remote discovery and update checks only inspect user installations."""
    module = pyinfra_task_harness.load("flatpak.py")
    assert module.FlatpakRemotes.command == "flatpak remotes --user --columns=name"
    assert module.FlatpakUpdates.command == (
        "flatpak remote-ls --user --updates --columns=application"
    )
