#!/usr/bin/env python3
"""Preview or sync Mullvad Browser extensions and managed preferences to inventory.

Only reconstruct add-on URLs from existing inventory or HTTPS sourceURI
metadata. Never invent extension download URLs or export arbitrary prefs.js.
"""

import argparse
import difflib
import ast
import json
import os
import pprint
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def find_repository_root():
    """Find the working checkout when invoked from ~/scripts or source."""
    candidates = (Path.cwd(), *Path.cwd().parents,
                  *Path(__file__).resolve().parents, Path.home() / "pyinfra")
    for root in candidates:
        if (root / "group_data").is_dir() and (root / "deploy.py").is_file():
            return root
    return Path.cwd()


ROOT = find_repository_root()
DEFAULT_DISTRIBUTION = Path("/usr/lib/mullvad-browser/distribution")
PREF = re.compile(r'^\s*user_pref\(\s*("(?:\\.|[^"\\])*")\s*,\s*(.+?)\s*\);\s*$')
EXTENSION_ID = re.compile(r"(?:[A-Za-z0-9._@+-]+|\{[0-9A-Fa-f-]{36}\})\Z")

# A profile's prefs.js includes URLs and extension state. Import only an
# explicit list of ordinary UI/privacy settings from that sensitive file.
SAFE_PROFILE_PREFS = frozenset({
    "browser.tabs.warnOnClose",
    "browser.tabs.loadInBackground",
    "browser.search.suggest.enabled",
    "browser.urlbar.suggest.searches",
    "privacy.resistFingerprinting",
    "privacy.trackingprotection.enabled",
    "privacy.donottrackheader.enabled",
    "privacy.firstparty.isolate",
    "network.cookie.cookieBehavior",
    "dom.security.https_only_mode",
})


def literal_assignments(source):
    """Return literal top-level inventory values without executing Python."""
    tree = ast.parse(source)
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "mullvad_extensions", "mullvad_browser_prefs"
            }:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError, MemoryError) as exc:
                    raise ValueError(
                        f"{target.id} must be a literal mapping to sync safely"
                    ) from exc
    return values


def valid_url(url):
    """Only accept plain HTTPS download URLs without embedded credentials."""
    if not isinstance(url, str):
        return False
    parts = urlsplit(url)
    return parts.scheme == "https" and bool(parts.hostname) and not parts.username and not parts.password


def addon_sources(profile):
    """Read browser-supplied source URLs, without importing profile settings."""
    sources = {}
    if profile is None:
        return sources
    path = profile / "extensions.json"
    if not path.is_file():
        return sources
    data = json.loads(path.read_text(encoding="utf-8"))
    for addon in data.get("addons", []):
        addon_id = addon.get("id")
        url = addon.get("sourceURI")
        if isinstance(addon_id, str) and EXTENSION_ID.fullmatch(addon_id) and valid_url(url):
            sources[addon_id] = url
    return sources


def browser_extensions(directory, profile):
    """Find installed extension IDs in distribution and optional user profile."""
    extension_ids = set()
    locations = [directory / "extensions"]
    if profile is not None:
        locations.append(profile / "extensions")
    for location in locations:
        if location.is_dir():
            extension_ids.update(
                path.stem for path in location.glob("*.xpi")
                if path.is_file() and EXTENSION_ID.fullmatch(path.stem)
            )
    if profile is not None and (profile / "extensions.json").is_file():
        data = json.loads((profile / "extensions.json").read_text(encoding="utf-8"))
        extension_ids.update(
            addon["id"] for addon in data.get("addons", [])
            if isinstance(addon.get("id"), str)
            and EXTENSION_ID.fullmatch(addon["id"])
            and addon.get("active", False)
            and not addon.get("isSystem", False)
            and not addon.get("isBuiltin", False)
        )
    return extension_ids


def browser_preferences(path):
    """Read user.js or allowlisted preferences from a profile prefs.js."""
    if not path.is_file():
        return {}
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = PREF.fullmatch(line)
        if not match:
            continue
        try:
            key = json.loads(match.group(1))
            value = json.loads(match.group(2))
        except json.JSONDecodeError:
            continue
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", key):
            continue
        if not isinstance(value, (str, bool, int, float)):
            continue
        if path.name == "prefs.js" and key not in SAFE_PROFILE_PREFS:
            continue
        if any(word in key.lower() for word in (
            "password", "secret", "token", "credential", "proxy",
            "homepage", "username", "identity",
        )):
            continue
        result[key] = value
    return result


