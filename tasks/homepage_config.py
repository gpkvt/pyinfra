"""Helpers for Homepage configuration shared by deployment tasks."""

from urllib.parse import urlsplit


def homepage_api_exclusions(homepage_services):
    """Return API path patterns keyed by Homepage widget hostname."""
    exclusions = {}

    def visit(value):
        if isinstance(value, dict):
            widget = value.get("widget")
            if isinstance(widget, dict):
                url = widget.get("url")
                if isinstance(url, str):
                    parsed = urlsplit(url)
                    if parsed.hostname:
                        paths = exclusions.setdefault(parsed.hostname.lower(), set())
                        # Built-in Homepage widgets use these common API prefixes.
                        paths.update(("/api/*", "/v1/*"))
                        # Custom API widgets may use paths outside those prefixes.
                        if widget.get("type") == "customapi" and parsed.path:
                            paths.add(parsed.path)
            for child in value.values():
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)

    visit(homepage_services)
    return {hostname: sorted(paths) for hostname, paths in exclusions.items()}
