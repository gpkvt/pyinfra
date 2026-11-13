"""Manually synchronize the authenticated Linkwarden account into Homepage bookmarks.

Run this utility explicitly from the repository checkout. It updates only the
managed section in group_data/@local.py and stores favicons in files/homepage/icons/.
Changes should be reviewed and committed separately from infrastructure deployment.
"""
# pylint: disable=R0912,R0914
import ast
import hashlib
import html.parser
import json
import argparse
import os
import re
import runpy
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from pprint import pformat


BEGIN = "# BEGIN LINKWARDEN BOOKMARKS (managed)"
END = "# END LINKWARDEN BOOKMARKS (managed)"
TIMEOUT = 20
MAX_FAVICON_SIZE = 1024 * 1024


def api_json(url, token):
    """Return a JSON API response or fail without changing managed data."""
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        if response.status != 200:
            raise RuntimeError(f"Linkwarden API returned HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def fetch_links(base_url, token):
    """Fetch all pages and reject malformed or repeated cursors."""
    links = []
    cursor = None
    seen_cursors = set()
    while True:
        query = {} if cursor is None else {"cursor": cursor}
        url = f"{base_url}/api/v1/search"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        payload = api_json(url, token)
        data = payload.get("data")
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("links"), list)
            or "nextCursor" not in data
        ):
            raise RuntimeError("Unexpected Linkwarden search response")
        links.extend(data["links"])
        next_cursor = data.get("nextCursor")
        if next_cursor in (None, "", 0):
            return links
        marker = str(next_cursor)
        if marker in seen_cursors:
            raise RuntimeError("Linkwarden pagination cursor repeated")
        seen_cursors.add(marker)
        cursor = next_cursor


