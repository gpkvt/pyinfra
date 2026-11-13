# pylint: disable=C0301
"""
Install Limusic's latest stable Linux AppImage for the configured user.

The release AppImage is self-updating. The task installs it once per stable
release, verifies the published SHA-256 digest, and installs the matching
upstream application icon and a COSMIC-discoverable desktop entry.
"""

import shlex
from io import StringIO

from pyinfra import host
from pyinfra.facts.server import Command
from pyinfra.operations import files, server


config = host.data.get("workstation", {}).get("limusic", {})

if config.get("enabled", False):
    username = host.data.get("username")
    usergroup = host.data.get("usergroup", username)
    homedir = host.data.get("homedir")

    if not username or not homedir:
        raise ValueError(
            "username and homedir must be configured for workstation.limusic"
        )

    install_dir = f"{homedir}/.local/opt/limusic"
    appimage = f"{install_dir}/limusic.AppImage"
    version_file = f"{install_dir}/.release"
    icon_dir = f"{homedir}/.local/share/icons"
    icon_file = f"{icon_dir}/limusic.png"
    applications_dir = f"{homedir}/.local/share/applications"
    desktop_file = f"{applications_dir}/limusic.desktop"

    release_command = (
        "python3 -c "
        + shlex.quote(
            "import json, urllib.request; "
            "request = urllib.request.Request("
            "'https://api.github.com/repos/SimoHypers/limusic/releases/latest', "
            "headers={'Accept': 'application/vnd.github+json', "
            "'User-Agent': 'pyinfra-limusic-installer'}); "
            "print(json.load(urllib.request.urlopen(request, timeout=30))['tag_name'])"
        )
    )
    latest_tag = (host.get_fact(Command, release_command) or "").strip()

    if not latest_tag:
        raise RuntimeError("Could not resolve the latest stable Limusic release")

    installed_tag = (
        host.get_fact(
            Command,
            f"cat {shlex.quote(version_file)} 2>/dev/null || true",
        )
        or ""
    ).strip()

    files.directory(
        name="Create Limusic AppImage directory",
        path=install_dir,
        user=username,
        group=usergroup,
        mode="0755",
    )
    files.directory(
        name="Create Limusic icon directory",
        path=icon_dir,
        user=username,
        group=usergroup,
        mode="0755",
    )
    files.directory(
        name="Create user desktop applications directory",
        path=applications_dir,
        user=username,
        group=usergroup,
        mode="0755",
    )

    if latest_tag != installed_tag:
        install_script = r'''
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.request

expected_tag, appimage_path, icon_path, version_path = sys.argv[1:]
api_url = "https://api.github.com/repos/SimoHypers/limusic/releases/latest"
request = urllib.request.Request(
    api_url,
    headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "pyinfra-limusic-installer",
    },
)
with urllib.request.urlopen(request, timeout=30) as response:
    release = json.load(response)

tag = release.get("tag_name")
if tag != expected_tag:
    raise RuntimeError(
        f"Limusic release changed during deployment: {tag!r} != {expected_tag!r}"
    )

assets = [
    asset for asset in release.get("assets", [])
    if re.fullmatch(r"limusic_.+_amd64\.AppImage", asset.get("name", ""))
]
if len(assets) != 1:
    raise RuntimeError(
        f"Expected one x86_64 Limusic AppImage in {tag}, found {len(assets)}"
    )

asset = assets[0]
digest = asset.get("digest", "")
if not digest.startswith("sha256:"):
    raise RuntimeError("Limusic release does not publish an AppImage SHA-256 digest")

appimage = pathlib.Path(appimage_path)
icon = pathlib.Path(icon_path)
version = pathlib.Path(version_path)

def atomic_write(destination, data, mode):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

appimage.parent.mkdir(parents=True, exist_ok=True)
fd, temporary = tempfile.mkstemp(dir=appimage.parent)
try:
    hasher = hashlib.sha256()
    request = urllib.request.Request(
        asset["browser_download_url"],
        headers={"User-Agent": "pyinfra-limusic-installer"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, os.fdopen(fd, "wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
            output.write(chunk)
        output.flush()
        os.fsync(output.fileno())
    if hasher.hexdigest() != digest.removeprefix("sha256:"):
        raise RuntimeError("Limusic AppImage SHA-256 verification failed")
    os.chmod(temporary, 0o755)
    os.replace(temporary, appimage)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)

icon_url = (
    f"https://raw.githubusercontent.com/SimoHypers/limusic/{tag}/"
    "src-tauri/icons/icon.png"
)
request = urllib.request.Request(
    icon_url, headers={"User-Agent": "pyinfra-limusic-installer"}
)
with urllib.request.urlopen(request, timeout=30) as response:
    icon_data = response.read()
if not icon_data.startswith(b"\x89PNG\r\n\x1a\n"):
    raise RuntimeError("Downloaded Limusic icon is not a PNG image")
atomic_write(icon, icon_data, 0o644)
atomic_write(version, (tag + "\n").encode(), 0o644)
'''
        server.shell(
            name=f"Install Limusic AppImage {latest_tag}",
            commands=[
                "python3 -c "
                + shlex.quote(install_script)
                + " "
                + " ".join(
                    shlex.quote(value)
                    for value in (latest_tag, appimage, icon_file, version_file)
                )
            ],
            _sudo=True,
            _sudo_user=username,
            _if=lambda: (
                host.get_fact(
                    Command,
                    f"cat {shlex.quote(version_file)} 2>/dev/null || true",
                )
                or ""
            ).strip() != latest_tag,
        )

    desktop_exec = (
        '"'
        + appimage.replace("\\", "\\\\").replace('"', '\\"')
        + '" %U'
    )
    desktop_entry = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=Limusic\n"
        "Comment=Listen to YouTube Music\n"
        f"Exec={desktop_exec}\n"
        f"TryExec={appimage}\n"
        f"Icon={icon_file}\n"
        "Terminal=false\n"
        "Categories=AudioVideo;Audio;Player;\n"
        "StartupWMClass=limusic\n"
    )
    files.put(
        name="Create Limusic COSMIC desktop launcher",
        src=StringIO(desktop_entry),
        dest=desktop_file,
        user=username,
        group=usergroup,
        mode="0644",
    )
