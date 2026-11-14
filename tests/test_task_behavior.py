"""Direct input/output tests for task helpers and pyinfra operations."""
# pylint: disable=protected-access

import builtins
import sys
from types import SimpleNamespace

import pytest


def test_apt_repository_accepts_supported_signing_key_extensions(pyinfra_task_harness):
    for extension in ("asc", "key"):
        pyinfra_task_harness.load("apt.py", {
            "apt_sources": {
                "docker": {
                    "key": {
                        "url": "https://download.docker.com/linux/debian/gpg",
                        "path": f"/etc/apt/keyrings/docker.{extension}",
                    },
                    "repository": {
                        "url": "https://download.docker.com/linux/debian",
                        "distribution": "bookworm",
                        "components": ["stable"],
                    },
                },
            },
        })

    destinations = [
        kwargs["dest"] for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "apt" and name == "key"
    ]
    assert destinations == [
        "/etc/apt/keyrings/docker.asc",
        "/etc/apt/keyrings/docker.key",
    ]


def test_apt_repository_rejects_unsupported_keyring_suffix(pyinfra_task_harness):
    try:
        pyinfra_task_harness.load("apt.py", {
            "apt_sources": {
                "example": {
                    "key": {"url": "https://example.test/key", "path": "/etc/apt/keyrings/key.pem"},
                    "repository": {
                        "url": "https://example.test/debian",
                        "distribution": "stable",
                    },
                },
            },
        })
    except ValueError as error:
        assert "must end in .gpg, .asc, or .key" in str(error)
    else:
        raise AssertionError("Unsupported APT keyring suffix was accepted")


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


def test_flatpak_command_output_is_parsed_as_application_ids(pyinfra_task_harness):
    module = pyinfra_task_harness.load("flatpak.py")

    assert module._command_lines(
        "app.go2tv.go2tv\norg.example.Installed\n"
    ) == ["app.go2tv.go2tv", "org.example.Installed"]
    assert module._command_lines("") == []
    assert module._command_lines(None) == []
    assert module._command_lines([" app.one ", "", "app.two"]) == [
        "app.one", "app.two"
    ]


def test_flatpak_install_resolves_ids_from_string_command_output(
    pyinfra_task_harness
):
    host = pyinfra_task_harness.host

    def get_fact(fact, *args, **kwargs):
        if getattr(fact, "__name__", "") == "FlatpakRemotes":
            return ["flathub"]
        if getattr(fact, "__name__", "") == "FlatpakUpdates":
            return []
        if getattr(fact, "__name__", "") == "Command":
            command = kwargs.get("command", args[0] if args else "")
            if command.startswith("flatpak list --user"):
                return "org.example.AlreadyInstalled\n"
            if command.startswith("flatpak remote-ls --user"):
                return "app.go2tv.go2tv\norg.example.Available\n"
        return ""

    host.get_fact = get_fact
    pyinfra_task_harness.load("flatpak.py", {
        "flatpak_packages": [
            "app.go2tv.go2tv",
            "org.example.AlreadyInstalled",
        ],
    })

    installs = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "flatpak" and name == "packages"
    ]
    assert len(installs) == 1
    assert installs[0]["packages"] == ["app.go2tv.go2tv"]
    assert installs[0]["remote"] == "flathub"
    assert installs[0]["user"] is True




def test_flatpak_update_skips_only_lock_contention_and_propagates_failures(
    pyinfra_task_harness,
):
    pyinfra_task_harness.host.get_fact = lambda fact, **_kwargs: (
        ["org.example.App"] if fact.__name__ == "FlatpakUpdates" else []
    )
    pyinfra_task_harness.load("flatpak.py")

    update = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Update user Flatpak packages"
    )
    command = update["commands"][0]
    assert "exec 9>/tmp/flatpak-update.lock" in command
    assert "if ! flock -n 9; then" in command
    assert "flatpak update --user -y" in command
    assert '|| echo "Flatpak update already running. Skipping."' not in command

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


