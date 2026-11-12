"""Helpers for Homepage configuration shared by deployment tasks."""

from copy import deepcopy
from urllib.parse import urlsplit


def homepage_api_exclusions(homepage_services):
    """Return configured Homepage API paths keyed by widget URL hostname."""
    exclusions = {}

    def visit(value):
        if isinstance(value, dict):
            widget = value.get("widget")
            if isinstance(widget, dict):
                url = widget.get("url")
                if isinstance(url, str):
                    parsed = urlsplit(url)
                    if parsed.hostname:
                        sablier = widget.get("sablier", {})
                        paths = sablier.get("api_paths", []) if isinstance(sablier, dict) else []
                        paths = [
                            path for path in paths
                            if isinstance(path, str) and path.startswith("/")
                        ]
                        if widget.get("type") == "customapi" and parsed.path:
                            paths.append(parsed.path)
                        if paths:
                            exclusions.setdefault(parsed.hostname.lower(), set()).update(paths)
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(homepage_services)
    return {hostname: sorted(paths) for hostname, paths in exclusions.items()}


def homepage_services_for_render(homepage_services):
    """Copy Homepage services and remove pyinfra-only Sablier metadata."""
    result = deepcopy(homepage_services)

    def visit(value):
        if isinstance(value, dict):
            widget = value.get("widget")
            if isinstance(widget, dict):
                widget.pop("sablier", None)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result
