#!/usr/bin/env python3
"""Export supported live COSMIC settings into the workstation.cosmic block."""

import argparse
import ast
import difflib
import json
import re
import sys
from pathlib import Path
from pprint import pformat


COMPONENTS = {
    "appearance": {
        "com.system76.CosmicTheme.Mode/v1/is_dark": ("mode", "mode"),
    },
    "dock": {
        "com.system76.CosmicPanel.Dock/v1/anchor": ("position", "position"),
        "com.system76.CosmicPanel.Dock/v1/autohide": ("autohide", "autohide"),
        "com.system76.CosmicPanel.Dock/v1/expand_to_edges": ("extend", "bool"),
        "com.system76.CosmicPanel.Dock/v1/size": ("size", "dock-size"),
        "com.system76.CosmicPanel.Dock/v1/plugins_wings": ("applets", "wings"),
        "com.system76.CosmicPanel.Dock/v1/plugins_center": ("applets", "center"),
    },
    "panel": {
        "com.system76.CosmicPanel.Panel/v1/anchor": ("position", "position"),
        "com.system76.CosmicPanel.Panel/v1/autohide": ("autohide", "autohide"),
        "com.system76.CosmicPanel.Panel/v1/expand_to_edges": ("extend", "bool"),
        "com.system76.CosmicPanel.Panel/v1/size": ("size", "panel-size"),
        "com.system76.CosmicPanel.Panel/v1/plugins_wings": ("applets", "wings"),
        "com.system76.CosmicPanel.Panel/v1/plugins_center": ("applets", "center"),
    },
    "input": {
        "com.system76.CosmicComp/v1/input_default": ("default", "ron"),
        "com.system76.CosmicComp/v1/input_touchpad": ("touchpad", "ron"),
    },
    "shortcuts": {
        "com.system76.CosmicSettings.Shortcuts/v1/custom": ("ron", "ron"),
    },
    "workspaces": {
        "com.system76.CosmicComp/v1/workspaces": ("ron", "ron"),
    },
    "window_management": {
        "com.system76.CosmicComp/v1/autotile": ("autotile", "bool"),
        "com.system76.CosmicComp/v1/focus_follows_cursor": ("focus_follows_cursor", "bool"),
        "com.system76.CosmicComp/v1/cursor_follows_focus": ("cursor_follows_focus", "bool"),
        "com.system76.CosmicComp/v1/autotile_behavior": ("autotile_behavior", "behavior"),
        "com.system76.CosmicComp/v1/edge_snap_threshold": ("edge_snap_threshold", "integer"),
    },
}


def read_value(root, relative_path):
    """Read one deployed COSMIC value, returning None when it is absent."""
    path = root.joinpath(*relative_path.split("/"))
    try:
        return path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def parse_bool(value):
    """Parse COSMIC's textual boolean representation."""
    if value not in ("true", "false"):
        raise ValueError(f"Expected true or false, got {value!r}")
    return value == "true"


def parse_string_list(value):
    """Parse a RON list containing strings, including RON trailing commas."""
    # COSMIC writes valid RON, which permits trailing commas that JSON rejects.
    normalized = re.sub(r",\s*(?=])", "", value)
    try:
        items = json.loads(normalized)
    except json.JSONDecodeError as error:
        raise ValueError(f"Unsupported COSMIC applet list: {error}") from error
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError("Applet lists must contain strings")
    return items


