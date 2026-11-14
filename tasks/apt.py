"""
Manage APT package updates, upgrades, and installations.

This module provides package management for Debian-based Linux hosts
using pyinfra.

Configuration:
    apt_packages (list[str]): Packages to install, retrieved from
        host.data.apt_packages. Defaults to an empty list.

    apt_sources (dict): Third-party APT repositories to configure,
        including their signing keys and repository definitions. Signing key paths must end in `.gpg` or `.asc`.
        Entries with enabled=False are retained as configuration fixtures
        but are not downloaded or added to the system.

Execution:
    1. Ensure the APT keyrings directory exists.
    2. Download enabled repository signing keys and configure repositories.
    3. Update APT sources and upgrade packages when appropriate.
    4. Install all configured packages in a single operation.
"""

from pyinfra import host
from pyinfra.operations import apt, files
from pyinfra.operations.util import any_changed


def update_apt_sources(repository_operations):
    """Update APT, forcing an update when repositories have changed."""
    repositories_changed = any_changed(*repository_operations)

    forced_update = apt.update(
        name="Force APT update (repositories changed)",
        _if=repositories_changed,
    )

    cached_update = apt.update(
        name="Update APT sources",
        cache_time=14400,
        _if=lambda: not repositories_changed(),
    )

    return forced_update, cached_update


def upgrade_apt_packages(update_operations):
    """Upgrade packages only when an APT index update changed the index."""
    apt.upgrade(
        name="Update apt packages",
        auto_remove=True,
        _if=any_changed(*update_operations),
    )


files.directory(
    name="Ensure APT keyrings directory exists",
    path="/etc/apt/keyrings",
    mode="0755",
)

apt_sources = host.data.get("apt_sources", {})
apt_repository_operations = []

for name, repo in apt_sources.items():
    if repo.get("enabled", True) is False:
        continue

    key = repo["key"]
    repository = repo["repository"]
    key_path = key["path"]
    if not isinstance(key_path, str) or not key_path.endswith((".gpg", ".asc")):
        raise ValueError(
            f"APT keyring path for {name!r} must end in .gpg or .asc"
        )

    key_operation = apt.key(
        name=f"Install {name} APT signing key",
        src=key["url"],
        dest=key_path,
        keyid=key.get("keyid"),
    )
    # A changed signing key must invalidate the APT index cache just like a
    # changed repository definition.
    apt_repository_operations.append(key_operation)

    architectures = repository.get("architectures", [])
    components = repository.get("components", [])
    options = [f"signed-by={key_path}"]

    if architectures:
        options.append(f"arch={','.join(architectures)}")

    source_lines = []
    for repo_type in repository.get("types", ["deb"]):
        source = (
            f"{repo_type} "
            f"[{' '.join(options)}] "
            f"{repository['url']} "
            f"{repository['distribution']}"
        )
        if components:
            source += " " + " ".join(components)
        source_lines.append(source)

    repository_operation = files.template(
        name=f"Configure {name} APT repository",
        src="templates/apt_repository.list.j2",
        dest=f"/etc/apt/sources.list.d/{name}.list",
        mode="0644",
        repo_lines=source_lines,
    )
    apt_repository_operations.append(repository_operation)

apt_packages = host.data.get("apt_packages", [])
apt_update = update_apt_sources(apt_repository_operations)
upgrade_apt_packages(apt_update)

if apt_packages:
    apt.packages(
        name="Install APT packages",
        packages=apt_packages,
    )