def test_git_credentials_use_linux_chattr_only_when_needed(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"git_credentials": ["https://user:token@example.test"]},
        raising=False,
    )
    pyinfra_task_harness.host.get_fact = lambda fact, *_args, **kwargs: (
        True if fact.__name__ == "File"
        else ["old credentials"] if fact.__name__ == "FileContents"
        else ["----i---------e------- /home/tester/.git-credentials"]
        if fact.__name__ == "Command"
        else None
    )
    pyinfra_task_harness.load("git.py")

    commands = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") in {
            "Make git-credentials writable before updating",
            "Protect git-credentials from modification",
        }
    ]
    assert len(commands) == 2
    unlock, protect = commands
    assert unlock["commands"] == [
        "chattr -i -- /home/tester/.git-credentials"
    ]
    assert unlock["_sudo"] is True
    assert unlock["_if"]() is True
    assert protect["commands"] == [
        "chattr +i -- /home/tester/.git-credentials"
    ]
    assert protect["_sudo"] is True
    assert protect["_if"]() is True
    assert not any(
        namespace == "files" and name == "flags"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )


def test_git_credentials_without_secret_leave_existing_file_untouched(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(builtins, "secrets", {}, raising=False)
    pyinfra_task_harness.host.get_fact = lambda *_args, **_kwargs: True
    pyinfra_task_harness.load("git.py")

    assert not any(
        namespace == "files" and name in {"flags", "template"}
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )


def test_git_credentials_are_protected_after_first_deployment(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"git_credentials": ["https://user:token@example.test"]},
        raising=False,
    )
    pyinfra_task_harness.host.get_fact = lambda fact, *_args, **_kwargs: (
        False if fact.__name__ == "File" else None
    )
    pyinfra_task_harness.load("git.py")

    protection = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Protect git-credentials from modification"
    )
    assert protection["_if"]() is True
    assert any(
        namespace == "files" and name == "template"
        and kwargs["dest"] == "/home/tester/.git-credentials"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_git_credentials_unchanged_immutable_file_is_a_noop(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"git_credentials": ["https://user:token@example.test"]},
        raising=False,
    )
    pyinfra_task_harness.host.get_fact = lambda fact, *_args, **_kwargs: (
        True if fact.__name__ == "File"
        else ["https://user:token@example.test"]
        if fact.__name__ == "FileContents"
        else ["----i---------e------- /home/tester/.git-credentials"]
        if fact.__name__ == "Command"
        else None
    )
    pyinfra_task_harness.load("git.py")

    commands = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
    ]
    assert len(commands) == 2
    assert all(kwargs["_if"]() is False for kwargs in commands)


def test_git_credentials_changed_non_immutable_file_is_not_unlocked(
    pyinfra_task_harness, monkeypatch,
):
    monkeypatch.setattr(
        builtins,
        "secrets",
        {"git_credentials": ["https://user:token@example.test"]},
        raising=False,
    )
    pyinfra_task_harness.host.get_fact = lambda fact, *_args, **_kwargs: (
        True if fact.__name__ == "File"
        else ["old credentials"] if fact.__name__ == "FileContents"
        else ["--------------e------- /home/tester/.git-credentials"]
        if fact.__name__ == "Command"
        else None
    )
    pyinfra_task_harness.load("git.py")

    commands = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
    ]
    assert commands[0]["_if"]() is False
    assert commands[1]["_if"]() is True


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





def test_proton_drive_cli_updates_when_configured_version_changes(pyinfra_task_harness):
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "0.9.1",
        },
    })
    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install or update Proton Drive CLI"
    )
    assert "0.9.1/linux-x64/proton-drive" in install["commands"][0]
    assert "proton-drive-version" in install["commands"][-1]
    assert install["_sudo"] is True


def test_proton_drive_cli_skips_when_configured_version_is_installed(
    pyinfra_task_harness,
):
    pyinfra_task_harness.host.get_fact = (
        lambda _fact, **_kwargs: ["0.9.1"]
    )
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "0.9.1",
        },
    })
    assert not any(
        namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install or update Proton Drive CLI"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_proton_flatpak_facts_are_deferred_until_execution(pyinfra_task_harness):
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": True,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": True,
            "drive_cli": False,
        },
    })
    remote = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Configure Flathub"
    )
    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Proton Flatpak application me.proton.Mail"
    )
    assert remote["_if"]() is True
    assert install["_if"]() is True


