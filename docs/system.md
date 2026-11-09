# System configuration

`tasks/system.py` manages operating-system settings from the current target's `host.data`. It is included in every full deployment. The supplied implementation targets Debian/Ubuntu-style system configuration files and Linux system facilities.

## Settings overview

| Setting | Type | Default / behavior | Purpose |
| --- | --- | --- | --- |
| `hostname` | string | No change when absent | System hostname. |
| `timezone` | string | No change when absent | System timezone identifier. |
| `locale` | string or `None` | `en_US.UTF-8` | System-wide UTF-8 locale; `None` skips management. |
| `editor` | string | No change when absent | `EDITOR` environment setting. |
| `visual_editor` | string | Falls back to `editor` | `VISUAL` environment setting. |
| `keyboard` | dictionary | `{}` | XKB keyboard settings; empty disables management. |
| `sysctl` | dictionary | `{}` | Kernel parameters; empty disables management. |
| `udev` | dictionary | `{}` | Rule filename to rule-content mapping. |
| `usbguard` | dictionary | Disabled unless enabled | USB device authorization policy. |

## Hostname and timezone

```python
hostname = "node01"
timezone = "Etc/UTC"
```

The task validates the configured values and uses pyinfra server operations to apply them. Use a valid hostname and a timezone name from the system timezone database.

## Locale

```python
locale = "en_US.UTF-8"
# Set to None to skip locale management.
```

The task checks `/etc/default/locale`, enables the requested locale when necessary, and maintains the `LANG` setting. The configured locale must use UTF-8 encoding. The custom `SystemLocale` fact is used to inspect the current setting.

## Default editors

```python
editor = "vim"
visual_editor = "code --wait"
```

The task maintains `EDITOR` and `VISUAL` in `/etc/environment`. If `visual_editor` is not set, it uses the `editor` value.

## Keyboard layout

```python
keyboard = {
    "layout": "us",
    "model": "pc105",
    "variant": "",
    "options": "",
}
```

Supported fields are `layout`, `model`, `variant` and `options`. Defaults are `us`, `pc105`, empty and empty respectively. The task writes `/etc/default/keyboard`. An empty dictionary disables management; when enabled, layout must not be empty.

## Kernel parameters (sysctl)

```python
sysctl = {
    "net.ipv4.ip_forward": 1,
    "vm.swappiness": 10,
}
```

Each key is a kernel parameter and each value is its desired value. The task validates names and values, applies parameters immediately, and persists them in `/etc/sysctl.d/99-local.conf`.

Accepted values are strings, integers, or non-empty lists of strings/integers. Booleans are rejected even though Python treats them as integers. Empty values and embedded newline/carriage-return characters are rejected. Parameter names must match `[a-zA-Z0-9_.-]+`.

## udev rules

```python
udev = {
    "70-network-name.rules": '''
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="02:00:00:00:00:01", NAME="lan0"
'''
}
```

Each key is a rule filename and each value is the complete rule content. Filenames must begin with a two-digit priority and end in `.rules`, matching `[0-9]{2}-[a-zA-Z0-9_.-]+\.rules`. The task writes rules under `/etc/udev/rules.d/`, sets root ownership and mode `0644`, and reloads udev rules when a file changes. An empty dictionary disables rule management.

## USBGuard

USBGuard applies a policy to USB devices. A restrictive policy can block essential input devices or remote administration hardware; prepare and validate rules before enabling it.

```python
usbguard = {
    "enabled": True,
    "implicit_policy": "block",
    "present_device_policy": "apply-policy",
    "rules": [
        "allow id 1d6b:0002",
        "allow id 1d6b:0003",
        "allow id 1050:0407",
    ],
}
```

The example IDs are illustrative only. Generate and review rules for the actual hardware.

| Parameter | Type | Default | Accepted values / meaning |
| --- | --- | --- | --- |
| `enabled` | boolean | `False` | Install and enable the USBGuard daemon. |
| `implicit_policy` | string | `block` | `allow`, `block` or `reject` for devices without a matching rule. |
| `present_device_policy` | string | `apply-policy` | `allow`, `block`, `reject`, `keep` or `apply-policy`. |
| `rules` | list of strings | `[]` | Explicit authorization rules. Required and non-empty when enabled. |

Rules must begin with `allow`, `block` or `reject` and must not contain embedded newlines or null characters.

The task manages:

| Path | Purpose | Mode |
| --- | --- | --- |
| `/etc/usbguard/` | Configuration directory | `0700` |
| `/etc/usbguard/usbguard-daemon.conf` | Daemon configuration | `0600` |
| `/etc/usbguard/rules.conf` | Device policy | `0600` |

The daemon configuration uses `/etc/usbguard/rules.conf`, the configured implicit/present-device policies, `PresentControllerPolicy=keep`, `InsertedDevicePolicy=apply-policy` and `IPCAllowedUsers=root`. USBGuard is installed through APT. Configuration changes cause the service to be enabled and restarted; otherwise the task ensures it is enabled and running.

### Add a USB device safely

1. Ensure you have a recovery path and that essential keyboard/mouse/controller devices have rules.
2. Inspect devices with `sudo usbguard list-devices`.
3. Temporarily authorize the intended device with `sudo usbguard allow-device <ID>`.
4. Inspect the active policy using `sudo usbguard list-rules`.
5. Add the reviewed rule to `usbguard["rules"]` in the relevant group-data file.
6. Run a dry deployment, then apply and verify.

A runtime permanent authorization does not update the pyinfra source configuration. The next deployment may restore the rules from group data.

Useful commands:

| Command | Purpose |
| --- | --- |
| `sudo usbguard list-devices` | List connected devices. |
| `sudo usbguard list-devices -b` | List blocked devices. |
| `sudo usbguard list-devices -a` | List allowed devices. |
| `sudo usbguard list-rules` | Show active rules. |
| `sudo usbguard generate-policy` | Generate an initial policy from currently connected devices. |
| `sudo usbguard allow-device <ID>` | Temporarily allow a device. |
| `sudo usbguard allow-device -p <ID>` | Persistently allow a device in the runtime policy. |

## Managed system files

| Path | Managed setting |
| --- | --- |
| `/etc/default/locale` | System locale (`LANG`). |
| `/etc/environment` | `EDITOR` and `VISUAL`. |
| `/etc/default/keyboard` | Keyboard layout. |
| `/etc/sysctl.d/99-local.conf` | Persistent kernel parameters. |
| `/etc/udev/rules.d/*.rules` | Custom udev rules. |
| `/etc/usbguard/usbguard-daemon.conf` | USBGuard daemon configuration. |
| `/etc/usbguard/rules.conf` | USBGuard authorization policy. |

Hostname and timezone are managed through pyinfra operations rather than direct file writes.

## Validation and execution

The task validates hostnames, timezone identifiers, UTF-8 locale syntax, editor values, keyboard fields, sysctl keys/values, udev filenames/content, and USBGuard options/rules. Invalid configuration raises `ValueError` during task preparation.

Run only this task for focused testing:

```bash
pyinfra inventory.py tasks/system.py --dry --diff
```

For normal provisioning, use `deploy.py` so shared initialization and task selection are consistent. Always review changes to sysctl, udev and USBGuard carefully before applying them remotely.
