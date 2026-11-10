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