def test_udev_reload_uses_runtime_change_detection(pyinfra_task_harness, monkeypatch):
    observed = []
    monkeypatch.setattr(
        sys.modules["pyinfra.operations.util"],
        "any_changed",
        lambda *operations: observed.extend(operations) or (lambda: True),
    )
    pyinfra_task_harness.load("system.py", {
        "udev": {"99-example.rules": 'SUBSYSTEM=="example", MODE="0600"'},
    })
    reload_op = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload udev rules"
    )
    assert len(observed) == 1
    assert reload_op["_if"]() is True


def test_usbguard_service_restart_is_conditional_on_configuration_changes(
    pyinfra_task_harness, monkeypatch,
):
    changed = {"value": False}
    monkeypatch.setattr(
        sys.modules["pyinfra.operations.util"],
        "any_changed",
        lambda *_ops: lambda: changed["value"],
    )
    pyinfra_task_harness.load("system.py", {
        "usbguard": {"enabled": True, "rules": ["allow id 1234:5678"]},
    })
    restart = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "service"
        and kwargs.get("name") == "Enable and restart USBGuard"
    )
    ensure = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "service"
        and kwargs.get("name") == "Ensure USBGuard is enabled and running"
    )
    assert restart["service"] == "usbguard"
    assert restart["running"] is True
    assert restart["enabled"] is True
    assert restart["restarted"] is True
    assert restart["_if"]() is False
    assert ensure["_if"]() is True
    changed["value"] = True
    assert restart["_if"]() is True
    assert ensure["_if"]() is False


def test_sudoers_metadata_is_reconciled_when_content_matches(
    pyinfra_task_harness,
):
    expected = (
        "# Managed by pyinfra - do not edit manually\n"
        "tester ALL=(ALL) NOPASSWD: ALL\n"
    )
    pyinfra_task_harness.host.get_fact = lambda fact, *_args, **_kwargs: (
        expected if fact.__name__ == "SudoersFile" else False
    )
    pyinfra_task_harness.load("sudo.py", {
        "sudoers_rules": ["tester ALL=(ALL) NOPASSWD: ALL"],
    })

    managed_file = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("dest") == "/etc/sudoers.d/99-local"
    )
    assert managed_file["mode"] == "440"
    assert managed_file["user"] == "root"
    assert managed_file["group"] == "root"
    assert not any(
        namespace == "server" and name == "shell"
        and kwargs.get("name") == "Validate custom sudoers configuration"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_ssh_keypair_validation_runs_for_incomplete_pairs_and_skips_complete_pairs(
    pyinfra_task_harness,
):
    states = {
        "/home/tester/.ssh/id_ed25519": True,
        "/home/tester/.ssh/id_ed25519.pub": False,
    }
    pyinfra_task_harness.host.get_fact = (
        lambda _fact, *_args, **kwargs: states[kwargs["path"]]
    )
    pyinfra_task_harness.load("ssh_keys.py", {
        "ssh_keys": [{"name": "id_ed25519"}],
        "username": "tester",
        "usergroup": "tester",
    })
    generation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Generate SSH keypair: id_ed25519"
    )
    assert generation["_if"][0]() is True
    assert "Incomplete SSH keypair" in generation["commands"][0]

    # pyinfra evaluates facts while loading the task. Load it again with
    # the complete keypair state to verify the condition from that snapshot.
    states["/home/tester/.ssh/id_ed25519.pub"] = True
    pyinfra_task_harness.load("ssh_keys.py", {
        "ssh_keys": [{"name": "id_ed25519"}],
        "username": "tester",
        "usergroup": "tester",
    })
    complete_generation = next(
        kwargs for namespace, name, kwargs in reversed(pyinfra_task_harness.calls)
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Generate SSH keypair: id_ed25519"
    )
    assert complete_generation["_if"][0]() is False


def test_dehydrated_fact_handles_true_false_and_empty_output(pyinfra_task_harness):
    module = pyinfra_task_harness.load("dehydrated.py")
    fact = module.CertNeedsRenewal()
    assert fact.process(["false"]) is False
    assert fact.process(["true"]) is True
    assert fact.process([]) is False

    # Keep the wildcard unquoted so the remote shell expands certificate paths.
    assert 'for cert in /var/lib/dehydrated/certs/*/fullchain.pem; do' in fact.command
    assert 'for cert in "/var/lib/dehydrated/certs/*/fullchain.pem"; do' not in fact.command

