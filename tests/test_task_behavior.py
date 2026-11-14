"""Direct input/output tests for task helpers and pyinfra operations."""
# pylint: disable=protected-access

import hashlib
from types import SimpleNamespace

import pytest


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
    assert operation["_sudo"] is False
    assert operation["_if"]() is False
    assert observed == [
        "if [ -d /home/tester/.docker/data ]; then "
        "stat -c '%u:%g:%a' -- /home/tester/.docker/data; "
        "else printf 'missing\\n'; fi"
    ]


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


def test_powerline_fonts_extracts_on_first_deployment(pyinfra_task_harness):
    """Extraction and cache refresh are gated by actual operation changes."""
    result = pyinfra_task_harness.result
    result.did_change = lambda: True

    pyinfra_task_harness.load("fonts.py", {"powerline_fonts": True})

    extract = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "unarchive"
    )
    copy_fonts = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Powerline fonts"
    )
    cache = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Refresh font cache"
    )

    assert extract["_if"]() is True
    assert copy_fonts["_if"]() is True
    assert "cp -f" in copy_fonts["commands"][0]
    assert cache["_if"]() is True


def test_system_reloads_are_gated_by_operation_callbacks(pyinfra_task_harness):
    """udev and USBGuard reloads use execution-time change callbacks."""
    pyinfra_task_harness.load("system.py", {
        "locale": "",
        "udev": {"99-test.rules": 'SUBSYSTEM=="usb", MODE="0660"'},
        "usbguard": {
            "enabled": True,
            "rules": ["allow id 1234:5678"],
        },
    })

    reload_udev = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Reload udev rules"
    )
    restart_usbguard = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Enable and restart USBGuard after configuration changes"
    )
    ensure_usbguard = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "service"
        and kwargs.get("name") == "Ensure USBGuard is enabled and running"
    )

    assert callable(reload_udev["_if"])
    assert callable(restart_usbguard["_if"])
    assert callable(ensure_usbguard["_if"])
    assert reload_udev["_if"]() is False
    assert restart_usbguard["_if"]() is False
    assert ensure_usbguard["_if"]() is True

    pyinfra_task_harness.result.did_change = lambda: True
    assert reload_udev["_if"]() is True
    assert restart_usbguard["_if"]() is True
    assert ensure_usbguard["_if"]() is False


def test_mullvad_extensions_use_declarative_downloads(pyinfra_task_harness):
    """Existing extension files are reconciled against the configured URL."""
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
        "username": "tester",
        "usergroup": "tester",
        "mullvad_extensions": {
            "privacy-addon": {
                "id": "privacy@example.test",
                "url": "https://example.test/privacy.xpi",
            },
        },
    })

    download = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "download"
    )
    assert download["src"] == "https://example.test/privacy.xpi"
    assert download["dest"] == (
        "/opt/mullvad-browser/distribution/extensions/privacy@example.test.xpi"
    )
    assert "_if" not in download


@pytest.mark.parametrize("url", [
    "https://",
    "https:///extension.xpi",
    "http://example.test/extension.xpi",
    "https://user:password@example.test/extension.xpi",
    "not-a-url",
])
def test_mullvad_extension_rejects_invalid_urls(pyinfra_task_harness, url):
    with pytest.raises(ValueError, match="Invalid Mullvad extension URL"):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
            "mullvad_extensions": {
                "invalid": {
                    "id": "privacy@example.test",
                    "url": url,
                },
            },
        })


def test_mullvad_extension_accepts_brace_wrapped_uuid(pyinfra_task_harness):
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
        "mullvad_extensions": {
            "uuid-addon": {
                "id": "{12345678-1234-1234-1234-123456789abc}",
                "url": "https://example.test/extension.xpi",
            },
        },
    })

    download = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "files" and name == "download"
    )
    assert download["dest"].endswith(
        "/{12345678-1234-1234-1234-123456789abc}.xpi"
    )


def test_mullvad_extension_forces_download_when_source_changes(
    pyinfra_task_harness
):
    old_url = "https://old.example.test/extension.xpi"
    new_url = "https://new.example.test/extension.xpi"
    old_hash = hashlib.sha256(old_url.encode()).hexdigest()
    new_hash = hashlib.sha256(new_url.encode()).hexdigest()

    def get_fact(fact, *_args, **kwargs):
        if getattr(fact, "__name__", "") == "Command":
            return [old_hash]
        if getattr(fact, "__name__", "") == "File":
            return True
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
        "mullvad_extensions": {
            "privacy-addon": {
                "id": "privacy@example.test",
                "url": new_url,
            },
        },
    })

    calls = pyinfra_task_harness.calls
    download_index = next(
        i for i, (namespace, name, _kwargs) in enumerate(calls)
        if namespace == "files" and name == "download"
    )
    marker_index = next(
        i for i, (namespace, name, kwargs) in enumerate(calls)
        if namespace == "files" and name == "put"
        and kwargs.get("name") == "Record privacy-addon source URL"
    )

    download = calls[download_index][2]
    marker = calls[marker_index][2]

    assert download["force"] is True
    assert download["src"] == new_url
    assert marker["src"].getvalue() == f"{new_hash}\n"
    assert marker_index > download_index