FAVICON_EXTENSIONS = {
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "image/ico": ".ico",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def favicon_extension(content_type):
    """Return a supported filename extension for an image MIME type."""
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return FAVICON_EXTENSIONS.get(media_type)


def favicon_origin(url):
    """Return the normalized website origin used to share one favicon per site."""
    parsed = urllib.parse.urlsplit(url)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def favicon_filename(url, extension, prefix="linkwarden"):
    """Create a stable favicon name based on website origin, not bookmark URL."""
    origin = favicon_origin(url)
    digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()[:16]
    host_name = urllib.parse.urlsplit(origin).hostname or "link"
    host_name = re.sub(r"[^a-zA-Z0-9.-]", "-", host_name).lower()
    return f"{prefix}-{host_name}-{digest}{extension}"


class FaviconHTMLParser(html.parser.HTMLParser):
    """Collect icon links from a website's HTML head."""

    def __init__(self):
        super().__init__()
        self.icons = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "link":
            return
        attributes = dict(attrs)
        rel = attributes.get("rel", "").lower().split()
        href = attributes.get("href")
        if href and any("icon" in value for value in rel):
            self.icons.append(href)


def discover_favicon_urls(target_url):
    """Discover declared icon URLs, then try the conventional favicon path."""
    request = urllib.request.Request(
        target_url,
        headers={"User-Agent": "pyinfra-linkwarden-favicon-sync/1.0", "Accept": "text/html"},
    )
    candidates = []
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" in content_type or not content_type:
                document = response.read(MAX_FAVICON_SIZE + 1)
                if len(document) <= MAX_FAVICON_SIZE:
                    parser = FaviconHTMLParser()
                    parser.feed(document.decode("utf-8", errors="replace"))
                    candidates = [
                        urllib.parse.urljoin(response.geturl(), href)
                        for href in parser.icons
                    ]
    except (OSError, urllib.error.URLError, ValueError):
        pass
    candidates.append(urllib.parse.urljoin(target_url, "/favicon.ico"))
    return list(dict.fromkeys(
        url for url in candidates
        if urllib.parse.urlsplit(url).scheme in ("http", "https")
    ))


def _download_image(url, headers=None):
    """Fetch a bounded image response, returning (content, extension)."""
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "pyinfra/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            content = response.read(MAX_FAVICON_SIZE + 1)
        extension = favicon_extension(content_type)
        if len(content) > MAX_FAVICON_SIZE or not content or not extension:
            return None
        return content, extension
    except (OSError, urllib.error.URLError, ValueError):
        return None


def download_favicon(
    base_url, target_url, token, destination, prefix="linkwarden", icon_cache=None
):
    """Discover, cache and download one favicon per website origin."""
    origin = favicon_origin(target_url)
    if icon_cache is not None and origin in icon_cache:
        return icon_cache[origin]

    destination.parent.mkdir(parents=True, exist_ok=True)
    host_digest = hashlib.sha256(origin.encode("utf-8")).hexdigest()[:16]
    host_name = re.sub(
        r"[^a-zA-Z0-9.-]", "-", urllib.parse.urlsplit(origin).hostname or "link"
    ).lower()
    existing = sorted(destination.parent.glob(f"{prefix}-{host_name}-{host_digest}.*"))
    if existing:
        result = f"/icons/{existing[0].name}"
        if icon_cache is not None:
            icon_cache[origin] = result
        return result

    downloaded = None
    for favicon_url in discover_favicon_urls(target_url):
        downloaded = _download_image(favicon_url)
        if downloaded:
            break

    if not downloaded:
        endpoint = (
            f"{base_url}/api/v1/getFavicon?"
            f"{urllib.parse.urlencode({'url': target_url})}"
        )
        downloaded = _download_image(
            endpoint,
            {"Authorization": f"Bearer {token}", "Accept": "image/*"},
        )
    if not downloaded:
        return None

    content, extension = downloaded
    destination = destination.with_name(favicon_filename(target_url, extension, prefix))
    if not destination.exists() or destination.read_bytes() != content:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
    result = f"/icons/{destination.name}"
    if icon_cache is not None:
        icon_cache[origin] = result
    return result


def build_bookmark_groups(
    links, base_url, token, icon_dir, download_icons=True, icon_cache=None
):
    """Build deterministic Homepage groups, de-duplicated by URL."""
    grouped = {}
    seen_urls = set()
    icon_cache = icon_cache if icon_cache is not None else {}
    for link in links:
        if not isinstance(link, dict) or link.get("type") != "url":
            continue
        url = link.get("url")
        name = (link.get("name") or url or "").strip()
        collection = link.get("collection")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            continue
        if not name or not isinstance(collection, dict):
            continue
        collection_name = (collection.get("name") or "Unorganized").strip()
        if not collection_name or url in seen_urls:
            continue
        seen_urls.add(url)
        filename = favicon_filename(url, ".ico")
        icon = (
            download_favicon(
                base_url, url, token, icon_dir / filename, icon_cache=icon_cache
            )
            if download_icons else None
        )
        item = {"href": url}
        if icon:
            item["icon"] = icon
        grouped.setdefault(collection_name, []).append({name: [item]})
    return [
        {collection: sorted(items, key=lambda entry: next(iter(entry)).casefold())}
        for collection, items in sorted(grouped.items(), key=lambda pair: pair[0].casefold())
    ]



def _service_entries(services):
    """Yield (service name, mutable configuration) pairs from Homepage groups."""
    for group in services if isinstance(services, list) else []:
        if not isinstance(group, dict):
            continue
        for entries in group.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                for name, config in entry.items():
                    if isinstance(config, dict):
                        yield name, config


def collect_service_favicons(
    services, base_url, token, icon_dir, download_icons=True, icon_cache=None
):
    """Download missing Homepage service icons and return their config references."""
    icon_references = {}
    icon_cache = icon_cache if icon_cache is not None else {}
    for name, service in _service_entries(services):
        href = service.get("href")
        current_icon = service.get("icon")
        if not isinstance(href, str) or not href.startswith(("https://", "http://")):
            continue
        if isinstance(current_icon, str) and current_icon.startswith("/icons/"):
            existing_icon = icon_dir / current_icon.removeprefix("/icons/")
            if existing_icon.is_file():
                continue
        elif current_icon:
            # Preserve explicit Homepage icon identifiers and external icon URLs.
            continue
        if not download_icons:
            continue
        filename = icon_dir / favicon_filename(href, ".ico", prefix="homepage")
        icon = download_favicon(
            base_url, href, token, filename, prefix="homepage",
            icon_cache=icon_cache,
        )
        if icon:
            icon_references[name] = icon
    return icon_references


def update_service_icon_references(config_path, icon_references):
    """Update only Homepage service icon values in the Python inventory source."""
    if not icon_references:
        return False
    source = config_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docker_node = next(
        (
            node.value for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "docker"
                    for target in node.targets)
            and isinstance(node.value, ast.Dict)
        ),
        None,
    )
    if docker_node is None:
        raise RuntimeError("Could not locate docker configuration in inventory")

    def dict_value(node, key):
        for key_node, value_node in zip(node.keys, node.values):
            if isinstance(key_node, ast.Constant) and key_node.value == key:
                return value_node
        return None

    homepage_node = dict_value(docker_node, "homepage")
    services_node = dict_value(homepage_node, "services") if isinstance(homepage_node, ast.Dict) else None
    if not isinstance(services_node, ast.List):
        raise RuntimeError("Could not locate Homepage services in inventory")

    line_offsets = []
    offset = 0
    for line in source.splitlines(keepends=True):
        line_offsets.append(offset)
        offset += len(line)
    edits = []
    for group in services_node.elts:
        if not isinstance(group, ast.Dict):
            continue
        for entries in group.values:
            if not isinstance(entries, ast.List):
                continue
            for entry in entries.elts:
                if not isinstance(entry, ast.Dict):
                    continue
                for name_node, service_node in zip(entry.keys, entry.values):
                    if not isinstance(name_node, ast.Constant) or name_node.value not in icon_references:
                        continue
                    if not isinstance(service_node, ast.Dict):
                        continue
                    icon_node = dict_value(service_node, "icon")
                    value = repr(icon_references[name_node.value])
                    if icon_node is not None:
                        start = line_offsets[icon_node.lineno - 1] + icon_node.col_offset
                        end = line_offsets[icon_node.end_lineno - 1] + icon_node.end_col_offset
                        edits.append((start, end, value))
                    else:
                        line_start = line_offsets[service_node.lineno - 1]
                        line = source[line_start:source.find("\n", line_start)]
                        indent = line[:len(line) - len(line.lstrip())]
                        insert_at = line_start + service_node.col_offset + 1
                        addition = f"\n{indent}    \"icon\": {value},"
                        edits.append((insert_at, insert_at, addition))
    if len(edits) != len(icon_references):
        raise RuntimeError(
            f"Could not update all Homepage service icons ({len(edits)}/{len(icon_references)})"
        )
    updated = source
    for start, end, value in sorted(edits, reverse=True):
        updated = updated[:start] + value + updated[end:]
    if updated != source:
        config_path.write_text(updated, encoding="utf-8")
        return True
    return False


