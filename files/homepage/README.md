# Homepage icons

The PNG icons in this directory are sourced from [homarr-labs/dashboard-icons](https://github.com/homarr-labs/dashboard-icons), under the Apache License 2.0. They are deployed to Homepage's local public icon directory by `tasks/docker/homepage.py`.

Upstream icon files: `png/<name>.png`. See [LICENSE](LICENSE) for the upstream license text.

## Proton service icons

The Proton service SVGs are copied from the official [Proton WebClients repository](https://github.com/ProtonMail/WebClients), under the repository's license. They are stored locally so Homepage does not depend on external favicon redirects.

Source paths: `applications/mail/src/favicon.svg`, `applications/calendar/src/favicon.svg`, `applications/drive/src/favicon.svg`, `applications/docs/src/favicon.svg`, `applications/docs/src/app/hooks/sheets-favicon.svg`, `applications/vpn-settings/src/favicon.svg`, `applications/pass/src/favicon.svg`, `applications/wallet/src/favicon.svg`, `applications/meet/src/favicon.svg`, and `applications/lumo/src/favicon.svg`.

The Proton Authenticator bookmark retains the generic Proton logo because the upstream WebClients repository does not currently provide a dedicated Authenticator favicon.
