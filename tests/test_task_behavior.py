"""Direct input/output tests for task helpers and pyinfra operations."""
# pylint: disable=protected-access

from types import SimpleNamespace


def test_upgrade_apt_packages_runs_only_after_an_index_change(
    pyinfra_task_harness, monkeypatch
):
    module = pyinfra_task_harness.load("apt.py")
    updates = [object(), object()]
    changed = {"value": False}
    monkeypatch.setattr(
        module, "any_changed", lambda *operations: (
            updates == list(operations) and (lambda: changed["value"])
        )
    )

    module.upgrade_apt_packages(updates)
    upgrade = next(
        kwargs for namespace, name, kwargs in reversed(pyinfra_task_harness.calls)
        if namespace == "apt" and name == "upgrade"
    )
    assert upgrade["auto_remove"] is True
    assert upgrade["_if"]() is False

    changed["value"] = True
    assert upgrade["_if"]() is True


def test_flatpak_output_normalization_handles_common_result_shapes(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("flatpak.py")

    assert module._output_as_text("output") == "output"
    assert module._output_as_text(("one", ["two", "three"])) == "one\ntwo\nthree"
    assert module._output_as_text(
        SimpleNamespace(stdout=["out"], stderr="err")
    ) == "out"
    assert module._output_as_text(SimpleNamespace(combined="combined")) == "combined"


def test_flatpak_uninstall_operation_reports_only_real_removals(
    pyinfra_task_harness, monkeypatch
):
    module = pyinfra_task_harness.load("flatpak.py")
    operation = module.uninstall_unused_packages.__wrapped__

    monkeypatch.setattr(
        pyinfra_task_harness.host, "run_shell_command", lambda *_a, **_k: "UNCHANGED"
    )
    assert not list(operation())

    monkeypatch.setattr(
        pyinfra_task_harness.host, "run_shell_command", lambda *_a, **_k: "REMOVED"
    )
    assert list(operation()) == ["true"]


def test_set_immutable_uses_requested_chattr_flag(pyinfra_task_harness, capsys):
    module = pyinfra_task_harness.load("git.py")
    calls = []
    pyinfra_task_harness.host.run_shell_command = (
        lambda command, **kwargs: calls.append((command, kwargs))
    )

    module.set_immutable("/home/tester/.git-credentials", False)
    module.set_immutable("/home/tester/.git-credentials", True)

    assert calls == [
        ("chattr -i /home/tester/.git-credentials",
         {"print_output": False, "_sudo": True}),
        ("chattr +i /home/tester/.git-credentials",
         {"print_output": False, "_sudo": True}),
    ]
    assert "Set -i" in capsys.readouterr().out
    assert "Set +i" in capsys.readouterr().out


def test_apparmor_enforcement_is_skipped_when_profiles_are_enforcing(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("apparmor.py")
    pyinfra_task_harness.host.get_fact = lambda _fact: {
        "profile-a": "enforce", "profile-b": "enforce"
    }

    assert not list(module.enforce_apparmor_profile.__wrapped__(
        "/etc/apparmor.d/example", ["profile-a", "profile-b"]
    ))


def test_apparmor_enforcement_schedules_only_profiles_not_already_enforcing(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("apparmor.py")
    pyinfra_task_harness.host.get_fact = lambda _fact: {
        "profile-a": "enforce", "profile-b": "complain"
    }

    commands = list(module.enforce_apparmor_profile.__wrapped__(
        "/etc/apparmor.d/example", ["profile-a", "profile-b"]
    ))

    assert len(commands) == 1
    assert "aa-enforce" in str(commands[0])
    assert "/etc/apparmor.d/example" in str(commands[0])