def parse_applets(value):
    """Parse the string-list tuple used by COSMIC panel and dock applets."""
    match = re.fullmatch(
        r"\s*Some\s*\(\s*\(\s*(\[.*?\])\s*,\s*(\[.*?\])\s*,?\s*\)\s*\)\s*",
        value,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Unsupported COSMIC plugins_wings RON representation")
    left, right = (parse_string_list(item) for item in match.groups())
    return {"left": left, "right": right}


def parse_center(value):
    """Parse the JSON-compatible RON list emitted for center applets."""
    match = re.fullmatch(r"\s*Some\s*\(\s*(\[.*\])\s*\)\s*", value, re.DOTALL)
    if not match:
        raise ValueError("Unsupported COSMIC plugins_center RON representation")
    return parse_string_list(match.group(1))


def convert_value(value, kind):
    """Convert a supported on-disk value to its host-data representation."""
    if kind == "mode":
        return {"true": "dark", "false": "light"}[value]
    if kind == "position":
        result = value.lower()
        if result not in {"top", "bottom", "left", "right"}:
            raise ValueError(f"Unsupported COSMIC position: {value}")
        return result
    if kind == "autohide":
        if value == "OnOverlap":
            return True
        if value == "Never":
            return False
        raise ValueError(f"Unsupported COSMIC autohide value: {value}")
    if kind == "bool":
        return parse_bool(value)
    if kind == "dock-size":
        try:
            return {"S": "small", "M": "normal", "L": "large"}[value]
        except KeyError as error:
            raise ValueError(f"Unsupported COSMIC dock size: {value}") from error
    if kind == "panel-size":
        try:
            return {"XS": "xs", "S": "s", "M": "m", "L": "l", "XL": "xl"}[value]
        except KeyError as error:
            raise ValueError(f"Unsupported COSMIC panel size: {value}") from error
    if kind == "behavior":
        if value not in {"PerWorkspace", "Global"}:
            raise ValueError(f"Unsupported COSMIC autotile behavior: {value}")
        return value
    if kind == "integer":
        result = int(value)
        if result < 0:
            raise ValueError("COSMIC edge snap threshold cannot be negative")
        return result
    if kind == "ron":
        return value
    raise ValueError(f"Unknown conversion type: {kind}")


def export_supported(config_root):
    """Collect only known keys and preserve unknown or unavailable settings."""
    result = {}
    for component, settings in COMPONENTS.items():
        values = {}
        for relative_path, (option, kind) in settings.items():
            raw = read_value(config_root, relative_path)
            if raw is None:
                continue
            if kind == "wings":
                applets = parse_applets(raw)
                values.setdefault("applets", {}).update(applets)
            elif kind == "center":
                values.setdefault("applets", {})["center"] = parse_center(raw)
            else:
                values[option] = convert_value(raw, kind)
        if values:
            result[component] = values
    return result


def find_cosmic_expression(source):
    """Locate the existing literal workstation.cosmic expression safely."""
    tree = ast.parse(source)
    candidates = []
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(isinstance(target, ast.Name) and target.id == "workstation"
               for target in targets):
            candidates.append(node.value)
    if len(candidates) != 1:
        raise ValueError("Expected exactly one top-level workstation assignment")
    workstation_node = candidates[0]
    workstation = ast.literal_eval(workstation_node)
    if not isinstance(workstation, dict) or not isinstance(workstation.get("cosmic"), dict):
        raise ValueError("workstation.cosmic must be an existing literal dictionary")
    cosmic_nodes = []
    if isinstance(workstation_node, ast.Dict):
        for key, value in zip(workstation_node.keys, workstation_node.values):
            if isinstance(key, ast.Constant) and key.value == "cosmic":
                cosmic_nodes.append(value)
    if len(cosmic_nodes) != 1 or not isinstance(cosmic_nodes[0], ast.Dict):
        raise ValueError("workstation.cosmic must be a literal dictionary")
    return cosmic_nodes[0], workstation["cosmic"]


def update_local_config(source, exported):
    """Merge exported settings into only the existing workstation.cosmic expression."""
    node, existing = find_cosmic_expression(source)
    merged = dict(existing)
    for component, values in exported.items():
        current = merged.get(component, {})
        if not isinstance(current, dict):
            raise ValueError(f"workstation.cosmic.{component} must be a dictionary")
        merged[component] = {**current, **values}
    replacement = pformat(merged, sort_dicts=False, width=88)
    lines = source.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:node.lineno - 1]) + node.col_offset
    end = sum(len(line) for line in lines[:node.end_lineno - 1]) + node.end_col_offset
    return source[:start] + replacement + source[end:]


def main(argv=None):
    """Run the COSMIC exporter and optionally preview the proposed change."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir", type=Path,
        default=Path.home() / ".config" / "cosmic",
        help="COSMIC configuration directory (default: ~/.config/cosmic)",
    )
    parser.add_argument(
        "--workstation-file", "--local-file", dest="workstation_file",
        type=Path, default=Path("group_data/workstation.py"),
        help="workstation configuration file to update (default: group_data/workstation.py)",
    )
    parser.add_argument("--dry-run", action="store_true", help="print a unified diff without writing")
    args = parser.parse_args(argv)

    try:
        if not args.config_dir.is_dir():
            raise ValueError(f"COSMIC config directory does not exist: {args.config_dir}")
        if not args.workstation_file.is_file():
            raise ValueError(f"Workstation configuration does not exist: {args.workstation_file}")
        original = args.workstation_file.read_text(encoding="utf-8")
        exported = export_supported(args.config_dir)
        if not exported:
            print("No supported COSMIC settings found; local configuration unchanged.")
            return 0
        updated = update_local_config(original, exported)
        if updated == original:
            print("COSMIC configuration is already up to date.")
            return 0
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=str(args.workstation_file),
            tofile=str(args.workstation_file) + " (updated)",
        )
        sys.stdout.writelines(diff)
        if not args.dry_run:
            args.workstation_file.write_text(updated, encoding="utf-8")
            print(f"Updated {args.workstation_file}")
        return 0
    except (OSError, SyntaxError, ValueError, TypeError, KeyError) as error:
        print(f"cosmic export: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
