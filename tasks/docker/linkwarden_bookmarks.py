"""Synchronize the authenticated Linkwarden account into Homepage bookmarks.

The task runs on the pyinfra controller before Homepage is rendered. It only
updates the explicitly managed section in group_data/@local.py and stores
favicon files in files/homepage/icons/.
"""
# pylint: disable=R0912,R0914
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from pprint import pformat

from pyinfra import host

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
        if not isinstance(data, dict) or not isinstance(data.get("links"), list):
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


def favicon_filename(url):
    """Create a stable, filesystem-safe favicon name."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    host_name = urllib.parse.urlsplit(url).hostname or "link"
    host_name = re.sub(r"[^a-zA-Z0-9.-]", "-", host_name).lower()
    return f"linkwarden-{host_name}-{digest}.ico"


def download_favicon(base_url, target_url, token, destination):
    """Download a bounded favicon and write only when its bytes changed."""
    endpoint = f"{base_url}/api/v1/getFavicon?{urllib.parse.urlencode({'url': target_url})}"
    request = urllib.request.Request(
        endpoint,
        headers={"Authorization": f"Bearer {token}", "Accept": "image/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            content = response.read(MAX_FAVICON_SIZE + 1)
        if len(content) > MAX_FAVICON_SIZE or not content_type.startswith("image/"):
            return None
        if not content:
            return None
    except (OSError, urllib.error.URLError, ValueError):
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or destination.read_bytes() != content:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
    return f"/icons/{destination.name}"


def build_bookmark_groups(links, base_url, token, icon_dir):
    """Build deterministic Homepage groups, de-duplicated by URL."""
    grouped = {}
    seen_urls = set()
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
        filename = favicon_filename(url)
        icon = download_favicon(base_url, url, token, icon_dir / filename)
        item = {"href": url}
        if icon:
            item["icon"] = icon
        grouped.setdefault(collection_name, []).append({name: [item]})
    return [
        {collection: sorted(items, key=lambda entry: next(iter(entry)).casefold())}
        for collection, items in sorted(grouped.items(), key=lambda pair: pair[0].casefold())
    ]


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
    rendered = "\n" + "\n".join(
        indentation + line for line in pformat(groups, width=100).splitlines()
    ) + "\n            "
    updated = source[:start] + rendered + source[end:]
    if updated != source:
        config_path.write_text(updated, encoding="utf-8")
        return True
    return False


def synchronize(config_path, icon_dir, domain, token):
    """Fetch a complete account snapshot, then update the managed source."""
    base_url = domain.strip().rstrip("/")
    if not base_url.startswith(("https://", "http://")):
        base_url = "https://" + base_url
    links = fetch_links(base_url, token)
    groups = build_bookmark_groups(links, base_url, token, icon_dir)
    return update_managed_bookmarks(config_path, groups)


docker = host.data.get("docker", {})
linkwarden = docker.get("linkwarden", {})
homepage = docker.get("homepage", {})
linkwarden_secrets = secrets.get("docker", {}).get("linkwarden", {})  # pylint: disable=undefined-variable
api_token = linkwarden_secrets.get("api_token")
if linkwarden and homepage and api_token:
    repository_root = Path(__file__).resolve().parents[2]
    synchronize(
        repository_root / "group_data" / "@local.py",
        repository_root / "files" / "homepage" / "icons",
        linkwarden.get("domain", "linkwarden.21x9.org"),
        api_token,
    )
