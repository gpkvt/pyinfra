"""Focused tests for Flatpak remote selection and deployment behavior."""

import pytest



def load_flatpak_task(pyinfra_task_harness):
    """Load the task module under the shared mocked pyinfra environment."""
    return pyinfra_task_harness.load("flatpak.py")


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


def test_flatpak_remote_selection_rejects_unavailable_applications(
    pyinfra_task_harness,
):
    """An unavailable application is reported before scheduling installation."""
    module = pyinfra_task_harness.load("flatpak.py")
    with pytest.raises(ValueError, match="unavailable from configured remotes"):
        module.select_flatpak_remote("app.missing", {"flathub": {"app.other"}})


def test_flatpak_task_installs_duplicate_refs_from_flathub(pyinfra_task_harness):
    """The task passes an explicit Flathub remote to avoid ambiguous installs."""
    pyinfra_task_harness.host.data["flatpak_packages"] = ["app.one"]
    fact_commands = []

    def get_fact(fact, **kwargs):
        command = kwargs.get("command", "")
        if command:
            fact_commands.append(command)
        if fact.__name__ == "FlatpakRemotes":
            return ["flathub", "other"]
        if command == "flatpak list --user --app --columns=application":
            return []
        if command.endswith(" flathub"):
            return ["app.one"]
        if command.endswith(" other"):
            return ["app.one"]
        if fact.__name__ == "FlatpakUpdates":
            return []
        return []
    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("flatpak.py")
    installs = [
        call[2] for call in pyinfra_task_harness.calls
        if call[0] == "flatpak" and call[1] == "packages"
    ]
    assert len(installs) == 1
    assert installs[0]["packages"] == ["app.one"]
    assert installs[0]["remote"] == "flathub"
    assert installs[0]["user"] is True
    assert (
        "flatpak remote-ls --user --app --columns=application flathub"
        in fact_commands
    )
    assert (
        "flatpak remote-ls --user --app --columns=application other"
        in fact_commands
    )


def test_flatpak_task_skips_already_installed_applications(pyinfra_task_harness):
    """Installed apps are not rescheduled even if their configured remote differs."""
    pyinfra_task_harness.host.data["flatpak_packages"] = ["app.one"]
    def get_fact(fact, **kwargs):
        if fact.__name__ == "FlatpakRemotes":
            return ["flathub"]
        if kwargs.get("command") == "flatpak list --user --app --columns=application":
            return ["app.one"]
        if fact.__name__ in {"FlatpakUpdates", "FlatpakSystemUpdates"}:
            return []
        return []
    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("flatpak.py")
    assert not any(
        call[0] == "flatpak" and call[1] == "packages"
        for call in pyinfra_task_harness.calls
    )



def test_flatpak_facts_are_user_scoped(pyinfra_task_harness):
    """Remote discovery and update checks only inspect user installations."""
    module = pyinfra_task_harness.load("flatpak.py")
    assert module.FlatpakRemotes.command == "flatpak remotes --user --columns=name"
    assert module.FlatpakUpdates.command == (
        "flatpak remote-ls --user --updates --columns=application"
    )
