"""Behavioral tests for the HyFetch LiMusic now-playing helper."""

import os
import subprocess
from pathlib import Path


HELPER = Path(__file__).parents[1] / "files" / "hyfetch-song"


def run_helper(tmp_path, playerctl_source=None):
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    if playerctl_source is not None:
        playerctl = binary_dir / "playerctl"
        playerctl.write_text(playerctl_source, encoding="utf-8")
        playerctl.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{binary_dir}:{env.get('PATH', '')}"
    return subprocess.run(
        ["bash", str(HELPER)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_helper_prints_only_the_playing_limusic_track(tmp_path):
    result = run_helper(
        tmp_path,
        """#!/usr/bin/env bash
case "$*" in
    -l) printf '%s\\n' 'spotify' 'org.mpris.MediaPlayer2.LiMusic' ;;
    *status) printf '%s\\n' 'Playing' ;;
    *metadata*) printf '%s\\n' 'Artist — Track' ;;
esac
""",
    )

    assert result.returncode == 0
    assert result.stdout == "Artist — Track\\n"
    assert result.stderr == ""


def test_helper_is_silent_when_limusic_is_not_playing(tmp_path):
    result = run_helper(
        tmp_path,
        """#!/usr/bin/env bash
case "$*" in
    -l) printf '%s\\n' 'org.mpris.MediaPlayer2.LiMusic' ;;
    *status) printf '%s\\n' 'Paused' ;;
    *metadata*) printf '%s\\n' 'must not be printed' ;;
esac
""",
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_helper_is_silent_when_limusic_is_not_available(tmp_path):
    result = run_helper(tmp_path)

    assert result.returncode == 0
    assert result.stdout == ""
