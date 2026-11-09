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

Target:
    Debian / Ubuntu
"""

import re
from io import StringIO

from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.operations import files, server

# Custom fact: retrieve current system locale
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
