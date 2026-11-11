# pylint: disable=C0103, C0301, C0302
"""
Define host-specific configuration for pyinfra system provisioning.

This module contains the configuration options consumed by the deployment tasks. It centralizes system settings, network configuration, application preferences, service definitions, and user environment customization.

Configuration sections: General: Defines the primary user, group, and home directory.

Network:
    Configures local network identification, WireGuard interfaces,
    and hostname mappings.

User environment:
    Controls optional shell, terminal, and powerline configuration.

Docker:
    Defines containerized applications and their deployment options.

APT packages:
    Lists system packages to install and maintain.

Flatpak packages:
    Lists Flatpak applications to install and maintain.

WireGuard:
    Defines VPN interface and peer configurations.

Firewall:
    Controls application-specific firewall policies.

Caddy:
    Defines reverse proxy and TLS configuration.

SSH:
    Defines SSH client connection settings and host-specific options.

Zsh plugins:
    Defines plugins and themes managed through zplug.

Zsh configuration:
    Defines additional configuration modules imported by `.zshrc`.

Notes:

- This module contains configuration data only; provisioning
  is handled by the corresponding pyinfra task modules.
- Optional features and services are controlled through
  configuration options.
- Sensitive credentials and private keys are maintained
  separately in the encrypted secrets configuration.
- Default values for optional settings are determined
  by the consuming deployment modules.

"""

# General settings
hostname="chao"
timezone = "Europe/Amsterdam"
locale = "en_US.UTF-8"
keyboard = {
    "layout": "de",
    "model": "pc105",
    "variant": "",
    "options": "",
}

username="gpkvt"
usergroup="gpkvt"
homedir="/home/gpkvt"

local_network_cidr="192.168.42.0/24"
wireguard_interface="home"
editor = "mcedit"

# Configure /etc/hosts
hostnames = {
  "127.0.0.1": "localhost local.21x9.org rss.21x9.org timetagger.21x9.org grav.21x9.org forgejo.21x9.org portainer.21x9.org tasmoadmin.21x9.org wallabag.21x9.org vaultwarden.21x9.org nocodb.21x9.org homepage.21x9.org linkwarden.21x9.org",
  "::1": "localhost local.21x9.org",
  "192.168.42.100": "storage.intern.21x9.org paperless.intern.21x9.org huginn.intern.21x9.org grafana.intern.21x9.org ha.intern.21x9.org",
  "192.168.42.120": "storage.21x9.org",
}

# Install and configure certain tools
zsh=True
powerline=True
tmux=True
powerline_fonts=False

# Configure Linux kernel parameters
sysctl = {
    # Network security
    "net.ipv4.conf.all.accept_redirects": 0,
    "net.ipv4.conf.default.accept_redirects": 0,
    "net.ipv4.conf.all.send_redirects": 0,
    "net.ipv4.conf.default.send_redirects": 0,
    "net.ipv4.conf.all.rp_filter": 1,
    "net.ipv4.conf.default.rp_filter": 1,

    # Network performance
    "net.core.somaxconn": 4096,
    "net.ipv4.tcp_syncookies": 1,

    # Virtual memory
    "vm.swappiness": 10,
    "vm.vfs_cache_pressure": 50,
}

# Configure udev-rules
udev = {
    "70-persistent-net.rules": """
# Rename wireless interface to wlan0
SUBSYSTEM=="net", ACTION=="add", ATTR{address}=="04:7b:cb:cf:36:78", NAME="wlan0"
"""
}

