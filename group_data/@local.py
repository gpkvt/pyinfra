""" Define host-specific configuration for pyinfra system provisioning.

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
username="gpkvt"
usergroup="gpkvt"
homedir="/home/gpkvt"

local_network_cidr="192.168.42.0/24"
wireguard_interface="home"

# Configure /etc/hosts
hostnames = {
  "127.0.0.1": "localhost local.21x9.org timetagger.21x9.org",
  "::1": "localhost local.21x9.org",
  "192.168.42.100": "storage.intern.21x9.org paperless.intern.21x9.org huginn.intern.21x9.org grafana.intern.21x9.org ha.intern.21x9.org",
  "192.168.42.120": "storage.21x9.org",
}

# Install and configure certain tools
zsh=True
powerline=True
tmux=True

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
  },
  "dock": {
      "enabled": True,
      "position": "bottom",
      "autohide": False,
      "extend": True,
      "anchor_gap": False,
      "margin": 4,
      "size": "small",
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
  }
}

# Install apt packages
apt_packages = [
  "netcat-openbsd",
  "aria2",
  "bat",
  "btop",
  "bind9-dnsutils",
  "debian-goodies",
  "gron",
  "htop",
  "hub",
  "icdiff",
  "ioping",
  "iotop",
  "keychain",
  "lsof",
  "mtr",
  "ncdu",
  "net-tools",
  "nload",
  "nmon",
  "oping",
  "powerline",
  "progress",
  "pv",
  "ranger",
  "reptyr",
  "tig",
  "unp",
  "jq",
  "nethogs",
  "duf",
  "python3-pip",
  "python3-passlib",
]

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
  "dev.cappsy.CosmicExtAppletDrives",
  "dev.cappsy.CosmicExtAppletLogoMenu",
  "dev.edfloreshz.Calculator",
  "dev.edfloreshz.CosmicTweaks",
  "dev.heppen.webapps",
  "dev.mariinkys.Cedilla",
  "fr.clockworks.cosmic-ext-applet-hue",
  "io.github.AceMythos.cosmic-ext-applet-power-monitor",
  "io.github.cosmic_utils.camera",
  "io.github.cosmic_utils.cosmic-ext-applet-clipboard-manager",
  "io.github.cosmic_utils.minimon-applet",
  "io.github.giantpinkrobots.flatsweep",
  "io.github.hepp3n.kdeconnect",
  "io.github.marcelogomes90.cosmic-ext-applet-status-hub",
  "io.github.pieterdd.RcloneShuttle",
  "md.obsidian.Obsidian",
  "me.proton.Mail",
  "net.epson.epsonscan2",
  "net.fhannenheim.musicfetch",
  "net.filebot.FileBot",
  "one.flipperzero.qFlipper",
  "org.chromium.Chromium",
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
  "io.github.DrakRosmann.CosmicExtAppletQuickSettings",
  "io.github.marcelogomes90.cosmic-ext-applet-trash",
  "io.github.crocodile.cosmic-ext-applet-workspace-icons",
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
}

caddy_config = {
  "local.21x9.org:443": {
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
  }
}

# Configure ssh client
ssh_config = {
    "*": """
  IdentitiesOnly yes
  Compression yes
  ForwardAgent no
    """,
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
