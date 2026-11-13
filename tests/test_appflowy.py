"""Static configuration checks for the AppFlowy deployment."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_appflowy_compose_uses_host_bind_mounts_and_loopback_only():
    """AppFlowy persists data below .docker and exposes only its local Nginx port."""
    compose = (
        ROOT / "templates/docker/appflowy/docker-compose.yml.j2"
    ).read_text()

    assert '"127.0.0.1:{{ port }}:80"' in compose
    assert '"{{ homedir }}/.docker/appflowy/postgres:/var/lib/postgresql/data"' in compose
    assert '"{{ homedir }}/.docker/appflowy/minio:/data"' in compose
    assert '"{{ homedir }}/.docker/appflowy/search:/var/lib/appflowy/keyword_index"' in compose
    assert "postgres_data:" not in compose
    assert "minio_data:" not in compose
    assert "keyword_index_data:" not in compose
    assert "appflowy_log_collector:" not in compose
    assert "appflowy_backup:" not in compose


def test_appflowy_services_receive_their_redis_urls():
    """Every AppFlowy component uses the Compose Redis service, not localhost."""
    compose = (
        ROOT / "templates/docker/appflowy/docker-compose.yml.j2"
    ).read_text()

    assert "APPFLOWY_REDIS_URI=${APPFLOWY_REDIS_URI}" in compose
    assert "AI_REDIS_URL=${AI_REDIS_URL}" in compose
    assert "APPFLOWY_WORKER_REDIS_URL=${APPFLOWY_WORKER_REDIS_URL}" in compose
    assert "APPFLOWY_INDEXER_REDIS_URL=${APPFLOWY_INDEXER_REDIS_URL}" in compose
    assert "APPFLOWY_SEARCH_REDIS_URL=${APPFLOWY_INDEXER_REDIS_URL}" in compose
    assert "redis://localhost:6379" not in compose


def test_appflowy_homepage_entry_is_link_only():
    """Homepage links to AppFlowy without adding an authenticated API widget."""
    local_config = runpy.run_path(str(ROOT / "group_data/@local.py"))
    homepage_services = local_config["docker"]["homepage"]["services"]
    appflowy_card = next(
        card["AppFlowy"]
        for group in homepage_services
        for card in group.get("Services", [])
        if "AppFlowy" in card
    )
    assert appflowy_card["href"] == "https://appflowy.21x9.org"
    assert "widget" not in appflowy_card


def test_appflowy_nginx_preserves_caddy_scheme_and_client_ip():
    """The AppFlowy Nginx proxy trusts Caddy's forwarded scheme and client address."""
    nginx = (
        ROOT / "templates/docker/appflowy/nginx.conf.j2"
    ).read_text()
    assert "map $http_x_forwarded_for $appflowy_client_ip" in nginx
    assert "map \"$http_x_forwarded_proto:$appflowy_form_object\"" in nginx
    assert "limit_req_zone $appflowy_client_ip" in nginx
    assert "proxy_set_header X-Forwarded-For $appflowy_client_ip;" in nginx
    assert "listen 443 ssl" not in nginx
    assert "ssl_certificate " not in nginx
