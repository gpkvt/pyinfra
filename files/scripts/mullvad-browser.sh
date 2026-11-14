#!/usr/bin/env bash
set -e

if (($# == 0)); then
    exec env GTK_CSD=1 MOZ_ENABLE_WAYLAND=1 /usr/lib/mullvad-browser/start-mullvad-browser
fi

URI="$1"

if [[ "$URI" == file://* ]]; then
    URI="${URI#file://}"
    URI=$(printf '%b' "${URI//%/\\x}")
fi

exec env GTK_CSD=1 MOZ_ENABLE_WAYLAND=1 /usr/lib/mullvad-browser/start-mullvad-browser "$URI"
