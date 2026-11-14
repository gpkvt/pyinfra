# pylint: disable=E1101
"""
Manage basic system configuration.

Configuration:
    hostname:
        System hostname.

    timezone:
        System timezone.

    locale:
        System-wide default locale (default: en_US.UTF-8).

    editor:
        Default CLI editor (e.g. mcedit).

    visual_editor:
        Default visual editor (e.g. cosmic-editor).

    keyboard:
        System-wide keyboard layout configuration.

        Supported settings:
            layout: XKB keyboard layout (default: us).
            model: Keyboard model (default: pc105).
            variant: Keyboard variant (default: empty).
            options: Keyboard options (default: empty).

    sysctl:
        Dictionary of Linux kernel parameters.
        Parameters are applied immediately and persisted
        in /etc/sysctl.d/99-local.conf.

    udev:
        Dictionary of udev rules.
        Keys are rule filenames, values are rule contents.

    usbguard:
        USBGuard configuration for controlling USB device access.

        USBGuard provides a default-deny security policy that allows
        only explicitly authorized USB devices. Rules can identify
        devices by vendor/product ID, serial number, device hash,
        parent hash, physical port and USB interface.

        Configuration is managed through host.data:
            enabled:
                Install and enable the USBGuard daemon.
            implicit_policy:
                Default action for devices not matching any rule
                (allow, block or reject). Defaults to block.
            present_device_policy:
                Policy applied to devices already connected when
                USBGuard starts.
            rules:
                List of USBGuard policy rules.

        Rules are persisted in /etc/usbguard/rules.conf and
        daemon settings in /etc/usbguard/usbguard-daemon.conf.
        Changes trigger a USBGuard service restart.

        Adding new USB devices:
            1. Connect the new USB device.
            2. List connected devices:
                   sudo usbguard list-devices
            3. Identify the device ID of the blocked device.
            4. Temporarily authorize the device:
                   sudo usbguard allow-device <ID>
               Or permanently authorize it:
                   sudo usbguard allow-device -p <ID>
            5. Retrieve the generated policy rules:
                   sudo usbguard list-rules
            6. Copy the corresponding allow rule into
               host.data['usbguard']['rules'] in group_data.
            7. Deploy the updated configuration using pyinfra.

        Useful commands:
            List all devices:
                sudo usbguard list-devices

            List blocked devices:
                sudo usbguard list-devices -b

            List allowed devices:
                sudo usbguard list-devices -a

            List active rules:
                sudo usbguard list-rules

            Temporarily allow a device:
                sudo usbguard allow-device <ID>

            Permanently allow a device:
                sudo usbguard allow-device -p <ID>

            Temporarily block a device:
                sudo usbguard block-device <ID>

            Permanently reject a device:
                sudo usbguard reject-device -p <ID>

            Generate initial policy from connected devices:
                sudo usbguard generate-policy

        Important:
            Permanent authorization modifies the active USBGuard
            policy, but pyinfra manages rules.conf as the source
            of truth. Always copy new rules into group_data to
            preserve them across deployments.

            Review generated rules before accepting them.
            USBGuard rules may be tied to physical USB ports
            and parent controllers.

            Ensure keyboards, mice and other essential devices
            are authorized before enabling a default-deny policy.

Target:
    Debian / Ubuntu
"""

import re
from io import StringIO

from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.operations import apt, files, server

# Custom fact: retrieve current system locale
class SystemTimezone(FactBase):
    """Return the configured system timezone."""

    command = (
        "timedatectl show --property=Timezone --value 2>/dev/null "
        "|| cat /etc/timezone 2>/dev/null || true"
    )

    def process(self, output):
        return "".join(output).strip() or None


class SystemLocale(FactBase):
    """
    Return the current LANG setting from /etc/default/locale.
    """

    command = "cat /etc/default/locale 2>/dev/null || true"

    def process(self, output):
        for line in output:
            match = re.match(
                r'^\s*LANG\s*=\s*["\']?([^"\']+)["\']?\s*$',
                line,
            )
            if match:
                return match.group(1)

        return None

# Load configuration
hostname = host.data.get("hostname")
timezone = host.data.get("timezone")
locale = host.data.get("locale", "en_US.UTF-8")

editor = host.data.get("editor")
visual_editor = host.data.get("visual_editor", editor)

keyboard = host.data.get("keyboard", {})

