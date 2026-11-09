# System Configuration

This document describes `tasks/system.py`, which manages basic operating-system configuration using pyinfra.

## Overview

The system task configures the following settings:

- System hostname
- System timezone
- System-wide locale
- Default command-line editor
- Default visual editor
- System-wide keyboard layout

The task is intended for Debian and Ubuntu systems.

Configuration is read from the current host's `host.data` object, normally populated through `group_data/@local.py`.

## Configuration

The following options can be defined in the host configuration.

| Option | Type | Default | Description |
|---|---|---|---|
| `hostname` | string | None | System hostname |
| `timezone` | string | None | System timezone |
| `locale` | string | `en_US.UTF-8` | System-wide UTF-8 locale |
| `editor` | string | None | Default command-line editor |
| `visual_editor` | string | Value of `editor` | Default visual editor |
| `keyboard` | dictionary | `{}` | Keyboard configuration |

### Hostname

Example:

```python
hostname = "workstation"
```

The hostname is validated before being applied. It must be a valid hostname with a maximum length of 253 characters.

The configuration is applied using pyinfra's `server.hostname` operation.

### Timezone

Example:

```python
timezone = "Europe/Amsterdam"
```

Use a valid timezone identifier from the system timezone database.

The task validates the timezone format and applies it using `server.timezone`.

### Locale

Example:

```python
locale = "en_US.UTF-8"
```

The locale must use UTF-8 encoding.

The task:

1. Reads the current `LANG` setting from `/etc/default/locale`.
2. Checks whether the requested locale is already configured.
3. Enables the locale if necessary.
4. Updates `/etc/default/locale` with the requested `LANG` value.

The locale check is implemented through the custom `SystemLocale` fact.

The default locale is `en_US.UTF-8` when no explicit value is configured. Set `locale = None` to skip locale management.

### Default editors

Example:

```python
editor = "mcedit"
visual_editor = "cosmic-editor"
```

The task configures:

- `EDITOR` for command-line applications.
- `VISUAL` for applications using a visual editor.

If `visual_editor` is not specified, it defaults to the value of `editor`.

Both variables are maintained in `/etc/environment`.

### Keyboard layout

Example:

```python
keyboard = {
    "layout": "de",
    "model": "pc105",
    "variant": "",
    "options": "",
}
```

Supported parameters:

| Parameter | Default | Description |
|---|---|---|
| `layout` | `us` | XKB keyboard layout |
| `model` | `pc105` | Keyboard model |
| `variant` | Empty | Keyboard variant |
| `options` | Empty | Additional XKB options |

The task writes the configuration to `/etc/default/keyboard`.

An empty keyboard dictionary disables keyboard configuration.

The layout must not be empty when keyboard configuration is enabled.

## Validation

The task validates configuration values before generating operations.

- Hostnames must conform to the accepted hostname syntax.
- Timezones must conform to the accepted timezone identifier syntax.
- Locales must use UTF-8 encoding.
- Editor names must contain only supported characters.
- Keyboard settings must be strings containing supported characters.

Invalid configuration raises `ValueError` and stops task preparation.

## System files

The task manages the following files:

| File | Purpose |
|---|---|
| `/etc/default/locale` | System-wide locale |
| `/etc/environment` | Default editor environment variables |
| `/etc/default/keyboard` | XKB keyboard configuration |

The hostname and timezone are managed through pyinfra operations rather than direct file editing.

## Execution

Run the task independently:

```bash
pyinfra inventory.py tasks/system.py --sudo --diff
```

Review the proposed changes before applying them.

For the complete deployment, use:

```bash
pyinfra inventory.py deploy.py --sudo --diff
```

**Note:** `tasks/system.py` is currently not included by `deploy.py`. The independent command above is therefore required until the task is explicitly integrated into the deployment entry point.

## Implementation

The task uses:

- `pyinfra.host` to retrieve host configuration.
- `pyinfra.api.FactBase` to implement `SystemLocale`.
- `pyinfra.operations.server` for hostname, timezone and locale management.
- `pyinfra.operations.files` for configuration file management.

The task is designed to avoid unnecessary locale changes by comparing the requested locale against the current system configuration.



# System Configuration

This document describes `tasks/system.py`, which manages basic operating-system configuration using pyinfra.

## Overview

The system task configures the following settings:

- System hostname
- System timezone
- System-wide locale
- Default command-line editor
- Default visual editor
- System-wide keyboard layout

The task is intended for Debian and Ubuntu systems.

