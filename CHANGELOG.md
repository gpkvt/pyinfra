# Changelog

All notable changes to this project are documented in this file.

This project follows a continuous development model.
Changes are tracked as a date timestamp until formal releases are introduced.

## [10.11.2026]

### Added

- Added a script to temporarily disable the keyboard for 60 seconds.
- Added Chromecast and DLNA firewall rules.
- Added task and module docstrings to improve documentation and discoverability.
- Added an opt-in workstation role with separate configuration for backup, power management, hardware, storage, peripherals, desktop utilities, and maintenance ([#4](https://github.com/gpkvt/pyinfra/pull/4)).
- Added workstation backup tooling (Restic, Borg, Borgmatic, and rsync) and a configurable Borgmatic template with exclusion and retention settings ([#4](https://github.com/gpkvt/pyinfra/pull/4)).

### Changed

- Improved APT repository handling, including automatic source renewal when repository configuration changes.
- Improved SSH key handling and generation.
- Improved documentation for deployment, system configuration, secrets, udev, and USBGuard.
- Consolidated configured APT and Flatpak application installation into batch operations instead of creating one operation per package ([#4](https://github.com/gpkvt/pyinfra/pull/4)).

### Documentation

- Added usage instructions for udev and USBGuard.
- Added contribution guidelines and a security policy.
- Improved the README and deployment documentation.
- Reworked the README and expanded the task, system, and template documentation ([#1](https://github.com/gpkvt/pyinfra/pull/1), [#3](https://github.com/gpkvt/pyinfra/pull/3)).

### Fixed

- Separated Docker container-specific deployment from the main Docker setup and added it to the deployment entry point ([#4](https://github.com/gpkvt/pyinfra/pull/4)). This avoids the multiple execution of deployment steps.

## [09.11.2026]

### Added

- Added automated APT package management and support for additional APT repositories and signing keys.
- Added Flatpak package and runtime management, including detection and removal of unused packages.
- Added COSMIC desktop panel and dock applet configuration.
- Added font deployment with optional Powerline font download and installation.
- Added SSH key management, including generation and deployment.
- Added system configuration management for hostname, timezone, keyboard layout, locale, and default editor.
- Added sudoers configuration.
- Added sysctl configuration options.
- Added udev rule management and USBGuard configuration for USB device access control.
- Added VSCodium extension installation.
- Added support for Waydroid, Synaptics, and WineHQ APT repositories.
- Added Mullvad browser extensions.

### Changed

- Replaced the keyboard-disabling Python script with a Bash implementation.
- Improved Chromecast and DLNA firewall rules.
- Improved detection of unused Flatpak packages and runtimes.
- Updated the Flatpak package list.

### Fixed

- Pull new docker images before systemd start, to avoid timeouts
- Fixed APT repository signing key formats.
- Fixed missing imports and errors occurring during dry-run execution.
- Fixed an incorrect applet ID in the COSMIC configuration.
- Fixed an incorrect parameter in the deployment documentation.
- Fixed various code quality and linting issues.

### Removed

- Removed automatic APT unused-package cleanup because it could report changes on every run due to the lack of dry-run support.

### Documentation

- Added deployment and system configuration documentation.
- Added information about secrets and SSH keys.