# Configure hostname
if hostname:
    if (
        len(hostname) > 253
        or not re.fullmatch(
            r"(?=.{1,253}\Z)"
            r"[a-zA-Z0-9]"
            r"(?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?",
            hostname,
        )
    ):
        raise ValueError(f"Invalid hostname: {hostname}")

    server.hostname(
        name=f"Set hostname to {hostname}",
        hostname=hostname,
        _sudo=True,
    )

# Configure timezone
if timezone:
    if not re.fullmatch(
        r"[a-zA-Z0-9_+-]+(?:/[a-zA-Z0-9_+-]+)*",
        timezone,
    ):
        raise ValueError(f"Invalid timezone: {timezone}")

    current_timezone = host.get_fact(SystemTimezone)

    if current_timezone != timezone:
        server.timezone(
            name=f"Set timezone to {timezone}",
            timezone=timezone,
            _sudo=True,
        )

# Configure system locale
if locale:
    if not isinstance(locale, str) or not re.fullmatch(
        r"[a-zA-Z0-9_@.-]+",
        locale,
    ):
        raise ValueError(f"Invalid locale: {locale}")

    if not locale.upper().endswith("UTF-8"):
        raise ValueError(
            f"System locale must use UTF-8 encoding: {locale}"
        )

    current_locale = host.get_fact(SystemLocale)

    if current_locale != locale:
        server.locale(
            name=f"Enable locale: {locale}",
            locale=locale,
            present=True,
            _sudo=True,
        )

        files.put(
            name=f"Set system default locale: {locale}",
            src=StringIO(f'LANG="{locale}"\n'),
            dest="/etc/default/locale",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
        )

# Configure default CLI editors
for variable, value in {
    "EDITOR": editor,
    "VISUAL": visual_editor,
}.items():
    if value:
        if not isinstance(value, str) or not re.fullmatch(
            r"[a-zA-Z0-9_.+-]+",
            value,
        ):
            raise ValueError(
                f"Invalid {variable}: {value}"
            )

        files.line(
            name=f"Set default {variable}: {value}",
            path="/etc/environment",
            line=f"{variable}={value}",
        )

# Configure keyboard layout
if keyboard:
    if not isinstance(keyboard, dict):
        raise ValueError(
            "Keyboard configuration must be a dictionary"
        )

    layout = keyboard.get("layout", "us")
    model = keyboard.get("model", "pc105")
    variant = keyboard.get("variant", "")
    options = keyboard.get("options", "")

    for field, value in {
        "layout": layout,
        "model": model,
        "variant": variant,
        "options": options,
    }.items():
        if not isinstance(value, str):
            raise ValueError(
                f"Keyboard {field} must be a string"
            )

        if not re.fullmatch(
            r"[a-zA-Z0-9_,+-]*",
            value,
        ):
            raise ValueError(
                f"Invalid keyboard {field}: {value}"
            )

    if not layout:
        raise ValueError(
            "Keyboard layout cannot be empty"
        )

    keyboard_config = (
        f'XKBMODEL="{model}"\n'
        f'XKBLAYOUT="{layout}"\n'
        f'XKBVARIANT="{variant}"\n'
        f'XKBOPTIONS="{options}"\n'
        'BACKSPACE="guess"\n'
    )

    files.put(
        name=f"Configure keyboard layout: {layout}",
        src=StringIO(keyboard_config),
        dest="/etc/default/keyboard",
        user="root",
        group="root",
        mode="644",
        _sudo=True,
    )

# Configure sysctl parameters
sysctl = host.data.get("sysctl", {})

if sysctl:
    if not isinstance(sysctl, dict):
        raise ValueError(
            "Sysctl configuration must be a dictionary"
        )

    for key, value in sysctl.items():
        # Validate parameter name
        if not isinstance(key, str) or not re.fullmatch(
            r"[a-zA-Z0-9_.-]+",
            key,
        ):
            raise ValueError(
                f"Invalid sysctl parameter: {key}"
            )

        # Validate parameter value
        if isinstance(value, bool):
            raise ValueError(
                f"Invalid sysctl value for {key}: {value}"
            )

        if isinstance(value, (str, int)):
            values = [value]
        elif isinstance(value, list):
            values = value
        else:
            raise ValueError(
                f"Invalid sysctl value type for {key}: "
                f"{type(value).__name__}"
            )

        if not values:
            raise ValueError(
                f"Sysctl value cannot be empty: {key}"
            )

        for item in values:
            if (
                isinstance(item, bool)
                or not isinstance(item, (str, int))
                or not str(item)
                or "\n" in str(item)
                or "\r" in str(item)
            ):
                raise ValueError(
                    f"Invalid sysctl value for {key}: {item}"
                )

        server.sysctl(
            name=f"Configure sysctl: {key}",
            key=key,
            value=value,
            persist=True,
            persist_file="/etc/sysctl.d/99-local.conf",
            _sudo=True,
        )

