# Homepage icons

The PNG icons in this directory are sourced from [homarr-labs/dashboard-icons](https://github.com/homarr-labs/dashboard-icons), under the Apache License 2.0. They are deployed to Homepage's local public icon directory by `tasks/docker/homepage.py`.

Upstream icon files: `png/<name>.png`. See [LICENSE](LICENSE) for the upstream license text.

## Proton service icons

The Proton bookmarks use service-specific artwork from the official [Proton WebClients repository](https://github.com/ProtonMail/WebClients). Mail, VPN, Drive, Calendar, Meet, and Wallet use each app's `icon-maskable.svg` artwork, with its white mask background removed for Homepage's dark theme. Docs and Sheets use their dedicated document and spreadsheet favicons. Pass and Lumo use their dedicated service artwork. Authenticator uses the dedicated Authenticator logo from `packages/components/containers/account/authenticatorPromotion/assets/authenticator-logo.svg`.

All SVGs are stored locally to avoid external favicon redirects.

## Proton dashboard artwork

The ten Proton bookmark PNGs use the service artwork from the supplied Proton dashboard screenshot. The white rounded-square tiles and the Lumo/Meet “New” badges are excluded. Each transparent PNG uses the same 48×48 canvas and a normalized 36-pixel maximum artwork size for consistent visual scale on Homepage. Authenticator retains its dedicated transparent SVG because it is not shown in the reference.