# Configure usbguard settings
usbguard = {
    "enabled": True,
    "implicit_policy": "block",
    "present_device_policy": "apply-policy",

    "rules": [
        'allow id 1d6b:0002 serial "0000:c3:00.3" name "xHCI Host Controller" hash "oSRBqitQDOgWuBAedOGgTHiwDU//ZY3Hg/EJsQfNmvM=" parent-hash "4sAqQt5FsutFyX4rDQ1yFTjAHHAeMK6KD463NF715x4=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0003 serial "0000:c3:00.3" name "xHCI Host Controller" hash "yk4omAkIgm8hhcOiCo1YDe3mTaXCcxEIrpW0uIoamd0=" parent-hash "4sAqQt5FsutFyX4rDQ1yFTjAHHAeMK6KD463NF715x4=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0002 serial "0000:c3:00.4" name "xHCI Host Controller" hash "ytflbcUR58vOaTlsVdDp+prbapFyL+b4z2vdOAgegjM=" parent-hash "+BCvwJFFwr5wyAlCR01CLcEp66YhBBNkDpteHETXrOA=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0003 serial "0000:c3:00.4" name "xHCI Host Controller" hash "8LvDdXu4NWbVU1Eh+I9LUc9dxnpFqnSPUFWXpeUyPtc=" parent-hash "+BCvwJFFwr5wyAlCR01CLcEp66YhBBNkDpteHETXrOA=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0002 serial "0000:c5:00.3" name "xHCI Host Controller" hash "D5ys1blyYvBmYW/bdzM/Emm6DmXOYav1EoN/dGmYOb0=" parent-hash "HhVwqoJetqwYAPUeWRYVBX7iAJ1TXmZMuzXfAaBpUTk=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0003 serial "0000:c5:00.3" name "xHCI Host Controller" hash "ZyfxD6UHCCiSh9iEjdyauzHXhemCaGupxLgcBj3pWks=" parent-hash "HhVwqoJetqwYAPUeWRYVBX7iAJ1TXmZMuzXfAaBpUTk=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0002 serial "0000:c5:00.4" name "xHCI Host Controller" hash "PIhMg/EQ6L9eag7K2Sr54qcQV7CuvgRRj8l8sSKi5ZY=" parent-hash "+fcV1hCPZJah+gDkMEtWVVjyjL+PGsIF1708cD0hIaM=" with-interface 09:00:00 with-connect-type ""',

        'allow id 1d6b:0003 serial "0000:c5:00.4" name "xHCI Host Controller" hash "KO1NQ7RUKlHxfOoXihmS1c3W/qdBBGVulR+zAZ0uOB4=" parent-hash "+fcV1hCPZJah+gDkMEtWVVjyjL+PGsIF1708cD0hIaM=" with-interface 09:00:00 with-connect-type ""',

        # YubiKey OTP + FIDO + CCID
        'allow id 1050:0407 serial "" name "YubiKey OTP+FIDO+CCID" hash "Q+A8QQReKclmBSaDIYja0w4Bx6ld2IU6wF7HFKdtJ3Q=" parent-hash "oSRBqitQDOgWuBAedOGgTHiwDU//ZY3Hg/EJsQfNmvM=" via-port "1-2" with-interface { 03:01:01 03:00:00 0b:00:00 } with-connect-type "hotplug"',

        # USB 2.0 Hub
        'allow id 05e3:0610 serial "" name "USB2.0 Hub" hash "p0xurg8ayXbgrHAmFBL5BElzY8M/rvDA/w3li6d/wtw=" parent-hash "oSRBqitQDOgWuBAedOGgTHiwDU//ZY3Hg/EJsQfNmvM=" via-port "1-3" with-interface { 09:00:01 09:00:02 } with-connect-type "not used"',

        # Integrated Camera
        'allow id 174f:11a8 serial "200901010001" name "Integrated Camera" hash "sBAoDzRbccuatqKpqEsFFW5f9RIM2sOpSXpUciJ9IRo=" parent-hash "ytflbcUR58vOaTlsVdDp+prbapFyL+b4z2vdOAgegjM=" with-interface { 0e:01:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:01:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 0e:02:01 fe:01:01 } with-connect-type "not used"',

        # USB device behind the hub
        'allow id 10ab:9309 serial "" name "" hash "whHOIdQrSVT8iQWv1Bg5SSP7oI4SXttsMYptqf04kXs=" parent-hash "p0xurg8ayXbgrHAmFBL5BElzY8M/rvDA/w3li6d/wtw=" via-port "1-3.1" with-interface { e0:01:01 e0:01:01 e0:01:01 e0:01:01 e0:01:01 e0:01:01 e0:01:01 e0:01:01 e0:01:01 } with-connect-type "not used"',
    ],}