@pytest.mark.parametrize(
    ("config", "message"),
    [
        ({"typo-ssh": "Allow"}, "Unsupported UFW rule name"),
        ({"ssh": "allow"}, "Invalid UFW action"),
        ({"custom": {"action": "Allow"}}, "non-empty string"),
        ({"custom": {"action": "Allow", "rule": "   "}}, "non-empty string"),
        ({"custom": {"action": "Allow", "rule": "from 'unterminated"}}, "Invalid UFW custom rule"),
        ({"custom": {"action": "Allow", "rule": "22/tcp", "extra": True}}, "Unsupported UFW custom rule options"),
    ],
)
def test_ufw_rejects_invalid_configuration(pyinfra_task_harness, config, message):
    with pytest.raises(ValueError, match=message):
        pyinfra_task_harness.load("ufw.py", {"ufw": config})


def test_ufw_rejects_non_dictionary_configuration(pyinfra_task_harness):
    with pytest.raises(ValueError, match="must be a dictionary"):
        pyinfra_task_harness.load("ufw.py", {"ufw": []})


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
    module = pyinfra_task_harness.load("workstation/cosmic/config.py", {
        "workstation": {"cosmic": {"enabled": False}}
    })
    module.deploy_cosmic_values("dock", {"config.ron": "value"})
    assert not pyinfra_task_harness.calls

    module = pyinfra_task_harness.load("workstation/cosmic/config.py", {
        "workstation": {"cosmic": {"enabled": True}},
        "homedir": "/home/tester",
        "username": "tester",
    })
    module.deploy_cosmic_values("dock", {
        "com.system76.CosmicPanel/v1/plugins.ron": "[\"dock\"]",
        "com.system76.CosmicPanel/v1/anchor": "Bottom",
        "com.system76.CosmicPanel.Dock/v1/anchor": "Bottom",
    })
    directories = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
    ]
    uploads = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
    ]
    assert [call["path"] for call in directories] == [
        "/home/tester/.config/cosmic/com.system76.CosmicPanel.Dock/v1",
        "/home/tester/.config/cosmic/com.system76.CosmicPanel/v1",
    ]
    plugin_upload = next(
        call for call in uploads
        if call["dest"].endswith("/com.system76.CosmicPanel/v1/plugins.ron")
    )
    uploaded_content = plugin_upload["src"].getvalue()
    assert uploaded_content == '["dock"]' + chr(10)
    assert uploaded_content.endswith(chr(10))
    assert "\\n" not in uploaded_content
    assert plugin_upload["mode"] == "0644"


def test_numeric_directory_skips_when_uid_gid_and_mode_match(pyinfra_task_harness):
    module = pyinfra_task_harness.load("docker.py")
    observed = []
    observed_sudo = []
    def get_fact(_fact, command, **kwargs):
        observed.append(command)
        observed_sudo.append(kwargs.get("_sudo"))
        return ["1000:1000:750"]

    pyinfra_task_harness.host.get_fact = get_fact

    module.ensure_numeric_directory(
        "/home/tester/.docker/data", "1000", "1000", "750", sudo=False
    )

    operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs["name"] == "Ensure directory metadata: /home/tester/.docker/data"
    )
    assert operation["_sudo"] is False
    assert operation["_if"]() is False
    assert observed == [
        "if [ -d /home/tester/.docker/data ]; then "
        "stat -c '%u:%g:%a' -- /home/tester/.docker/data; "
        "else printf 'missing\\n'; fi"
    ]
    assert observed_sudo == [False]


def test_numeric_directory_repairs_missing_or_mismatched_metadata(
    pyinfra_task_harness
):
    module = pyinfra_task_harness.load("docker.py")
    current = {"metadata": "missing"}
    observed_sudo = []

    def get_fact(*_args, **kwargs):
        observed_sudo.append(kwargs.get("_sudo"))
        return current["metadata"]

    pyinfra_task_harness.host.get_fact = get_fact

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
    assert observed_sudo == [True, True]
    assert "install -d -o 1000 -g 1000 -m 750" in operation["commands"][0]