Configuration is read from the current host's `host.data` object, normally populated through `group_data/@local.py`.

## Configuration

The following options can be defined in the host configuration.

| Option | Type | Default | Description |
|---|---|---|---|
| `hostname` | string | None | System hostname |
| `timezone` | string | None | System timezone |
| `locale` | string | `en_US.UTF-8` | System-wide UTF-8 locale |
| `editor` | string | None | Default command-line editor |
| `visual_editor` | string | Value of `editor` | Default visual editor |
| `keyboard` | dictionary | `{}` | Keyboard configuration |

### Hostname

Example:

```python
hostname = "workstation"
```

The hostname is validated before being applied. It must be a valid hostname with a maximum length of 253 characters.

The configuration is applied using pyinfra's `server.hostname` operation.

### Timezone

Example:

```python
timezone = "Europe/Amsterdam"
```

Use a valid timezone identifier from the system timezone database.

The task validates the timezone format and applies it using `server.timezone`.

### Locale

Example:

```python
locale = "en_US.UTF-8"
```

The locale must use UTF-8 encoding.

The task:

1. Reads the current `LANG` setting from `/etc/default/locale`.
2. Checks whether the requested locale is already configured.
3. Enables the locale if necessary.
4. Updates `/etc/default/locale` with the requested `LANG` value.

The locale check is implemented through the custom `SystemLocale` fact.

The default locale is `en_US.UTF-8` when no explicit value is configured. Set `locale = None` to skip locale management.

### Default editors

Example:

```python
editor = "mcedit"
visual_editor = "cosmic-editor"
```

The task configures:

- `EDITOR` for command-line applications.
- `VISUAL` for applications using a visual editor.

If `visual_editor` is not specified, it defaults to the value of `editor`.

Both variables are maintained in `/etc/environment`.

### Keyboard layout

Example:

```python
keyboard = {
    "layout": "de",
    "model": "pc105",
    "variant": "",
    "options": "",
}
```

Supported parameters:

| Parameter | Default | Description |
|---|---|---|
| `layout` | `us` | XKB keyboard layout |
| `model` | `pc105` | Keyboard model |
| `variant` | Empty | Keyboard variant |
| `options` | Empty | Additional XKB options |

The task writes the configuration to `/etc/default/keyboard`.

An empty keyboard dictionary disables keyboard configuration.

The layout must not be empty when keyboard configuration is enabled.

## Validation

The task validates configuration values before generating operations.

- Hostnames must conform to the accepted hostname syntax.
- Timezones must conform to the accepted timezone identifier syntax.
- Locales must use UTF-8 encoding.
- Editor names must contain only supported characters.
- Keyboard settings must be strings containing supported characters.

Invalid configuration raises `ValueError` and stops task preparation.

## System files

The task manages the following files:

| File | Purpose |
|---|---|
| `/etc/default/locale` | System-wide locale |
| `/etc/environment` | Default editor environment variables |
| `/etc/default/keyboard` | XKB keyboard configuration |

The hostname and timezone are managed through pyinfra operations rather than direct file editing.

## Execution

Run the task independently:

```bash
pyinfra inventory.py tasks/system.py --sudo --diff
```

Review the proposed changes before applying them.

For the complete deployment, use:

```bash
pyinfra inventory.py deploy.py --sudo --diff
```

**Note:** `tasks/system.py` is currently not included by `deploy.py`. The independent command above is therefore required until the task is explicitly integrated into the deployment entry point.

## Implementation

The task uses:

- `pyinfra.host` to retrieve host configuration.
- `pyinfra.api.FactBase` to implement `SystemLocale`.
- `pyinfra.operations.server` for hostname, timezone and locale management.
- `pyinfra.operations.files` for configuration file management.

The task is designed to avoid unnecessary locale changes by comparing the requested locale against the current system configuration.

## udev rules

Custom udev rules can be managed through the `udev` dictionary in the host configuration.

Each dictionary key represents a rule filename, and its value contains the complete udev rule configuration.

Example:

python

```python
udev = {
    "70-persistent-net.rules": """
# Rename wireless interface to wlan0
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="04:7b:cb:cf:36:78", NAME="wlan0"
"""
}
```

The task:

1. Validates the rule filenames. They must start with a two-digit priority followed by a hyphen and end in `.rules`.
2. Validates that rule contents are strings.
3. Writes the rules to `/etc/udev/rules.d/`.
4. Sets ownership to `root:root` and permissions to `644`.
5. Reloads udev rules using `udevadm control --reload-rules` if any rule file changes.