# Configure sudo
sudoers_rules = [
    # WireGuard
    "ALL ALL=NOPASSWD: /usr/bin/wg show",
    "ALL ALL=NOPASSWD: /usr/bin/wg-quick",

    # User-specific permissions
    "gpkvt ALL=(root) ALL",

    # Passwordless sudo for sudo group
    "%sudo ALL=(ALL) NOPASSWD: ALL",
]

# Proton applications
proton = {
    "mail": True,
    "bridge": True,
    "vpn": True,
    "pass": True,
    "flatpak": True,
    "drive_cli_version": "0.9.0"
}

# Configure vscodium
vscodium = {
    "extensions": [
        # GitHub
        "GitHub.vscode-pull-request-github",

        # Ansible
        "5mdt.ansible-vault-editor",

        # Containers and Docker
        "ms-azuretools.vscode-containers",
        "ms-azuretools.vscode-docker",

        # Git
        "mhutchie.git-graph",

        # Remote access
        "jeanp413.open-remote-ssh",
        "Kelvin.vscode-sshfs",

        # Python
        "ms-python.python",
        "ms-python.debugpy",
        "ms-python.vscode-python-envs",

        # Data formats
        "redhat.vscode-xml",
        "redhat.vscode-yaml",

        # Formatting
        "esbenp.prettier-vscode",
    ],
}

# Configure COSMIC Desktop
cosmic = {
  "enabled": True,

  "appearance": {
      "enabled": True,
      "mode": "dark",
  },

  "panel": {
      "enabled": True,
      "position": "top",
      "autohide": False,
      "extend": True,
      "anchor_gap": False,
      "margin": 4,
      "size": "extra_small",
      "applets": {
          "left": [
              "io.github.DrakRosmann.CosmicExtAppletQuickSettings",
          ],

          "center": [
              "io.github.cosmic_utils.minimon-applet",
          ],

          "right": [
              "io.github.hepp3n.kdeconnect",
              "com.system76.CosmicAppletStatusArea",
              "com.system76.CosmicAppletTime",
              "com.vintagetechie.CosmicExtAppletTempest",
              "com.system76.CosmicAppletPower",
          ],
      },
  },
  "dock": {
      "enabled": True,
      "position": "bottom",
      "autohide": False,
      "extend": True,
      "anchor_gap": False,
      "margin": 4,
      "size": "small",
      "applets": {
          "left": [
              "io.github.crocodile.cosmic-ext-applet-workspace-icons",
          ],

          "center": [
              "com.system76.CosmicPanelAppButton",
              "com.system76.CosmicPanelLauncherButton",
              "com.system76.CosmicAppList",
              "com.system76.CosmicAppletMinimize",
          ],

          "right": [
              "io.github.AceMythos.cosmic-ext-applet-power-monitor",
              "com.system76.CosmicAppletTiling",
              "org.cosmic_utils.CosmicExtAppletContainerManager",
              "io.github.marcelogomes90.cosmic-ext-applet-trash",
          ],
      },
  },
  "workspaces": {
      "enabled": True,
      "orientation": "horizontal",
      "dynamic": True,
      "separate_displays": True,
      "wraparound": True,
  },
}

cosmic_config_files = {
    "appearance": {
        "src": "files/cosmic/local/appearance/",
        "dest": ".config/cosmic/com.system76.CosmicTheme.Mode/v1/",
    },

    "panel": {
        "src": "files/cosmic/local/panel/",
        "dest": ".config/cosmic/com.system76.CosmicPanel.Panel/v1/",
    },

    "dock": {
        "src": "files/cosmic/local/dock/",
        "dest": ".config/cosmic/com.system76.CosmicPanel.Dock/v1/",
    },
}

# Mullvad Browser extensions
mullvad_browser_dir = "/home/gpkvt/.mullvad-browser/.mullvad/mullvadbrowser/i2xe179z.default-release"