# Configure udev rules
udev = host.data.get("udev", {})
udev_changed = False

if udev:
    if not isinstance(udev, dict):
        raise ValueError("udev configuration must be a dictionary")

    for filename, content in udev.items():
        if not isinstance(filename, str) or not re.fullmatch(
            r"[0-9]{2}-[a-zA-Z0-9_.-]+\.rules",
            filename,
        ):
            raise ValueError(f"Invalid udev rule filename: {filename}")

        if not isinstance(content, str):
            raise ValueError(
                f"udev rule content must be a string: {filename}"
            )

        result = files.put(
            name=f"Configure udev rules: {filename}",
            src=StringIO(content.rstrip() + "\n"),
            dest=f"/etc/udev/rules.d/{filename}",
            user="root",
            group="root",
            mode="644",
            _sudo=True,
        )

        if result.changed:
            udev_changed = True

    if udev_changed:
        server.shell(
            name="Reload udev rules",
            commands=["udevadm control --reload-rules"],
            _sudo=True,
        )

# Configure USBGuard
usbguard = host.data.get("usbguard", {})

if usbguard:
    print(__doc__)
    if not isinstance(usbguard, dict):
        raise ValueError("USBGuard configuration must be a dictionary")

    enabled = usbguard.get("enabled", False)

    if not isinstance(enabled, bool):
        raise ValueError("USBGuard enabled must be a boolean")

    if enabled:
        rules = usbguard.get("rules", [])
        implicit_policy = usbguard.get("implicit_policy", "block")
        present_device_policy = usbguard.get(
            "present_device_policy",
            "apply-policy",
        )

        if not isinstance(rules, list) or not rules:
            raise ValueError(
                "USBGuard requires an explicit, non-empty rules list"
            )

        if implicit_policy not in ("allow", "block", "reject"):
            raise ValueError(
                f"Invalid USBGuard implicit policy: {implicit_policy}"
            )

        if present_device_policy not in (
            "allow",
            "block",
            "reject",
            "keep",
            "apply-policy",
        ):
            raise ValueError(
                "Invalid USBGuard present device policy: "
                f"{present_device_policy}"
            )

        for rule in rules:
            if (
                not isinstance(rule, str)
                or not re.match(r"^(allow|block|reject)\s", rule)
                or "\n" in rule
                or "\r" in rule
                or "\x00" in rule
            ):
                raise ValueError(
                    f"Invalid USBGuard rule: {rule}"
                )

        # Install USBGuard
        apt.packages(
            name="Install USBGuard",
            packages=["usbguard"],
            present=True,
            _sudo=True,
        )

        # Create USBGuard configuration directory
        files.directory(
            name="Create USBGuard configuration directory",
            path="/etc/usbguard",
            present=True,
            user="root",
            group="root",
            mode="700",
            _sudo=True,
        )

        # Track configuration changes
        usbguard_changed = False

        # Configure USBGuard daemon
        daemon_config = (
            "RuleFile=/etc/usbguard/rules.conf\n"
            f"ImplicitPolicyTarget={implicit_policy}\n"
            f"PresentDevicePolicy={present_device_policy}\n"
            "PresentControllerPolicy=keep\n"
            "InsertedDevicePolicy=apply-policy\n"
            "IPCAllowedUsers=root\n"
        )

        daemon_result = files.put(
            name="Configure USBGuard daemon",
            src=StringIO(daemon_config),
            dest="/etc/usbguard/usbguard-daemon.conf",
            user="root",
            group="root",
            mode="600",
            _sudo=True,
        )

        if daemon_result.changed:
            usbguard_changed = True

        # Configure USBGuard rules
        rules_result = files.put(
            name="Configure USBGuard rules",
            src=StringIO("\n".join(rules) + "\n"),
            dest="/etc/usbguard/rules.conf",
            user="root",
            group="root",
            mode="600",
            _sudo=True,
        )

        if rules_result.changed:
            usbguard_changed = True

        # Enable and restart USBGuard only when necessary
        if usbguard_changed:
            server.shell(
                name="Enable and restart USBGuard",
                commands=[
                    "systemctl enable usbguard",
                    "systemctl restart usbguard",
                ],
                _sudo=True,
            )
        else:
            server.service(
                name="Ensure USBGuard is enabled and running",
                service="usbguard",
                running=True,
                enabled=True,
                _sudo=True,
            )