def update_managed_bookmarks(config_path, groups):
    """Replace only the marked managed section; leave all other source intact."""
    source = config_path.read_text(encoding="utf-8")
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise RuntimeError("Homepage bookmarks need exactly one Linkwarden marker pair")
    start = source.index(BEGIN) + len(BEGIN)
    end = source.index(END)
    if end < start:
        raise RuntimeError("Linkwarden bookmark markers are out of order")
    indentation = "            "
    rendered_groups = [
        "\n".join(
            indentation + line for line in pformat(group, width=100).splitlines()
        )
        for group in groups
    ]
    rendered = "\n" + ",\n".join(rendered_groups) + "\n            "
    updated = source[:start] + rendered + source[end:]
    if updated != source:
        config_path.write_text(updated, encoding="utf-8")
        return True
    return False


def synchronize(config_path, icon_dir, domain, token, services=None, dry_run=False):
    """Synchronize Linkwarden bookmarks and missing Homepage service icons."""
    base_url = domain.strip().rstrip("/")
    if not base_url.startswith(("https://", "http://")):
        base_url = "https://" + base_url
    links = fetch_links(base_url, token)
    icon_cache = {}
    groups = build_bookmark_groups(
        links, base_url, token, icon_dir, download_icons=not dry_run,
        icon_cache=icon_cache,
    )
    if dry_run:
        print(json.dumps(groups, indent=4, ensure_ascii=False))
        print(f"Dry run: {sum(len(items) for group in groups for items in group.values())} bookmarks; no files changed.")
        return False
    service_icons = collect_service_favicons(
        services or [], base_url, token, icon_dir, icon_cache=icon_cache
    )
    bookmarks_changed = update_managed_bookmarks(config_path, groups)
    icons_changed = update_service_icon_references(config_path, service_icons)
    icons_removed = cleanup_unused_favicons(config_path, icon_dir)
    return bookmarks_changed or icons_changed or icons_removed