mullvad_extensions = {
    "ublock-origin": {
        "id": "uBlock0@raymondhill.net",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi",
    },
    "dark-reader": {
        "id": "addon@darkreader.org",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi",
    },
    "duckduckgo": {
        "id": "jid1-ZAdIEUB7XOzOJw@jetpack",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/duckduckgo-for-firefox/latest.xpi",
    },
    "export-cookies": {
        "id": "{36bdf805-c6f2-4f41-94d2-9b646342c1dc}",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/export-cookies-txt/latest.xpi",
    },
    "multi-account-containers": {
        "id": "@testpilot-containers",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/multi-account-containers/latest.xpi",
    },
    "privacy-badger": {
        "id": "jid1-MnnxcxisBPnSXQ@jetpack",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/privacy-badger17/latest.xpi",
    },
    "tab-discarder": {
        "id": "tab-discarder@extension",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/automatic-tab-discarder/latest.xpi",
    },
    "video-downloadhelper": {
        "id": "{b9db16a4-6edc-47ec-a1f4-b86292ed211d}",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/video-downloadhelper/latest.xpi",
    },
    "proton-vpn": {
        "id": "vpn@proton.ch",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/proton-vpn-firefox-extension/latest.xpi",
    },
    "sponsorblock": {
        "id": "sponsorBlocker@ajay.app",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/sponsorblock/latest.xpi",
    },
    "alternate-player-twitch": {
        "id": "twitch5-fork@traumvogel",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/alternate-player-for-twitch/latest.xpi",
    },
    "wallabagger": {
        "id": "wallabagger@wallabag.org",
        "url": "https://addons.mozilla.org/firefox/downloads/latest/wallabagger/latest.xpi",
    },
}

# SSH key management
ssh_keys = [
    {
        "name": "id_ed25519",
        "type": "ed25519",
        "comment": "gpkvt@workstation",
    },
    {
        "name": "id_github",
        "type": "ed25519",
        "comment": "github",
    },
    {
        "name": "id_rsa_legacy",
        "type": "rsa",
        "bits": 4096,
        "comment": "legacy-connection",
    },
]

# Public keys authorized to access this machine.
# Keys can be provided directly as strings.
ssh_authorized_keys = {
    "gpkvt": [
    ],
}

# Enforce apparmor profiles
apparmor_profiles = [
    {
        "path": "/etc/apparmor.d/transmission",
        "names": [
            "transmission-cli",
            "transmission-daemon",
            "transmission-gtk",
            "transmission-qt",
        ],
    },
    {
        "path": "/etc/apparmor.d/usr.lib.libreoffice.program.oosplash",
        "names": [
            "libreoffice-oosplash",
        ],
    },
    {
        "path": "/etc/apparmor.d/usr.lib.libreoffice.program.soffice.bin",
        "names": [
            "libreoffice-soffice",
        ],
    },
]