def test_mullvad_extension_rejects_path_traversal_ids(pyinfra_task_harness):
    """Extension IDs cannot escape the managed extensions directory."""
    with pytest.raises(ValueError, match="Invalid Mullvad extension ID"):
        pyinfra_task_harness.load("mullvad_extensions.py", {
            "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
            "mullvad_extensions": {
                "malicious": {
                    "id": "../outside",
                    "url": "https://example.test/extension.xpi",
                },
            },
        })


def test_mullvad_extension_skips_download_when_source_marker_matches(
    pyinfra_task_harness
):
    """An existing XPI with its matching URL marker is left untouched."""
    url = "https://example.test/privacy.xpi"
    expected_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get_fact(fact, *_args, **_kwargs):
        if getattr(fact, "__name__", "") == "Command":
            return [expected_hash]
        if getattr(fact, "__name__", "") == "File":
            return True
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("mullvad_extensions.py", {
        "mullvad_browser_dir": "/opt/mullvad-browser/distribution",
        "mullvad_extensions": {
            "privacy-addon": {
                "id": "privacy@example.test",
                "url": url,
            },
        },
    })

    assert not any(
        namespace == "files" and name == "download"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )

def test_proton_flatpak_detection_handles_command_fact_lines(pyinfra_task_harness):
    """Flatpak remotes and installed applications are parsed as output lines."""
    host = pyinfra_task_harness.host

    def get_fact(fact, *args, **kwargs):
        command = kwargs.get("command", args[0] if args else "")
        if getattr(fact, "__name__", "") == "Command":
            if command.startswith("flatpak remote-list"):
                return ["flathub"]
        return []

    host.get_fact = get_fact
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

    remote_add = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Configure Flathub"
    )
    assert remote_add["_if"]() is False

    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "flatpak" and name == "packages"
    )
    assert install["packages"] == ["me.proton.Mail"]
    assert install["remote"] == "flathub"
    assert install["user"] is True


def test_proton_drive_cli_uses_documented_version_key(pyinfra_task_harness):
    """The configured drive_cli_version is used in the download URL."""
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "1.2.3",
        },
    })
    install = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Proton Drive CLI"
    )
    assert "https://proton.me/download/drive/cli/1.2.3/linux-x64/proton-drive" in install["commands"][0]


def test_proton_drive_cli_rejects_invalid_version(pyinfra_task_harness):
    with pytest.raises(ValueError, match="Invalid Proton Drive CLI version"):
        pyinfra_task_harness.load("proton.py", {
            "proton": {
                "mail": False,
                "bridge": False,
                "vpn": False,
                "pass": False,
                "flatpak": False,
                "drive_cli": True,
                "drive_cli_version": "../latest",
            },
        })


def test_proton_drive_cli_skips_when_requested_version_is_installed(pyinfra_task_harness):
    """An exact version marker prevents unnecessary binary downloads."""
    def get_fact(fact, *args, **kwargs):
        if getattr(fact, "__name__", "") == "File":
            return True
        command = kwargs.get("command", args[0] if args else "")
        if (
            getattr(fact, "__name__", "") == "Command"
            and "proton-drive.version" in command
        ):
            return ["1.2.3"]
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "1.2.3",
        },
    })
    assert not any(
        namespace == "server" and name == "shell"
        and kwargs.get("name", "").startswith("Install Proton Drive CLI")
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_docker_power_restore_uses_file_fact(pyinfra_task_harness):
    """The battery-saver marker is checked with pyinfra's File fact."""
    pyinfra_task_harness.host.get_fact = lambda fact, *args, **kwargs: (
        getattr(fact, "__name__", "") == "File"
        and kwargs.get("path") == "/var/lib/docker-power-manager/running-containers"
    )
    pyinfra_task_harness.load("docker_power.py", {
        "docker_sablier": {"enabled": True},
    })
    restore = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Restore containers previously stopped by the battery saver"
    )
    assert restore["_if"]() is True