def replace_assignments(source, changes):
    """Replace only the named top-level assignments, preserving other code."""
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    spans = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in changes:
                if target.id in spans:
                    raise ValueError(f"Duplicate assignment: {target.id}")
                spans[target.id] = (node.lineno - 1, node.end_lineno)
    for name, (start, end) in sorted(spans.items(), key=lambda item: item[1][0], reverse=True):
        lines[start:end] = [f"{name} = {pprint.pformat(changes[name], sort_dicts=True)}\n"]
    result = "".join(lines)
    for name in changes:
        if name not in spans:
            result += f"\n{name} = {pprint.pformat(changes[name], sort_dicts=True)}\n"
    return result


def synchronize(directory, profile, preferences_file, destination, prune=False):  # pylint: disable=R0914
    """Return updated inventory text and unresolved extension IDs."""
    if not destination.is_file():
        raise FileNotFoundError(f"Inventory file not found: {destination}")
    original = destination.read_text(encoding="utf-8")
    current = literal_assignments(original)
    installed = browser_extensions(directory, profile)
    existing = current.get("mullvad_extensions", {})
    if not isinstance(existing, dict):
        raise ValueError("mullvad_extensions must be a literal mapping")
    known = {}
    for name, config in existing.items():
        if not isinstance(config, dict) or not isinstance(config.get("id"), str):
            raise ValueError(f"Invalid configured extension: {name}")
        if valid_url(config.get("url")):
            known[config["id"]] = (name, config["url"])
    discovered = addon_sources(profile)
    updated = {} if prune else dict(existing)
    unresolved = []
    for addon_id in sorted(installed):
        if addon_id in known:
            name, url = known[addon_id]
        elif addon_id in discovered:
            name, url = addon_id, discovered[addon_id]
        else:
            unresolved.append(addon_id)
            continue
        updated[name] = {"id": addon_id, "url": url}
    if prune:
        # Never discard entries just because their download URL is unknown.
        updated.update({
            name: config for name, config in existing.items()
            if config.get("id") in unresolved
        })
    prefs = browser_preferences(preferences_file)
    old_prefs = current.get("mullvad_browser_prefs", {})
    if not isinstance(old_prefs, dict):
        raise ValueError("mullvad_browser_prefs must be a literal mapping")
    # Merge allowlisted profile values with existing inventory preferences,
    # rather than deleting settings the browser does not expose in prefs.js.
    changes = {"mullvad_extensions": updated}
    if preferences_file.is_file():
        changes["mullvad_browser_prefs"] = (
            {**old_prefs, **prefs}
            if preferences_file.name == "prefs.js" else prefs
        )
    return original, replace_assignments(original, changes), unresolved


def main(argv=None):
    """Preview by default; write changes only with --write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("local", "workstation"), default="local")
    parser.add_argument("--distribution", type=Path, default=DEFAULT_DISTRIBUTION)
    parser.add_argument("--profile", type=Path, help="Optional Mullvad Browser profile directory")
    parser.add_argument("--prefs-file", type=Path, help="Explicit user.js or allowlisted prefs.js source")
    parser.add_argument("--inventory", type=Path, help="Override group_data destination")
    parser.add_argument("--prune", action="store_true", help="Remove absent extensions with known URLs")
    parser.add_argument("--write", action="store_true", help="Write changed inventory; default is preview")
    args = parser.parse_args(argv)
    destination = args.inventory or ROOT / "group_data" / (
        "@local.py" if args.target == "local" else "workstation.py"
    )
    prefs_file = args.prefs_file or (
        args.profile / "prefs.js" if args.profile else args.distribution / "user.js"
    )
    try:
        original, updated, unresolved = synchronize(
            args.distribution, args.profile, prefs_file, destination, args.prune
        )
        for addon_id in unresolved:
            print(f"Skipping {addon_id}: no existing HTTPS XPI URL or sourceURI", file=sys.stderr)
        if updated == original:
            print("No changes.")
        elif args.write:
            # Atomically replace the inventory file; retain its current mode.
            descriptor, tmp_name = tempfile.mkstemp(
                prefix=f".{destination.name}.", dir=str(destination.parent)
            )
            try:
                os.fchmod(descriptor, destination.stat().st_mode & 0o777)
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(updated)
                os.replace(tmp_name, destination)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
            print(f"Updated {destination}")
        else:
            print("".join(difflib.unified_diff(
                original.splitlines(keepends=True), updated.splitlines(keepends=True),
                fromfile=str(destination), tofile=str(destination) + " (proposed)"
            )), end="")
            print("Preview only; pass --write to apply.")
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Sync error: {exc}\n")


if __name__ == "__main__":
    main()