# Install and configure docker container
docker = {
    "miniflux": {
        "postgres_version": 12,
        "port": "8005",
    },
    "timetagger": {
        "port": "8010",
    },
    "grav": {
        "image": "getgrav/grav:1.7",
        "port": 8015,
        "channel": "stable",
        "setup": True,
        "scheduler": True,
        "fix_permissions": True,
    },
    "forgejo": {
        "image": "codeberg.org/forgejo/forgejo:17",
        "port": 3000,
        "ssh_port": 2222,
        "ssh_server": False,
        "domain": "forgejo.21x9.org",
    },
    "portainer": {
        "image": "portainer/portainer-ce:lts",
        "port": 9000,
    },
    "tasmoadmin": {
        "image": "ghcr.io/tasmoadmin/tasmoadmin:latest",
        "port": 8016,
    },
    "wallabag": {
        "image": "wallabag/wallabag:latest",
        "port": 8017,
        "domain": "https://wallabag.21x9.org",
    },
    "vaultwarden": {
        "image": "vaultwarden/server:latest",
        "port": 8018,
        "domain": "https://vaultwarden.21x9.org",
    },
    "nocodb": {
        "image": "nocodb/nocodb:latest",
        "port": 8019,
        "domain": "https://nocodb.21x9.org",
    },
    "linkwarden": {
        "image": "ghcr.io/linkwarden/linkwarden:latest",
        "port": 8021,
        "domain": "linkwarden.21x9.org",
    },
    "homepage": {
        "image": "ghcr.io/gethomepage/homepage:latest",
        # API keys are supplied by secrets.json.gpg. The Homepage task merges
        # secrets.docker.homepage.environment over this optional base mapping.
        "port": 8020,
        "domain": "homepage.21x9.org",
        # Display service cards in a compact three-column row.
        "settings": {
            # Use a local image placed in ~/.docker/homepage/public/images/.
            "background": {
                "image": "https://images.unsplash.com/photo-1502790671504-542ad42d5189?auto=format&fit=crop&w=2560&q=80",
                "blur": "sm",
                "saturate": 50,
                "brightness": 50,
            },
            "layout": {
                "Services": {
                    "style": "row",
                    "columns": 3,
                },
            },
            # Keep the API key in secrets.json.gpg; Homepage resolves this
            # environment placeholder through its shared provider configuration.
            "providers": {
                "openweathermap": "{{HOMEPAGE_VAR_OPENWEATHERMAP_API_KEY}}",
            },
        },
        # Homepage services are configured as groups containing service entries.
        # Override or extend these entries here; the task renders services.yaml.
        "services": [
            {
                "Services": [
                    {
                        "Miniflux": {
                            "icon": "/icons/miniflux.png",
                            "href": "https://rss.21x9.org",
                            "description": "RSS reader",
                            "widget": {
                                "type": "miniflux",
                                "url": "https://rss.21x9.org",
                                "key": "{{HOMEPAGE_VAR_MINIFLUX_API_KEY}}",
                            },
                        },
                    },
                    {
                        "Forgejo": {
                            "icon": "/icons/forgejo.png",
                            "href": "https://forgejo.21x9.org",
                            "description": "Git service",
                            "widget": {
                                "type": "gitea",
                                "url": "https://forgejo.21x9.org",
                                "key": "{{HOMEPAGE_VAR_FORGEJO_API_KEY}}",
                            },
                        },
                    },
                    {
                        "Portainer": {
                            "icon": "/icons/portainer.png",
                            "href": "https://portainer.21x9.org",
                            "description": "Docker management",
                            "widget": {
                                "type": "portainer",
                                "url": "https://portainer.21x9.org",
                                "env": 3,
                                "key": "{{HOMEPAGE_VAR_PORTAINER_API_KEY}}",
                            },
                        },
                    },
                    {
                        "TimeTagger": {
                            "icon": "/icons/timetagger.png",
                            "href": "https://timetagger.21x9.org",
                            "description": "Time tracking",
                        },
                    },
                    {
                        "Grav": {
                            "icon": "/icons/grav.png",
                            "href": "https://grav.21x9.org",
                            "description": "CMS",
                        },
                    },
                    {
                        "TasmoAdmin": {
                            "icon": "/icons/tasmoadmin.png",
                            "href": "https://tasmoadmin.21x9.org",
                            "description": "Tasmota device management",
                        },
                    },
                    {
                        "Wallabag": {
                            "icon": "/icons/wallabag.png",
                            "href": "https://wallabag.21x9.org",
                            "description": "Read-it-later",
                        },
                    },
                    {
                        "Vaultwarden": {
                            "icon": "/icons/vaultwarden.png",
                            "href": "https://vaultwarden.21x9.org",
                            "description": "Password manager",
                        },
                    },
                    {
                        "NocoDB": {
                            "icon": "/icons/nocodb.png",
                            "href": "https://nocodb.21x9.org",
                            "description": "Database platform",
                        },
                    },
                ],
            },
            {
                "Network": [
                    {
                        "FRITZ!Box": {
                            "icon": "mdi-router-wireless",
                            "href": "http://192.168.42.1",
                            "description": "Router and internet connection",
                            "widget": {
                                "type": "fritzbox",
                                "url": "http://192.168.42.1",
                                "fields": ["connectionStatus", "uptime", "down", "up"],
                            },
                        },
                    },
                ],
            },
        ],
        # Header widgets are separate from service widgets in services.yaml.
        # Glances listens only on Docker's default bridge gateway. Homepage
        # reaches it through host.docker.internal without publishing the API port.
        "glances": {
            "bind_address": "172.17.0.1",
            "port": 61208,
        },
        "widgets": [
            {
                "glances": {
                    "url": "http://host.docker.internal:61208",
                    "cpu": True,
                    "mem": True,
                    "cputemp": True,
                    "uptime": True,
                    "disk": "/",
                    "expanded": True,
                    "label": "chao",
                },
            },
            {
                    "search": {
                        "provider": "duckduckgo",
                        "target": "_blank",
                    },
            },
            {
                "datetime": {
                    "text_size": "xl",
                    "locale": "de-DE",
                    "format": {
                        "dateStyle": "medium",
                        "timeStyle": "short",
                        "hourCycle": "h23",
                        "timeZone": "Europe/Amsterdam",
                    },
                },
            },
            {
                "openweathermap": {
                    "label": "Köln",
                    "latitude": 50.9375,
                    "longitude": 6.9603,
                    "units": "metric",
                    "provider": "openweathermap",
                    "cache": 5,
                    "format": {
                        "maximumFractionDigits": 1,
                    },
                },
            },
        ],
    },
}

