""" Font deployment """

from pyinfra.operations import apt, server, files
from pyinfra.facts.files import Directory
from pyinfra import host

apt.packages(
    name="Installing font packages",
    packages=[
        "fontconfig",
        "fontconfig-config",
        "fonts-adf-accanthis",
        "fonts-adf-berenis",
        "fonts-adf-gillius",
        "fonts-adf-universalis",
        "fonts-arphic-ukai",
        "fonts-arphic-uming",
        "fonts-cabin",
        "fonts-cantarell",
        "fonts-clear-sans",
        "fonts-comfortaa",
        "fonts-comic-neue",
        "fonts-croscore",
        "fonts-crosextra-caladea",
        "fonts-crosextra-carlito",
        "fonts-dejavu",
        "fonts-dejavu-core",
        "fonts-dejavu-extra",
        "fonts-dejavu-mono",
        "fonts-droid-fallback",
        "fonts-ebgaramond-extra",
        "fonts-firacode",
        "fonts-font-awesome",
        "fonts-freefont-otf",
        "fonts-freefont-ttf",
        "fonts-gfs-artemisia",
        "fonts-gfs-complutum",
        "fonts-gfs-didot",
        "fonts-gfs-neohellenic",
        "fonts-gfs-olga",
        "fonts-gfs-solomos",
        "fonts-go",
        "fonts-inter",
        "fonts-lato",
        "fonts-liberation",
        "fonts-liberation-sans-narrow",
        "fonts-liberation2",
        "fonts-linuxlibertine",
        "fonts-lmodern",
        "fonts-lobster",
        "fonts-lobstertwo",
        "fonts-lyx",
        "fonts-noto-cjk",
        "fonts-noto-cjk-extra",
        "fonts-noto-color-emoji",
        "fonts-noto-core",
        "fonts-noto-mono",
        "fonts-noto-ui-core",
        "fonts-oflb-asana-math",
        "fonts-open-sans",
        "fonts-opensymbol",
        "fonts-paratype",
        "fonts-powerline",
        "fonts-quicksand",
        "fonts-roboto-slab",
        "fonts-roboto-unhinted",
        "fonts-sil-andika",
        "fonts-sil-charis",
        "fonts-sil-gentium",
        "fonts-sil-gentium-basic",
        "fonts-sil-gentiumplus",
        "fonts-sil-gentiumplus-compact",
        "fonts-stix",
        "fonts-texgyre",
        "fonts-texgyre-math",
        "fonts-tuffy",
        "fonts-ubuntu",
        "fonts-urw-base35",
        "fonts-wine",
    ],
    _sudo=True,
)

if host.data.get("powerline_fonts", False):
    FONT_DIR = "~/.local/share/fonts"
    ARCHIVE = "/tmp/powerline-fonts.zip"
    EXTRACT_DIR = "/tmp/powerline-fonts"

    # Create font directory
    files.directory(
        name="Create user font directory",
        path=FONT_DIR,
    )
    files.directory(
        name="Create tmp directory",
        path=EXTRACT_DIR,
    )

    # Download Powerline fonts
    files.download(
        name="Download Powerline fonts",
        src="https://github.com/powerline/fonts/archive/refs/heads/master.zip",
        dest=ARCHIVE,
    )

    if host.get_fact(Directory, EXTRACT_DIR):
        # Extract archive
        files.unarchive(
            name="Extract Powerline fonts",
            src=ARCHIVE,
            dest=EXTRACT_DIR,
            remote_src=True,
        )

        # Install all TTF and OTF fonts
        server.shell(
            name="Install Powerline fonts",
            commands=[
                f'find {EXTRACT_DIR}/fonts-master -type f '
                r'\( -iname "*.ttf" -o -iname "*.otf" \) '
                rf'-exec cp -n {{}} {FONT_DIR}/ \;'
            ],
        )

    # Refresh font cache
    server.shell(
        name="Refresh font cache",
        commands=[
            f"fc-cache -f {FONT_DIR}"
        ],
    )
