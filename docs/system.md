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