# Caddy configuration
caddy_config = {
  "rss.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8005",
    "header": [
      "-Server"
    ],
  },
  "timetagger.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8010",
    "header": [
      "-Server"
    ],
  },
  "grav.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8015",
    "header": [
      "-Server"
    ],
  },
  "forgejo.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:3000",
    "header": [
      "-Server"
    ],
  },
  "portainer.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:9000",
    "header": [
      "-Server"
    ],
  },
  "tasmoadmin.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8016",
    "header": [
      "-Server"
    ],
  },
  "wallabag.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8017",
    "header": [
      "-Server"
    ],
  },
  "vaultwarden.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8018",
    "header": [
      "-Server"
    ],
  },
  "homepage.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8020",
    "header": [
      "-Server"
    ],
  },
  "nocodb.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8019",
    "header": [
      "-Server"
    ],
  },
  "linkwarden.21x9.org:443": {
    "tls": "/var/lib/dehydrated/certs/21x9.org/fullchain.pem /var/lib/dehydrated/certs/21x9.org/privkey.pem",
    "reverse_proxy": "127.0.0.1:8021",
    "header": [
      "-Server"
    ],
  },
}

# Install apt packages
apt_packages = [
  "7zip",
  "7zip-rar",
  "apt-file",
  "aria2",
  "atop",
  "audacity",
  "bat",
  "bc",
  "borgbackup",
  "bsdutils",
  "btop",
  "build-essential",
  "bzip2",
  "curl",
  "debian-goodies",
  "fwupd",
  "git",
  "glances",
  "gnupg",
  "gnupg-utils",
  "gnupg2",
  "gparted",
  "gpg",
  "gpg-agent",
  "gzip",
  "handbrake",
  "html2text",
  "htop",
  "hyfetch",
  "iftop",
  "ioping",
  "iotop",
  "keychain",
  "lsb-release",
  "lshw",
  "lsof",
  "mc",
  "needrestart",
  "netcat-openbsd",
  "net-tools",
  "nload",
  "nmon",
  "powertop",
  "pv",
  "pwgen",  "reptyr",
  "restic",
  "rsync",
  "taskd",
  "taskwarrior",
  "thunderbird",
  "thunderbird-locale-de",
  "thunderbird-locale-en",
  "tig",
  "timewarrior",
  "unp",
  "unrar-free",
  "unzip",
  "vlc",
  "wget",
  "youtube-music",
  "yt-dlp",
  "zip",
]

