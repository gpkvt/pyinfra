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
    output = capsys.readouterr().out
    assert "Set -i" in output
    assert "Set +i" in output


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


def test_system_timezone_fact_normalizes_output(pyinfra_task_harness):
    module = pyinfra_task_harness.load("system.py")
    assert module.SystemTimezone().process([" Europe/Berlin ", "\n"]) == "Europe/Berlin"
    assert module.SystemTimezone().process(["  ", "\n"]) is None


def test_dehydrated_fact_handles_true_false_and_empty_output(pyinfra_task_harness):
    module = pyinfra_task_harness.load("dehydrated.py")
    fact = module.CertNeedsRenewal()
    assert fact.process(["false"]) is False
    assert fact.process(["true"]) is True
    assert fact.process([]) is False


def test_ufw_added_rules_normalizes_only_added_rule_commands(pyinfra_task_harness):
    module = pyinfra_task_harness.load("ufw.py", {"ufw": {}})
    assert module.UfwAddedRules().process([
        "Added user rules (see 'ufw status' for running firewall):",
        "ufw allow 22/tcp",
        "  ufw deny 80/tcp  ",
        "",
    ]) == {"ufw allow 22/tcp", "ufw deny 80/tcp"}


def test_ufw_custom_rule_matches_with_or_without_explicit_in_token(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("ufw.py", {"ufw": {}})
    pyinfra_task_harness.host.get_fact = lambda _fact: {
        "ufw allow from 192.0.2.0/24 to any port 443 proto tcp"
    }

    assert module.ufw_custom_rule_exists(
        "Allow", "from 192.0.2.0/24 to any port 443 proto tcp"
    ) is True
    assert module.ufw_custom_rule_exists(
        "Allow", "in from 192.0.2.0/24 to any port 443 proto tcp"
    ) is True
    assert module.ufw_custom_rule_exists(
        "Deny", "from 192.0.2.0/24 to any port 443 proto tcp"
    ) is False


def test_vscodium_fact_quotes_user_and_normalizes_installed_ids(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("vscodium.py", {"vscodium": {}})
    fact = module.VSCodiumExtensions()

    assert fact.command("user name") == (
        "sudo -H -u 'user name' -- sh -lc 'codium --list-extensions'"
    )
    assert fact.process([
        "Vendor.Extension@1.2.3", "vendor.extension", "", "Other.Tool"
    ]) == {"vendor.extension", "other.tool"}


def test_cosmic_values_are_deployed_only_when_enabled(pyinfra_task_harness):
    module = pyinfra_task_harness.load("cosmic/config.py", {
        "cosmic": {"enabled": False}
    })
    module.deploy_cosmic_values("dock", {"config.ron": "value"})
    assert not pyinfra_task_harness.calls

    module = pyinfra_task_harness.load("cosmic/config.py", {
        "cosmic": {"enabled": True},
        "homedir": "/home/tester",
        "username": "tester",
    })
    module.deploy_cosmic_values("dock", {
        "com.system76.CosmicPanel/v1/plugins.ron": "[\"dock\"]"
    })
    directories = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
    ]
    uploads = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
    ]
    assert directories[-1]["path"] == (
        "/home/tester/.config/cosmic/com.system76.CosmicPanel/v1"
    )
    assert uploads[-1]["dest"] == (
        "/home/tester/.config/cosmic/com.system76.CosmicPanel/v1/plugins.ron"
    )
    assert uploads[-1]["src"].getvalue() == '["dock"]\n'
    assert uploads[-1]["mode"] == "0644"


def test_numeric_directory_skips_when_uid_gid_and_mode_match(pyinfra_task_harness):
    module = pyinfra_task_harness.load("docker.py")
    observed = []
    pyinfra_task_harness.host.get_fact = (
        lambda _fact, command, **_kwargs: observed.append(command)
        or "1000:1000:750"
    )

    module.ensure_numeric_directory(
        "/home/tester/.docker/data", "1000", "1000", "750", sudo=False
    )

    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs["name"] == "Ensure directory metadata: /home/tester/.docker/data"
    )
    assert observed == [
        "if [ -d /home/tester/.docker/data ]; then "
        "stat -c '%u:%g:%a' -- /home/tester/.docker/data; "
        "else printf 'missing\\n'; fi"
    ]
    assert operation["_sudo"] is False
    assert operation["_if"]() is False


def test_numeric_directory_repairs_missing_or_mismatched_metadata(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("docker.py")
    current = {"metadata": "missing"}
    pyinfra_task_harness.host.get_fact = (
        lambda *_args, **_kwargs: current["metadata"]
    )

    module.ensure_numeric_directory(
        "/home/tester/.docker/data", "1000", "1000", "750"
    )
    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs["name"] == "Ensure directory metadata: /home/tester/.docker/data"
    )

    assert operation["_if"]() is True
    current["metadata"] = "1000:1000:700"
    assert operation["_if"]() is True
    assert "install -d -o 1000 -g 1000 -m 750" in operation["commands"][0]
