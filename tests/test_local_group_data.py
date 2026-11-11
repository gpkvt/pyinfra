# pylint: disable=W0621, C0123
"""Regression tests for the host-specific ``group_data/@local.py`` data."""

import ipaddress
import runpy
from urllib.parse import urlparse

import pytest

from conftest import ROOT


@pytest.fixture(scope="module")
def local_data():
    """Load local host data as plain Python values without running pyinfra."""
    return runpy.run_path(str(ROOT / "group_data/@local.py"))


def test_required_identity_and_locale_settings_are_non_empty(local_data):
    for key in ("hostname", "timezone", "locale", "username", "usergroup", "homedir"):
        assert isinstance(local_data[key], str)
        assert local_data[key].strip()

    assert local_data["homedir"].startswith("/home/")


def test_keyboard_configuration_has_expected_fields(local_data):
    keyboard = local_data["keyboard"]

    assert {"layout", "model", "variant", "options"} <= keyboard.keys()
    assert all(isinstance(value, str) for value in keyboard.values())


def test_local_network_is_a_valid_network(local_data):
    network = ipaddress.ip_network(local_data["local_network_cidr"], strict=False)

    assert network.num_addresses > 1


def test_hosts_mapping_uses_valid_ip_addresses(local_data):
    hostnames = local_data["hostnames"]

    assert hostnames
    for address, names in hostnames.items():
        ipaddress.ip_address(address)
        assert isinstance(names, str) and names.split()


def test_optional_shell_and_terminal_switches_are_booleans(local_data):
    for key in ("zsh", "powerline", "tmux", "powerline_fonts"):
        assert isinstance(local_data[key], bool)


def test_sysctl_configuration_contains_integer_values(local_data):
    sysctl = local_data["sysctl"]

    assert sysctl
    assert all(isinstance(key, str) and key.startswith(("net.", "vm.")) for key in sysctl)
    assert all(type(value) is int for value in sysctl.values())


def test_udev_rules_have_file_names_and_non_empty_contents(local_data):
    udev = local_data["udev"]

    assert udev
    for filename, contents in udev.items():
        assert filename.endswith(".rules")
        assert isinstance(contents, str) and contents.strip()


def test_usbguard_configuration_is_complete(local_data):
    usbguard = local_data["usbguard"]

    assert isinstance(usbguard["enabled"], bool)
    assert usbguard["implicit_policy"] in {"allow", "block", "reject"}
    assert usbguard["present_device_policy"] in {
        "allow", "block", "reject", "apply-policy", "keep"
    }
    assert usbguard["rules"]
    assert all(rule.startswith(("allow ", "block ", "reject ")) for rule in usbguard["rules"])


def test_sudoers_rules_are_non_empty_strings(local_data):
    rules = local_data["sudoers_rules"]

    assert rules
    assert all(isinstance(rule, str) and rule.strip() for rule in rules)


def test_package_lists_contain_unique_non_empty_package_ids(local_data):
    for key in ("apt_packages", "flatpak_packages"):
        packages = local_data[key]

        assert packages
        assert all(isinstance(package, str) and package.strip() for package in packages)
        assert len(packages) == len(set(packages)), f"duplicate entries in {key}"


def test_apt_sources_have_valid_key_and_repository_definitions(local_data):
    sources = local_data["apt_sources"]

    assert sources
    for name, source in sources.items():
        assert name
        assert {"key", "repository"} <= source.keys()
        assert {"url", "path"} <= source["key"].keys()
        assert {"url", "distribution", "components", "architectures"} <= source["repository"].keys()

        for url in (source["key"]["url"], source["repository"]["url"]):
            assert urlparse(url).scheme == "https"
            assert urlparse(url).netloc

        assert source["key"]["path"].startswith("/")
        assert source["repository"]["components"]
        assert source["repository"]["architectures"]


def test_docker_services_have_valid_ports(local_data):
    docker = local_data["docker"]

    assert docker
    for service, config in docker.items():
        assert service
        port = int(config["port"])
        assert 1 <= port <= 65535


def test_wireguard_interfaces_have_addresses_and_balanced_policy_routes(local_data):
    configurations = local_data["wireguard_config"]

    assert configurations
    for name, config in configurations.items():
        assert name
        interface = config["interface"]
        addresses = interface["Address"].split(",")
        assert addresses
        for address in addresses:
            ipaddress.ip_interface(address.strip())

        assert interface["DNS"]
        assert interface["PostUp"]
        assert interface["PreDown"]
        assert len(interface["PostUp"]) == len(interface["PreDown"])


def test_ssh_keys_have_unique_names_and_supported_key_types(local_data):
    keys = local_data["ssh_keys"]
    names = [key["name"] for key in keys]

    assert keys
    assert len(names) == len(set(names))
    assert all(key["type"] in {"ed25519", "rsa", "ecdsa"} for key in keys)
    assert all(key.get("comment") for key in keys)


def test_mullvad_browser_extensions_have_ids_and_https_downloads(local_data):
    extensions = local_data["mullvad_extensions"]

    assert extensions
    for name, extension in extensions.items():
        assert name
        assert extension["id"]
        parsed_url = urlparse(extension["url"])
        assert parsed_url.scheme == "https"
        assert parsed_url.netloc


def test_cosmic_configuration_has_consistent_enabled_flags(local_data):
    cosmic = local_data["cosmic"]

    assert isinstance(cosmic["enabled"], bool)
    for section in ("appearance", "panel", "dock", "workspaces"):
        assert isinstance(cosmic[section]["enabled"], bool)

    for section in ("panel", "dock"):
        applets = cosmic[section]["applets"]
        assert {"left", "center", "right"} <= applets.keys()
        assert all(isinstance(items, list) for items in applets.values())


def test_cosmic_config_file_paths_are_relative_and_complete(local_data):
    config_files = local_data["cosmic_config_files"]

    assert {"appearance", "panel", "dock"} <= config_files.keys()
    for config in config_files.values():
        assert config["src"].startswith("files/")
        assert config["dest"].startswith(".config/")


def test_ufw_rules_use_supported_actions(local_data):
    assert local_data["ufw"]

    for config in local_data["ufw"].values():
        if isinstance(config, dict):
            assert config["action"] in {"Allow", "Deny", "Reject", "Limit"}
            assert isinstance(config["rule"], str) and config["rule"].strip()
        else:
            assert config in {"Allow", "Deny", "Reject", "Limit"}


def test_zsh_configuration_lists_are_non_empty_and_unique(local_data):
    for key in ("zplug_plugins", "zshrc_imports"):
        values = local_data[key]
        assert values
        assert all(isinstance(value, str) and value.strip() for value in values)
        assert len(values) == len(set(values)), f"duplicate entries in {key}"