apt_sources = {
  "docker": {
      "key": {
          "url": "https://download.docker.com/linux/ubuntu/gpg",
          "path": "/etc/apt/keyrings/docker-keyring.asc",
      },
      "repository": {
          "url": "https://download.docker.com/linux/ubuntu",
          "distribution": "noble",
          "components": ["stable"],
          "architectures": ["amd64"],
      },
  },
  "mullvad": {
      "key": {
          "url": "https://repository.mullvad.net/deb/mullvad-keyring.asc",
          "path": "/etc/apt/keyrings/mullvad-keyring.asc",
      },
      "repository": {
          "url": "https://repository.mullvad.net/deb/stable",
          "distribution": "stable",
          "components": ["main"],
          "architectures": ["amd64"],
          "types": ["deb"],
      },
  },
  "proton": {
      "key": {
          "url": "https://repo.protonvpn.com/debian/public_key.asc",
          "path": "/etc/apt/keyrings/proton-keyring.asc",
      },
      "repository": {
          "url": "https://repo.protonvpn.com/debian",
          "distribution": "stable",
          "components": ["main"],
          "architectures": ["amd64"],
          "types": ["deb"],
      },
  },
  "vscodium": {
      "key": {
          "url": "https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/-/raw/master/pub.gpg",
          "path": "/usr/share/keyrings/vscodium-archive-keyring.asc",
      },
      "repository": {
          "url": "https://download.vscodium.com/debs",
          "distribution": "vscodium",
          "components": ["main"],
          "architectures": ["amd64", "arm64"],
          "types": ["deb"],
      },
  },
  "signal": {
      "key": {
          "url": "https://updates.signal.org/desktop/apt/keys.asc",
          "path": "/usr/share/keyrings/signal-desktop-keyring.asc",
      },
      "repository": {
          "url": "https://updates.signal.org/desktop/apt",
          "distribution": "xenial",
          "components": ["main"],
          "architectures": ["amd64"],
          "types": ["deb"],
      },
  },
  "waydroid": {
      "key": {
          "url": "https://repo.waydro.id/waydroid.gpg",
          "path": "/etc/apt/keyrings/waydroid-keyring.gpg",
      },
      "repository": {
          "url": "https://repo.waydro.id/",
          "distribution": "noble",
          "components": ["main"],
          "architectures": ["amd64"],
          "types": ["deb"],
      },
  },
  "synaptics": {
      "key": {
          "url": "https://www.synaptics.com/sites/default/files/Ubuntu/synaptics-repository-keyring.gpg",
          "path": "/usr/share/keyrings/synaptics-keyring.gpg",
      },
      "repository": {
          "url": "https://www.synaptics.com/sites/default/files/Ubuntu",
          "distribution": "stable",
          "components": ["main", "non-free"],
          "architectures": ["amd64"],
          "types": ["deb"],
      },
  },
  "winehq": {
      "key": {
          "url": "https://dl.winehq.org/wine-builds/winehq.key",
          "path": "/etc/apt/keyrings/winehq-keyring.key",
      },
      "repository": {
          "url": "https://dl.winehq.org/wine-builds/ubuntu",
          "distribution": "noble",
          "components": ["main"],
          "architectures": ["amd64", "i386"],
          "types": ["deb"],
      },
  },
}

# Install flatpak packages
flatpak_packages = [
  "app.go2tv.go2tv",
  "app.ytmdesktop.ytmdesktop",
  "best.ellie.StartupConfiguration",
  "ch.protonmail.protonmail-bridge",
  "com.bambulab.BambuStudio",
  "com.chatterino.chatterino",
  "com.core447.StreamController",
  "com.github.d4nj1.tlpui",
  "com.github.donadigo.appeditor",
  "com.github.hmrdsmoke.void-watcher",
  "com.github.phase1geo.minder",
  "com.github.tchx84.Flatseal",
  "com.github.wwmm.easyeffects",
  "com.obsproject.Studio",
  "com.prof18.feedflow",
  "com.spotify.Client",
  "com.vintagetechie.CosmicExtAppletCargoWatch",
  "com.vintagetechie.CosmicExtAppletTempest",
  "de.willuhn.Jameica",
  "dev.DBrox.CosmicPrivacyIndicator",
  "dev.cappsy.CosmicExtAppletDict",
  "dev.cappsy.CosmicExtAppletDrives",  "dev.cappsy.CosmicExtAppletLogoMenu",
  "dev.edfloreshz.Calculator",
  "dev.edfloreshz.CosmicTweaks",
  "dev.heppen.webapps",
  "dev.mariinkys.Cedilla",
  "fr.clockworks.cosmic-ext-applet-hue",
  "io.github.AceMythos.cosmic-ext-applet-power-monitor",
  "io.github.DrakRosmann.CosmicExtAppletQuickSettings",
  "io.github.cosmic_utils.camera",
  "io.github.cosmic_utils.cosmic-ext-applet-clipboard-manager",
  "io.github.cosmic_utils.minimon-applet",
  "io.github.crocodile.cosmic-ext-applet-workspace-icons",
  "io.github.giantpinkrobots.flatsweep",
  "io.github.hepp3n.kdeconnect",
  "io.github.marcelogomes90.cosmic-ext-applet-status-hub",
  "io.github.marcelogomes90.cosmic-ext-applet-trash",
  "io.github.pieterdd.RcloneShuttle",
  "io.tangencylabs.solidcraft",
  "md.obsidian.Obsidian",
  "me.proton.Mail",
  "net.epson.epsonscan2",
  "net.fhannenheim.musicfetch",
  "net.filebot.FileBot",
  "one.flipperzero.qFlipper",
  "org.chromium.Chromium",
  "org.chromium.Chromium.Codecs",
  "org.cosmic_utils.CosmicExtAppletContainerManager",
  "org.darktable.Darktable",
  "org.freecad.FreeCAD",
  "org.gnome.Loupe",
  "org.gnome.meld",
  "org.localsend.localsend_app",
  "org.musicbrainz.Picard",
  "org.prismlauncher.PrismLauncher",
  "org.signal.Signal",
  "org.torproject.torbrowser-launcher",
  "tech.feliciano.pocket-casts",
]

