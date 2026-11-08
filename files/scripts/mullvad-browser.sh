#!/bin/bash
set -e

if [ -z "$1" ]; then
    GTK_CSD=1 MOZ_ENABLE_WAYLAND=1 /usr/lib/mullvad-browser/start-mullvad-browser
fi

URI="$1"

if [[ "$URI" == file://* ]]; then
    URI="${URI#file://}"
    URI=$(printf '%b' "${URI//%/\\x}")
fi

GTK_CSD=1 MOZ_ENABLE_WAYLAND=1 /usr/lib/mullvad-browser/start-mullvad-browser "$URI"
