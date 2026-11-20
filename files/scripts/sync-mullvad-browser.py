#!/usr/bin/env python3
"""Preview or sync Mullvad Browser extensions and managed preferences to inventory.

Only reconstruct add-on URLs from existing inventory or HTTPS sourceURI
metadata. Never invent extension download URLs or export arbitrary prefs.js.
"""

import argparse
import ast
import json
import pprint
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DISTRIBUTION = Path("/usr/lib/mullvad-browser/distribution")
PREF = re.compile(r'^\s*user_pref\(\s*("(?:\\.|[^"\\])*")\s*,\s*(.+?)\s*\);\s*$')
EXTENSION_ID = re.compile(r"(?:[A-Za-z0-9._@+-]+|\{[0-9A-Fa-f-]{36}\})\Z")


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
    """Read explicit user.js values only; never export a profile's prefs.js."""
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
        if (
            isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9._-]+", key)
            and isinstance(value, (str, bool, int, float))
            and not any(word in key.lower() for word in (
                "password", "secret", "token", "credential", "proxy",
                "homepage", "username", "identity",
            ))
        ):
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


def synchronize(directory, profile, preferences_file, destination, prune=False):
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
    # Avoid destroying existing settings when no user.js is present.
    changes = {"mullvad_extensions": updated}
    if preferences_file.is_file():
        changes["mullvad_browser_prefs"] = prefs
    return original, replace_assignments(original, changes), unresolved


def main(argv=None):
    """Preview by default; write changes only with --write."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("local", "workstation"), default="local")
    parser.add_argument("--distribution", type=Path, default=DEFAULT_DISTRIBUTION)
    parser.add_argument("--profile", type=Path, help="Optional Mullvad Browser profile directory")
    parser.add_argument("--prefs-file", type=Path, help="Explicit user.js file, not prefs.js")
    parser.add_argument("--inventory", type=Path, help="Override group_data destination")
    parser.add_argument("--prune", action="store_true", help="Remove absent extensions with known URLs")
    parser.add_argument("--write", action="store_true", help="Write changed inventory; default is preview")
    args = parser.parse_args(argv)
    destination = args.inventory or ROOT / "group_data" / (
        "@local.py" if args.target == "local" else "workstation.py"
    )
    prefs_file = args.prefs_file or args.distribution / "user.js"
    if prefs_file.name == "prefs.js":
        parser.error("Refusing prefs.js: it may contain private browser state; supply user.js")
    try:
        original, updated, unresolved = synchronize(
            args.distribution, args.profile, prefs_file, destination, args.prune
        )
        for addon_id in unresolved:
            print(f"Skipping {addon_id}: no existing HTTPS XPI URL or sourceURI", file=sys.stderr)
        if updated == original:
            print("No changes.")
        elif args.write:
            destination.write_text(updated, encoding="utf-8")
            print(f"Updated {destination}")
        else:
            import difflib
            print("".join(difflib.unified_diff(
                original.splitlines(keepends=True), updated.splitlines(keepends=True),
                fromfile=str(destination), tofile=str(destination) + " (proposed)"
            )), end="")
            print("Preview only; pass --write to apply.")
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Sync error: {exc}\n")


if __name__ == "__main__":
    main()