def test_zsh_task_installs_playerctl_for_hyfetch(pyinfra_task_harness):
    pyinfra_task_harness.load("zsh.py")

    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "apt" and name == "packages"
    )
    assert install["packages"] == ["playerctl"]
    assert install["name"] == "Ensure playerctl is installed for Hyfetch music metadata"

    hyfetch = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Configure hyfetch"
    )
    assert hyfetch["src"] == "files/hyfetch.conf"
    assert hyfetch["dest"].endswith("/.config/neowofetch/config.conf")

    helper_dir = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "directory"
        and kwargs.get("name") == "Create Hyfetch helper directory"
    )
    assert helper_dir["path"].endswith("/.local/bin/")
    assert helper_dir["mode"] == "755"

    helper = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Deploy HyFetch LiMusic now-playing helper"
    )
    assert helper["src"] == "files/hyfetch-song"
    assert helper["dest"].endswith("/.local/bin/hyfetch-song")
    assert helper["mode"] == "750"



def test_system_locale_replaces_the_matching_lang_line(pyinfra_task_harness):
    """The locale value replaces LANG rather than writing the regex as content."""
    pyinfra_task_harness.host.get_fact = lambda fact, **_kwargs: (
        ["C.UTF-8"] if fact.__name__ == "Locales" else None
    )
    pyinfra_task_harness.load("system.py", {"locale": "C.UTF-8"})

    locale_operation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "line"
        and kwargs.get("name") == "Set system default locale: C.UTF-8"
    )
    assert locale_operation["path"] == "/etc/default/locale"
    assert locale_operation["line"] == "^LANG="
    assert locale_operation["replace"] == 'LANG="C.UTF-8"'
    assert locale_operation["present"] is True

def test_system_locale_skips_generation_when_equivalent_locale_is_installed(
    pyinfra_task_harness,
):
    """Installed locale aliases are normalized before scheduling generation."""
    pyinfra_task_harness.host.get_fact = (
        lambda fact, **_kwargs: ["C.utf8"] if fact.__name__ == "Locales" else None
    )
    pyinfra_task_harness.load("system.py", {"locale": "C.UTF-8"})

    assert not any(
        namespace == "server" and name == "locale"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )
    default_locale = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "line"
        and kwargs.get("name") == "Set system default locale: C.UTF-8"
    )
    assert default_locale["line"] == "^LANG="
    assert default_locale["replace"] == 'LANG="C.UTF-8"'


def test_system_locale_generates_missing_locale(pyinfra_task_harness):
    """A locale not present in the installed locale fact is generated."""
    pyinfra_task_harness.host.get_fact = (
        lambda fact, **_kwargs: [] if fact.__name__ == "Locales" else None
    )
    pyinfra_task_harness.load("system.py", {"locale": "en_GB.UTF-8"})

    assert any(
        namespace == "server" and name == "locale"
        and kwargs.get("locale") == "en_GB.UTF-8"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )

def test_powerline_fonts_install_and_refresh_only_when_required(
    pyinfra_task_harness, monkeypatch,
):
    """Powerline font copies and cache refresh are gated by actual changes."""
    pyinfra_task_harness.host.get_fact = (
        lambda fact, _command=None, **_kwargs: ["missing"] if fact.__name__ == "Command" else None
    )
    changed = {"value": False}
    util = sys.modules["pyinfra.operations.util"]
    monkeypatch.setattr(
        util,
        "any_changed",
        lambda *operations: lambda: any(operation.did_change() for operation in operations),
    )
    monkeypatch.setattr(
        pyinfra_task_harness.result,
        "did_change",
        lambda: changed["value"],
    )
    pyinfra_task_harness.load("fonts.py", {"powerline_fonts": True})

    extraction = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "unarchive"
        and kwargs.get("name") == "Extract Powerline fonts"
    )
    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install missing Powerline fonts"
    )
    refresh = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Refresh font cache"
    )

    assert extraction["creates"] == "/tmp/powerline-fonts/fonts-master"
    assert install["_if"]() is True
    pyinfra_task_harness.host.get_fact = (
        lambda fact, _command=None, **_kwargs: ["current"] if fact.__name__ == "Command" else None
    )
    assert install["_if"]() is False
    assert refresh["_if"]() is False
    changed["value"] = True
    assert refresh["_if"]() is True


def test_powerline_fonts_are_not_downloaded_when_disabled(pyinfra_task_harness):
    """The optional Powerline archive is untouched when the feature is disabled."""
    pyinfra_task_harness.load("fonts.py", {"powerline_fonts": False})

    assert not any(
        namespace == "files" and name in {"download", "unarchive"}
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )


def test_cosmic_panel_uses_default_applets_when_not_configured(
    pyinfra_task_harness, monkeypatch,
):
    """Enabling the panel without an applet override preserves COSMIC defaults."""
    monkeypatch.delitem(sys.modules, "tasks.workstation.cosmic.config", raising=False)
    pyinfra_task_harness.load("workstation/cosmic/panel.py", {
        "username": "tester",
        "homedir": "/home/tester",
        "workstation": {
            "cosmic": {
                "enabled": True,
                "panel": {"enabled": True},
            },
        },
    })

    panel_config = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == (
            "Configure COSMIC panel: "
            "com.system76.CosmicPanel.Panel/v1/plugins_wings"
        )
    )
    panel_values = panel_config["src"].getvalue()
    assert panel_values.endswith(chr(10))
    assert "\\n" not in panel_values
    assert "com.system76.CosmicAppletQuickSettings" in panel_values
    assert "com.system76.CosmicAppletNotifications" in panel_values
    assert "com.system76.CosmicAppletTime" in panel_values
    assert "com.system76.CosmicAppletUserSession" in panel_values


def test_cosmic_panel_respects_explicit_empty_applet_configuration(
    pyinfra_task_harness, monkeypatch,
):
    """An explicit empty applet mapping removes all default panel applets."""
    monkeypatch.delitem(sys.modules, "tasks.workstation.cosmic.config", raising=False)
    pyinfra_task_harness.load("workstation/cosmic/panel.py", {
        "username": "tester",
        "homedir": "/home/tester",
        "workstation": {
            "cosmic": {
                "enabled": True,
                "panel": {
                    "enabled": True,
                    "applets": {"left": [], "center": [], "right": []},
                },
            },
        },
    })

    panel_config = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "put"
        and kwargs.get("name") == (
            "Configure COSMIC panel: "
            "com.system76.CosmicPanel.Panel/v1/plugins_wings"
        )
    )
    assert panel_config["src"].getvalue() == "Some((\n    [],\n    [],\n))\n"


@pytest.mark.parametrize("name", ["../cron", "nested/repository", ".", "..", "bad name"])
def test_apt_repository_rejects_unsafe_repository_names(
    pyinfra_task_harness, name,
):
    with pytest.raises(ValueError, match="Invalid APT repository name"):
        pyinfra_task_harness.load("apt.py", {
            "apt_sources": {name: {}},
        })


def test_apt_sources_must_be_a_mapping(pyinfra_task_harness):
    with pytest.raises(ValueError, match="apt_sources must be a mapping"):
        pyinfra_task_harness.load("apt.py", {"apt_sources": ["example"]})


def test_apt_repository_requires_key_and_repository_mappings(pyinfra_task_harness):
    with pytest.raises(ValueError, match="requires key and repository mappings"):
        pyinfra_task_harness.load("apt.py", {
            "apt_sources": {"example": {"key": [], "repository": {}}},
        })


@pytest.mark.parametrize(
    ("jobs", "expect_package", "expect_service"),
    [
        (
            [{
                "name": "obsolete-job",
                "command": "/usr/bin/true",
                "present": False,
            }],
            True,
            False,
        ),
        (
            [{
                "name": "active-job",
                "command": "/usr/bin/true",
                "minute": "*/5",
            }, {
                "name": "obsolete-job",
                "command": "/usr/bin/true",
                "present": False,
            }],
            True,
            True,
        ),
        ([], False, False),
    ],
)
def test_cron_package_and_daemon_follow_required_lifecycle(
    pyinfra_task_harness, jobs, expect_package, expect_service,
):
    """Removal-only jobs need crontab, but do not need the cron daemon."""
    pyinfra_task_harness.load("cron.py", {
        "username": "tester",
        "cron_jobs": jobs,
    })

    package_operations = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "apt" and name == "packages"
        and kwargs.get("name") == "Install cron"
    ]
    service_operations = [
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "service"
        and kwargs.get("name") == "Ensure cron daemon is enabled and running"
    ]

    assert bool(package_operations) is expect_package
    assert bool(service_operations) is expect_service
    assert len([
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "crontab" and name == "crontab"
    ]) == len(jobs)
