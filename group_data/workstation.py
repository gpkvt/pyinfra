""" Config options for workstation role """

workstation = {
    "backup": {
        "enabled": True,
        # Configure Restic/Borg repositories, credentials, source paths,
        # retention and restore testing separately before scheduling backups.
    },
    "power": {
        "enabled": True,
        # Choose exactly one: "power-profiles-daemon" or "tlp".
        "manager": "tlp",
    },
    "hardware": {
        "enabled": True,
        # Set to "intel" or "amd" after checking the actual CPU vendor.
        "cpu_vendor": "amd",
        # fwupd is installed, but firmware updates are not applied automatically.
    },
    "storage": {
        "enabled": True,
        # Installs smartmontools and nvme-cli; no polling schedule is created.
    },
    "peripherals": {
        "enabled": False,
        "printing": False,
        "scanning": False,
    },
    "desktop": {
        "enabled": False,
        # Optional replacement for the default package list:
        # "packages": ["xdg-utils", "xdg-user-dirs"],
    },
    "maintenance": {
        "enabled": True,
        # Installs maintenance utilities only. No unattended upgrades/reboots.
    },
    "limusic": {
        "enabled": True,
        # Installs the latest stable Limusic x86_64 AppImage and COSMIC launcher.
    },
}