def test_sudoers_uses_file_contents_fact_to_skip_unchanged_file(pyinfra_task_harness):
    """An unchanged sudoers file skips validation and installation."""
    content = (
        "# Managed by pyinfra - do not edit manually\n"
        "%sudo ALL=(ALL:ALL) ALL\n"
    )
    pyinfra_task_harness.host.get_fact = lambda fact, **_kwargs: (
        content.splitlines()
        if getattr(fact, "__name__", "") == "FileContents"
        else False
    )
    pyinfra_task_harness.load("sudo.py", {
        "sudoers_rules": ["%sudo ALL=(ALL:ALL) ALL"],
    })
    assert not any(
        namespace == "server" and name == "shell"
        and kwargs.get("name") == "Validate custom sudoers configuration"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )
    assert not any(
        namespace == "files" and name == "put"
        and kwargs.get("name") == "Manage custom sudoers configuration"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_ssh_keypair_incomplete_state_fails_instead_of_creating_empty_key(
    pyinfra_task_harness
):
    """A half-present keypair reaches the explicit validation failure path."""
    pyinfra_task_harness.host.get_fact = lambda fact, *args, **kwargs: (
        getattr(fact, "__name__", "") == "File"
        and kwargs.get("path", "").endswith("/id_ed25519")
    )
    pyinfra_task_harness.load("ssh_keys.py", {
        "username": "tester",
        "usergroup": "tester",
        "ssh_keys": [{"name": "id_ed25519"}],
    })
    generation = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "server" and name == "shell"
        and kwargs.get("name") == "Generate SSH keypair: id_ed25519"
    )
    assert generation["_if"][0]() is True
    assert "Incomplete SSH keypair" in generation["commands"][0]


def test_apt_sources_use_native_keyring_operation(pyinfra_task_harness):
    """APT signing keys are managed by pyinfra's apt.key operation."""
    pyinfra_task_harness.load("apt.py", {
        "apt_sources": {
            "example": {
                "key": {
                    "url": "https://example.test/archive-key.asc",
                    "path": "/etc/apt/keyrings/example.gpg",
                    "keyid": "0123456789ABCDEF",
                },
                "repository": {
                    "url": "https://example.test/apt",
                    "distribution": "stable",
                    "components": ["main"],
                },
            },
        },
    })
    key = next(
        kwargs for namespace, name, kwargs in pyinfra_task_harness.calls
        if namespace == "apt" and name == "key"
    )
    assert key["src"] == "https://example.test/archive-key.asc"
    assert key["dest"] == "/etc/apt/keyrings/example.gpg"
    assert key["keyid"] == "0123456789ABCDEF"
    assert not any(
        namespace == "files" and name == "download"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )


def test_apt_sources_reject_non_gpg_keyring_paths(pyinfra_task_harness):
    """apt.key destinations must match the enforced .gpg output extension."""
    with pytest.raises(ValueError, match="must end in .gpg"):
        pyinfra_task_harness.load("apt.py", {
            "apt_sources": {
                "example": {
                    "key": {
                        "url": "https://example.test/archive-key.asc",
                        "path": "/etc/apt/keyrings/example.asc",
                    },
                    "repository": {
                        "url": "https://example.test/apt",
                        "distribution": "stable",
                    },
                },
            },
        })


def test_proton_drive_cli_reinstalls_when_binary_is_missing(pyinfra_task_harness):
    """A stale version marker cannot hide a missing executable."""
    def get_fact(fact, *args, **kwargs):
        if getattr(fact, "__name__", "") == "File":
            return False
        command = kwargs.get("command", args[0] if args else "")
        if (
            getattr(fact, "__name__", "") == "Command"
            and "proton-drive.version" in command
        ):
            return ["1.2.3"]
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("proton.py", {
        "proton": {
            "mail": False,
            "bridge": False,
            "vpn": False,
            "pass": False,
            "flatpak": False,
            "drive_cli": True,
            "drive_cli_version": "1.2.3",
        },
    })
    assert any(
        namespace == "server" and name == "shell"
        and kwargs.get("name") == "Install Proton Drive CLI"
        for namespace, name, kwargs in pyinfra_task_harness.calls
    )


def test_system_timezone_skips_equivalent_utc_alias(pyinfra_task_harness):
    """Etc/UTC and UTC represent the same zone and must not cause a change."""
    def get_fact(fact, *_args, **_kwargs):
        if getattr(fact, "__name__", "") == "Timezone":
            return "Etc/UTC"
        return []

    pyinfra_task_harness.host.get_fact = get_fact
    pyinfra_task_harness.load("system.py", {
        "locale": "",
        "timezone": "UTC",
    })
    assert not any(
        namespace == "server" and name == "timezone"
        for namespace, name, _kwargs in pyinfra_task_harness.calls
    )