def cleanup_unused_favicons(config_path, icon_dir):
    """Remove unreferenced favicons managed by this synchronization script."""
    if not icon_dir.is_dir():
        return False

    tree = ast.parse(config_path.read_text(encoding="utf-8"))
    referenced = {
        Path(node.value.removeprefix("/icons/")).name
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("/icons/")
    }

    removed = False
    for prefix in ("linkwarden-", "homepage-"):
        for icon in icon_dir.glob(f"{prefix}*"):
            if icon.is_file() and icon.name not in referenced:
                icon.unlink()
                removed = True
    return removed


def resolve_sync_settings(config, secret_data):
    """Resolve Linkwarden and Homepage settings from host data and secrets."""
    docker_config = config.get("docker", {})
    docker_secrets = secret_data.get("docker", {})
    linkwarden = docker_config.get("linkwarden", {})
    homepage = docker_config.get("homepage", {})
    linkwarden_secrets = docker_secrets.get("linkwarden", {})
    homepage_environment = docker_secrets.get("homepage", {}).get("environment", {})

    token = (
        linkwarden_secrets.get("api_key")
        or homepage_environment.get("HOMEPAGE_VAR_LINKWARDEN_API_KEY")
    )
    if "linkwarden" not in docker_config:
        raise ValueError("docker.linkwarden is missing from group_data/@local.py")
    if "homepage" not in docker_config:
        raise ValueError("docker.homepage is missing from group_data/@local.py")
    if not token:
        raise ValueError(
            "Missing Linkwarden API key: set secrets.docker.linkwarden.api_key "
            "or secrets.docker.homepage.environment.HOMEPAGE_VAR_LINKWARDEN_API_KEY"
        )
    return linkwarden.get("domain", "linkwarden.21x9.org"), token


def select_local_secrets(secret_document, selector):
    """Select secrets for the local inventory target, not the system hostname."""
    return selector(secret_document, "@local")


def main():
    """Run a manual synchronization from the repository checkout."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true",
        help="fetch and display proposed bookmarks without downloading icons or changing files",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    config = runpy.run_path(str(root / "group_data" / "@local.py"))
    decrypted = subprocess.run(
        ["gpg", "--quiet", "--decrypt", str(root / "secrets.json.gpg")],
        check=True, capture_output=True, text=True,
    )
    from common import select_host_secrets  # pylint: disable=import-outside-toplevel
    secret_data = select_local_secrets(json.loads(decrypted.stdout), select_host_secrets)
    try:
        domain, token = resolve_sync_settings(config, secret_data)
    except ValueError as error:
        parser.error(str(error))
    synchronize(
        root / "group_data" / "@local.py",
        root / "files" / "homepage" / "icons",
        domain, token,
        services=config.get("docker", {}).get("homepage", {}).get("services", []),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