Rule filenames must match the following pattern:

text

```text
[0-9]{2}-[a-zA-Z0-9_.-]+.rules
```

An empty `udev` dictionary disables udev rule management.

## USBGuard

[USBGuard](<https://usbguard.github.io/>) provides USB device access control using a configurable authorization policy.

The system task can install and configure USBGuard, manage its daemon settings, and maintain a persistent list of authorized devices.

Configuration is controlled through the `usbguard` dictionary.

Example:

python

```python
usbguard = {
    "enabled": True,
    "implicit_policy": "block",
    "present_device_policy": "apply-policy",

    "rules": [
        # USB host controllers
        'allow id 1d6b:0002',
        'allow id 1d6b:0003',

        # YubiKey
        'allow id 1050:0407',
    ],
}
```

The example rules are illustrative. Production configurations should use appropriately specific rules generated for the actual hardware.

### Configuration parameters

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | boolean | `False` | Install and enable the USBGuard daemon |
| `implicit_policy` | string | `block` | Default action for devices without a matching rule |
| `present_device_policy` | string | `apply-policy` | Policy applied to devices already connected when USBGuard starts |
| `rules` | list | `[]` | USBGuard authorization policy rules |

Supported `implicit_policy` values:

- `allow` – allow devices without matching rules.
- `block` – block devices without matching rules.
- `reject` – reject devices without matching rules.

Supported `present_device_policy` values:

- `allow`
- `block`
- `reject`
- `keep`
- `apply-policy`

When USBGuard is enabled, an explicit, non-empty rules list is mandatory. Rules must be strings beginning with `allow`, `block`, or `reject`, with no embedded newlines or null characters.

### Managed configuration files

The task manages the following files:

| File | Purpose | Permissions |
| --- | --- | --- |
| `/etc/usbguard/usbguard-daemon.conf` | USBGuard daemon configuration | `600` |
| `/etc/usbguard/rules.conf` | USB device authorization rules | `600` |

The `/etc/usbguard` directory is owned by `root:root` with permissions `700`.

The daemon configuration includes:

- `RuleFile=/etc/usbguard/rules.conf`
- `ImplicitPolicyTarget` from the host configuration.
- `PresentDevicePolicy` from the host configuration.
- `PresentControllerPolicy=keep`.
- `InsertedDevicePolicy=apply-policy`.
- `IPCAllowedUsers=root`.

The task installs the `usbguard` APT package, writes both configuration files, and enables and restarts the service when configuration changes. Otherwise, it ensures that the service remains enabled and running.

### Adding new USB devices

When a new USB device needs to be authorized:

1. Connect the USB device.
2. List connected devices:bash
   ```bash
   sudo usbguard list-devices
   ```
3. Identify the device ID of the blocked device.
4. Temporarily authorize the device:bash
   ```bash
   sudo usbguard allow-device <ID>
   ```
   Alternatively, permanently authorize it:
   bash
   ```bash
   sudo usbguard allow-device -p <ID>
   ```
5. Retrieve the generated policy rules:bash
   ```bash
   sudo usbguard list-rules
   ```
6. Copy the corresponding authorization rule into `host.data['usbguard']['rules']` in `group_data/@local.py`.
7. Deploy the updated configuration using pyinfra.

**Important:** Permanent authorization modifies the active USBGuard policy, but pyinfra manages `/etc/usbguard/rules.conf` as the source of truth. Always copy new rules into the host configuration to preserve them across deployments.

Review generated rules before accepting them. USBGuard rules can depend on physical USB ports, parent controllers, device hashes and interface characteristics.

Ensure that keyboards, mice and other essential devices are authorized before enabling a default-deny policy.

### Useful USBGuard commands

| Command | Purpose |
| --- | --- |
| `sudo usbguard list-devices` | List connected USB devices |
| `sudo usbguard list-devices -b` | List blocked devices |
| `sudo usbguard list-devices -a` | List allowed devices |
| `sudo usbguard list-rules` | List active policy rules |
| `sudo usbguard allow-device <ID>` | Temporarily allow a device |
| `sudo usbguard allow-device -p <ID>` | Permanently allow a device |
| `sudo usbguard block-device <ID>` | Temporarily block a device |
| `sudo usbguard reject-device -p <ID>` | Permanently reject a device |
| `sudo usbguard generate-policy` | Generate an initial policy from connected devices |
