""" Docker container """

from pyinfra import host, local

container = host.data.get("docker", {})

if "miniflux" in container:
    local.include("tasks/docker/miniflux.py")

if "timetagger" in container:
    local.include("tasks/docker/timetagger.py")

if "grav" in container:
    local.include("tasks/docker/grav.py")

if "forgejo" in container:
    local.include("tasks/docker/forgejo.py")

if "portainer" in container:
    local.include("tasks/docker/portainer.py")

if "tasmoadmin" in container:
    local.include("tasks/docker/tasmoadmin.py")

if "wallabag" in container:
    local.include("tasks/docker/wallabag.py")

if "vaultwarden" in container:
    local.include("tasks/docker/vaultwarden.py")

if "nocodb" in container:
    local.include("tasks/docker/nocodb.py")

if "linkwarden" in container:
    local.include("tasks/docker/linkwarden.py")

if "homepage" in container:
    local.include("tasks/docker/homepage.py")
