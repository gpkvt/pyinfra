# Changelog

All notable changes to this project are documented in this file.

This project follows a continuous development model.
Changes are tracked as a date timestamp until formal releases are introduced.

## \[09.11.2026\]

### Added

- Introduced modular infrastructure provisioning and configuration using pyinfra.
- Added host-specific configuration through group data files.
- Added configurable host selection and support for local execution.
- Added automated APT and Flatpak package management.
- Added hostname, hosts file, directory, and system configuration management.
- Added WireGuard VPN configuration with automatic activation based on local network detection.
- Added SSH client configuration and UFW firewall management.
- Added Caddy reverse proxy configuration and Let's Encrypt certificate management using dehydrated.
- Added Docker installation and Docker Compose service deployments.
- Added Miniflux and TimeTagger service configurations.
- Added COSMIC desktop environment configuration.
- Added AppArmor profile management.
- Added GPG-encrypted secrets management for credentials and sensitive configuration.
- Added user environment configuration for Zsh, zplug, Powerlevel10k, Powerline, and tmux.
- Added Git configuration and credential management.
- Added reusable deployment tasks, templates, and supporting configuration files.

### Security

- Added encrypted storage for sensitive configuration using GPG.
- Added firewall and AppArmor configuration management.
- Added restricted permissions for sensitive configuration files.