# Configure wireguard conncetions
wireguard_config = {
  "home": {
    "interface": {
      "Address": "192.168.42.251/24,fd4b:4511:701a::251/64",
      "DNS": [
        "192.168.42.1,fd4b:4511:701a::e72:74ff:fe5a:6476",
        "fritz.box"
      ],
      "Table": 55995,
      "FwMark": 55995,
      "PostUp": [
        "ip rule add not fwmark 55995 table 55995",
        "ip rule add table main suppress_prefixlength 0"
      ],
      "PreDown": [
        "ip rule del table main suppress_prefixlength 0",
        "ip rule del not fwmark 55995 table 55995"
      ],
    },
  }
}

# Configure firewall
ufw = {
    "kdeconnect": "Allow",
    "localsend": "Allow",
    "chromecast-dlna": "Deny",
    "ssh": "Deny",

    # Allow Docker containers to access Caddy on the host.
    "docker-host-https": {
        "action": "Allow",
        "rule": "in from 172.16.0.0/12 to 172.17.0.1 port 443 proto tcp",
    },

    # Allow Homepage containers to access Glances on the host.
    "docker-host-glances": {
        "action": "Allow",
        "rule": "from 172.27.0.0/16 to 172.17.0.1 port 61208 proto tcp",
    },
}

# Configure ssh client
ssh_config = {
    "192.168.42.*": """
  HostKeyAlgorithms +ssh-rsa
  PubkeyAcceptedKeyTypes +ssh-rsa
    """,
    "gitlab.com": """
  HostName gitlab.com
  IdentityFile ~/.ssh/id_gitlab
  IdentitiesOnly yes
  ForwardAgent no
  User git
    """,
    "github.com": """
  HostName github.com
  IdentityFile ~/.ssh/id_github
  IdentitiesOnly yes
  ForwardAgent no
  User git
    """,
    "dns 192.168.42.100": """
  HostName 192.168.42.100

  PasswordAuthentication no
  IdentitiesOnly yes
  User root
    """,
    "dms 192.168.42.120": """
  HostName 192.168.42.120

  PasswordAuthentication no
  IdentitiesOnly yes
  User root
    """,
}

# Enable zplug zsh plugins
zplug_plugins = [
  '"zsh-users/zsh-syntax-highlighting"',
  '"zsh-users/zsh-autosuggestions"',
  '"zsh-users/zsh-completions"',
  '"plugins/per-directory-history", from:oh-my-zsh',
  '"plugins/history-substring-search", from:oh-my-zsh',
  '"plugins/common-aliases", from:oh-my-zsh',
  '"plugins/nmap", from:oh-my-zsh',
  '"plugins/taskwarrior", from:oh-my-zsh',
  '"romkatv/powerlevel10k", use:powerlevel10k.zsh-theme',
]

# Import scripts into .zshrc
zshrc_imports = [
  "exports",
  "variables",
  "keybindings",
  "history",
  "aliases",
  "completions",
  "zplug",
  "ssh",
  "tmux",
  "powerlevel",
  "neofetch",
]
