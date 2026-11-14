# Changelog

All notable changes to this project are documented in this file.

This project follows a continuous development model. Changes are tracked using date-based entries until formal releases are introduced.

## [14.11.2026]

### Added

- Added a Paperless consume-directory link at `~/Paperless` ([#214](https://github.com/gpkvt/pyinfra/pull/214)).
- Added LiMusic AppImage deployment with checksum verification, an application icon and a COSMIC launcher ([#196](https://github.com/gpkvt/pyinfra/pull/196), [#197](https://github.com/gpkvt/pyinfra/pull/197)).
- Added LiMusic now-playing metadata integration for HyFetch ([#209](https://github.com/gpkvt/pyinfra/pull/209), [#210](https://github.com/gpkvt/pyinfra/pull/210), [#211](https://github.com/gpkvt/pyinfra/pull/211)).
- Added configurable cron jobs ([#187](https://github.com/gpkvt/pyinfra/pull/187)).

### Changed

- Changed Sablier's default idle strategy to pause containers ([#256](https://github.com/gpkvt/pyinfra/pull/256)).
- Changed cron deployment so removal-only changes do not start or restart the cron daemon ([#255](https://github.com/gpkvt/pyinfra/pull/255)).
- Changed `hostnames` configuration to use lists; an empty list removes that IP's `/etc/hosts` entries ([#285](https://github.com/gpkvt/pyinfra/issues/285)).
- Expanded COSMIC applet configuration and adjusted configuration-directory handling; expanded Docker application-service configuration ([#241](https://github.com/gpkvt/pyinfra/pull/241), [#251](https://github.com/gpkvt/pyinfra/pull/251), [#253](https://github.com/gpkvt/pyinfra/pull/253), [#254](https://github.com/gpkvt/pyinfra/pull/254)).

### Fixed

- Fixed Samba systemd state checks to use pyinfra's `Command` fact and normalize its line-based output ([#264](https://github.com/gpkvt/pyinfra/issues/264)).
- Fixed fact-output handling and deployment idempotency across multiple tasks, including Docker, Caddy, Proton, LiMusic, Sablier and Syncthing ([#219](https://github.com/gpkvt/pyinfra/pull/219)).
- Corrected `runas` shell argument handling, X11 cleanup, Mullvad Browser configuration and privileged script links ([#223](https://github.com/gpkvt/pyinfra/pull/223), [#224](https://github.com/gpkvt/pyinfra/pull/224), [#225](https://github.com/gpkvt/pyinfra/pull/225)).
- Added validation for APT signing keys and sources, WireGuard, UFW, Docker power-save configuration and SSH key pairs ([#226](https://github.com/gpkvt/pyinfra/pull/226), [#227](https://github.com/gpkvt/pyinfra/pull/227), [#230](https://github.com/gpkvt/pyinfra/pull/230), [#231](https://github.com/gpkvt/pyinfra/pull/231), [#235](https://github.com/gpkvt/pyinfra/pull/235), [#242](https://github.com/gpkvt/pyinfra/pull/242), [#243](https://github.com/gpkvt/pyinfra/pull/243), [#249](https://github.com/gpkvt/pyinfra/pull/249), [#250](https://github.com/gpkvt/pyinfra/pull/250)).
- Corrected Git credential file attributes, sudoers metadata, Flatpak update error handling, USBGuard restart behavior and Dehydrated certificate-expiry handling ([#228](https://github.com/gpkvt/pyinfra/pull/228), [#229](https://github.com/gpkvt/pyinfra/pull/229), [#232](https://github.com/gpkvt/pyinfra/pull/232), [#233](https://github.com/gpkvt/pyinfra/pull/233), [#252](https://github.com/gpkvt/pyinfra/pull/252)).
- Fixed COSMIC applet configuration formatting and newline handling, Docker battery-stop retry behavior and configuration-directory creation ([#241](https://github.com/gpkvt/pyinfra/pull/241), [#251](https://github.com/gpkvt/pyinfra/pull/251)).

### Documentation

- Updated group-data examples and deployment documentation, including COSMIC, SSH, UFW and Sablier guidance ([#221](https://github.com/gpkvt/pyinfra/pull/221), [#236](https://github.com/gpkvt/pyinfra/pull/236), [#238](https://github.com/gpkvt/pyinfra/pull/238), [#239](https://github.com/gpkvt/pyinfra/pull/239), [#247](https://github.com/gpkvt/pyinfra/pull/247)).
## [13.11.2026]

### Added

- Added the AppFlowy Self-Hosted Commercial Docker Compose deployment with PostgreSQL, MinIO and Search host bind mounts, encrypted credentials, loopback-only Nginx publishing, Caddy/Sablier integration and a basic Homepage link.

### Changed

- Changed COSMIC workstation settings to use the nested configuration structure and expanded configurable appearance, input and keyboard-shortcut settings ([#207](https://github.com/gpkvt/pyinfra/pull/207), [#208](https://github.com/gpkvt/pyinfra/pull/208), [#212](https://github.com/gpkvt/pyinfra/pull/212)).
- Changed Flatpak installation to use the user scope, prefer Flathub and manage required runtimes ([#198](https://github.com/gpkvt/pyinfra/pull/198), [#199](https://github.com/gpkvt/pyinfra/pull/199), [#200](https://github.com/gpkvt/pyinfra/pull/200), [#201](https://github.com/gpkvt/pyinfra/pull/201), [#202](https://github.com/gpkvt/pyinfra/pull/202), [#203](https://github.com/gpkvt/pyinfra/pull/203)).
- Increased the default Sablier inactivity duration from 10 to 30 minutes ([#188](https://github.com/gpkvt/pyinfra/pull/188)).

### Fixed

- Improved AppFlowy first-deployment handling and corrected Docker, Redis, Sablier and Caddy integration issues ([#159](https://github.com/gpkvt/pyinfra/pull/159), [#160](https://github.com/gpkvt/pyinfra/pull/160), [#161](https://github.com/gpkvt/pyinfra/pull/161), [#181](https://github.com/gpkvt/pyinfra/pull/181), [#182](https://github.com/gpkvt/pyinfra/pull/182), [#183](https://github.com/gpkvt/pyinfra/pull/183)).
- Corrected Linkwarden API handling and improved manual synchronization, collection grouping, filtering and favicon handling ([#162](https://github.com/gpkvt/pyinfra/pull/162), [#164](https://github.com/gpkvt/pyinfra/pull/164), [#165](https://github.com/gpkvt/pyinfra/pull/165), [#175](https://github.com/gpkvt/pyinfra/pull/175), [#178](https://github.com/gpkvt/pyinfra/pull/178), [#186](https://github.com/gpkvt/pyinfra/pull/186), [#193](https://github.com/gpkvt/pyinfra/pull/193), [#194](https://github.com/gpkvt/pyinfra/pull/194)).
- Corrected Docker systemd handling, LiMusic locale metadata and Homepage integration; added no-op detection to avoid unnecessary deployment operations ([#166](https://github.com/gpkvt/pyinfra/pull/166), [#180](https://github.com/gpkvt/pyinfra/pull/180)).

### Tests

- Expanded automated checks and behavioral coverage for the recent deployment changes ([#189](https://github.com/gpkvt/pyinfra/pull/189), [#190](https://github.com/gpkvt/pyinfra/pull/190), [#191](https://github.com/gpkvt/pyinfra/pull/191), [#192](https://github.com/gpkvt/pyinfra/pull/192)).


## [12.11.2026]

### Added

- Added Docker-based Caddy and Sablier deployment. Sablier uses the Docker provider and Compose labels to start application containers on demand; Caddy uses host networking to retain loopback upstreams.
- Added Dehydrated certificate renewal inside the Caddy container with the Hetzner DNS-01 hook. `dehydrated_domains` in `group_data/@local.py` supports multiple certificates, each defined by one list of primary name and SANs.
- Added Snipe-IT asset management with MariaDB, persistent host bind mounts under `~/.docker/snipe-it/`, encrypted application/database credentials, loopback publishing, Caddy reverse proxy and Homepage integration.
- Added custom Homepage API widgets for supported services and an RSS feed widget.
- Added on-demand Docker service startup with Sablier, including Homepage integration and dynamic loading pages.

### Changed

- Configured Homepage API requests to bypass Sablier so dashboard widgets remain available without starting application containers.
- Set Caddy's HTTP response deadline to two minutes.

### Fixed

- Made Sablier Compose service ordering deterministic.
- Corrected Caddy/Sablier route handler ordering and preserved response headers.
- Improved Docker and Caddy systemd execution under the configured user, including no-op detection to avoid unnecessary operations.
- Fixed Docker deployment and repository-check regressions.
- Added Sablier labels for configured Compose dependencies so they start with applications and can stop with the same session group.
- Removed overlapping certificate renewal during deployment, added Caddy container health checks, and kept Caddy state in explicit host bind mounts below `~/.docker/caddy/`.
- Replaced the broken in-container cron setup with an idempotently deployed user systemd timer that runs Dehydrated daily at 03:00.
- Created Dehydrated's configured `conf.d` directory in the Caddy image and fixed the Hetzner hook's handling of textual exit-hook arguments.
- Fixed Caddy deployment change detection so unchanged renewal, image-build, container-start and health-check operations are skipped.

## [11.11.2026]

### Added

- Added Firefly III with MariaDB, scheduled maintenance, and the FinTS importer; application, database and importer configuration persist under `~/.docker/firefly-iii/` with Caddy routes for both web interfaces.
- Added Paperless-ngx with PostgreSQL, Valkey, Gotenberg and Tika, persistent host-directory mounts under `~/.docker/paperless/`, and the `paperless.21x9.org` Caddy reverse-proxy route.
- Added the WG-Easy Docker service with persistent WireGuard configuration under `~/.docker/wg-easy/`, loopback-only administration UI publishing and Caddy reverse proxy integration.
- Expanded Homepage bookmarks with personal links grouped into Misc, Social, Entertainment and Proton categories, including locally stored service icons.
- Added local Homepage icon assets and idempotent synchronization to the dashboard's public icon directory.
- Added Homepage widgets for Miniflux, Forgejo and Portainer, with API credentials sourced from encrypted secrets ([#67](https://github.com/gpkvt/pyinfra/pull/67), [#68](https://github.com/gpkvt/pyinfra/pull/68), [#73](https://github.com/gpkvt/pyinfra/pull/73)).
- Added the OpenWeatherMap widget with configurable API key and location ([#77](https://github.com/gpkvt/pyinfra/pull/77)).

### Changed

- Centralized Docker-to-host UFW rules in the local host configuration ([#75](https://github.com/gpkvt/pyinfra/pull/75)).
- Updated Homepage Docker networking to support HTTPS access to host-based services ([#74](https://github.com/gpkvt/pyinfra/pull/74)).
- Changed the Homepage weather location to Cologne, Germany ([#80](https://github.com/gpkvt/pyinfra/pull/80)).

### Fixed

- Corrected the Mullvad configuration structure ([#78](https://github.com/gpkvt/pyinfra/pull/78)).
- Fixed a missing host import in the Homepage task ([#79](https://github.com/gpkvt/pyinfra/pull/79)).
- Aligned Homepage icon directory and file permissions with the running container, preventing repeated permission changes on subsequent deployments.

### Documentation

- Expanded Homepage documentation for service bookmarks, Proton links, widgets, local icon assets and change-triggered container restarts.
- Documented the WG-Easy v15 deployment, storage and reverse-proxy setup.

## [10.11.2026]

### Added

- Added Linkwarden with PostgreSQL and Meilisearch, persistent Docker volumes under `~/.docker/linkwarden/`, configurable credentials, loopback publishing and Caddy integration.
- Added shared and per-host secret scopes with recursive host-over-shared merging, while retaining support for the legacy flat secrets format.
- Added the VS Code GPG Vault extension for file and selection encryption/decryption, including a keyboard shortcut to toggle file encryption ([#21](https://github.com/gpkvt/pyinfra/pull/21)).
- Added VPN task integration with the Zsh configuration workflow ([#19](https://github.com/gpkvt/pyinfra/pull/19)).
- Added the `gpg-vault` command-line helper for creating, editing, viewing, encrypting, decrypting and rekeying the GPG-encrypted secrets file. The helper is deployed with the user scripts and does not replace deployment-time secret loading ([#13](https://github.com/gpkvt/pyinfra/pull/13)).
- Added a `uv` project configuration with a Python 3.12 development environment and a development dependency group for pytest, coverage, pre-commit and deptry ([#15](https://github.com/gpkvt/pyinfra/pull/15)).
- Added Docker services for Forgejo, Portainer, TasmoAdmin, Wallabag and Vaultwarden, including persistent storage, local hostnames and Caddy reverse proxy integration ([#31](https://github.com/gpkvt/pyinfra/pull/31), [#34](https://github.com/gpkvt/pyinfra/pull/34), [#36](https://github.com/gpkvt/pyinfra/pull/36), [#39](https://github.com/gpkvt/pyinfra/pull/39), [#41](https://github.com/gpkvt/pyinfra/pull/41)).
- Added a script to temporarily disable the keyboard for 60 seconds.
- Added Chromecast and DLNA firewall rules.
- Added task and module docstrings to improve documentation and discoverability.
- Added an opt-in workstation role with separate configuration for backup, power management, hardware, storage, peripherals, desktop utilities, and maintenance ([#4](https://github.com/gpkvt/pyinfra/pull/4)).
- Added workstation backup tooling (Restic, Borg, Borgmatic, and rsync) and a configurable Borgmatic template with exclusion and retention settings ([#4](https://github.com/gpkvt/pyinfra/pull/4)).

### Changed

- Updated the Docker service storage layout to use persistent volume directories and corrected service-specific volume mappings, including Wallabag and TimeTagger ([#42](https://github.com/gpkvt/pyinfra/pull/42), [#43](https://github.com/gpkvt/pyinfra/pull/43), [#47](https://github.com/gpkvt/pyinfra/pull/47)).
- Replaced Wallabag bind-mounted application storage with Docker-managed named volumes to resolve SQLite permission problems; existing data requires manual migration ([#40](https://github.com/gpkvt/pyinfra/pull/40)).
- Corrected TasmoAdmin's persistent data directory and container mount path ([#37](https://github.com/gpkvt/pyinfra/pull/37), [#38](https://github.com/gpkvt/pyinfra/pull/38)).
- Updated Forgejo SSH configuration and local hostname handling ([#32](https://github.com/gpkvt/pyinfra/pull/32), [#33](https://github.com/gpkvt/pyinfra/pull/33)).
- Updated the Miniflux local hostname configuration ([#35](https://github.com/gpkvt/pyinfra/pull/35)).
- Switched GPG Vault encryption output to ASCII-armored format while retaining compatibility with existing binary ciphertext ([#45](https://github.com/gpkvt/pyinfra/pull/45)).
- Corrected the UFW active-state fact handling ([#20](https://github.com/gpkvt/pyinfra/pull/20)).
- Added JSON linting to the configured development checks ([#22](https://github.com/gpkvt/pyinfra/pull/22)).
- Updated the VS Code GPG Vault workflow to replace existing destination files without prompting and remove plaintext after successful encryption.
- Updated the pinned pip dependency from 24.0 to 26.2 ([#16](https://github.com/gpkvt/pyinfra/pull/16)).
- Improved APT repository handling, including automatic source renewal when repository configuration changes.
- Improved SSH key handling and generation.
- Improved documentation for deployment, system configuration, secrets, udev and USBGuard.
- Consolidated configured APT and Flatpak application installation into batch operations instead of creating one operation per package ([#4](https://github.com/gpkvt/pyinfra/pull/4)).

### Security

- Restricted the deployed Borgmatic configuration file permissions from `0644` to `0600`, limiting access to the root-owned file ([#17](https://github.com/gpkvt/pyinfra/pull/17)).

### Tests

- Added coverage for host isolation, nested secret merging, legacy compatibility, and invalid secrets documents.

### Documentation

- Expanded deployment and task documentation to cover Docker service dispatch, UFW rules and remote lockout risk, mocked pytest coverage and its GitHub Actions workflow, and the Borgmatic template's fallback-passphrase warning ([#14](https://github.com/gpkvt/pyinfra/pull/14)).
- Documented the `gpg-vault` workflow, its commands, deployment, and security considerations ([#13](https://github.com/gpkvt/pyinfra/pull/13)).
- Improved the Docker task reference, clarified service-specific configuration and storage behavior, and documented volume migration considerations ([#46](https://github.com/gpkvt/pyinfra/pull/46), [#48](https://github.com/gpkvt/pyinfra/pull/48)).
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

- Pull Docker images before starting systemd services to prevent startup timeouts.
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
