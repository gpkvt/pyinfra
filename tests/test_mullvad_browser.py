"""Tests for the Mullvad Browser launcher wrapper."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "files" / "scripts" / "mullvad-browser.sh"


def _run_wrapper(tmp_path, arguments):
    """Run the wrapper against a fake browser executable."""
    browser_dir = tmp_path / "browser bin"
    browser_dir.mkdir()
    browser = browser_dir / "start-mullvad-browser"
    args_file = tmp_path / "arguments"
    env_file = tmp_path / "environment"
    browser.write_text(
        '#!/usr/bin/env bash\n'
        'printf "%s\\n" "$#" "$@" > "$ARGS_FILE"\n'
        'printf "%s\\n" "$GTK_CSD" "$MOZ_ENABLE_WAYLAND" > "$ENV_FILE"\n',
        encoding="utf-8",
    )
    browser.chmod(0o755)

    source = SOURCE.read_text(encoding="utf-8")
    source = source.replace(
        "/usr/lib/mullvad-browser/start-mullvad-browser",
        f'"{browser}"',
    )
    wrapper = tmp_path / "mullvad-browser"
    wrapper.write_text(source, encoding="utf-8")
    wrapper.chmod(0o755)

    env = os.environ.copy()
    env.update({
        "ARGS_FILE": str(args_file),
        "ENV_FILE": str(env_file),
    })
    result = subprocess.run(
        [str(wrapper), *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    return result, args_file, env_file


def test_mullvad_browser_without_uri_launches_once(tmp_path):
    result, args_file, env_file = _run_wrapper(tmp_path, [])

    assert result.returncode == 0
    assert args_file.read_text(encoding="utf-8").splitlines() == ["0"]
    assert env_file.read_text(encoding="utf-8").splitlines() == ["1", "1"]


def test_mullvad_browser_passes_uri_to_single_launch(tmp_path):
    uri = "https://example.org/path?a=b"
    result, args_file, _env_file = _run_wrapper(tmp_path, [uri])

    assert result.returncode == 0
    assert args_file.read_text(encoding="utf-8").splitlines() == ["1", uri]


def test_mullvad_browser_decodes_file_uri(tmp_path):
    uri = "file:///tmp/a%20b"
    result, args_file, _env_file = _run_wrapper(tmp_path, [uri])

    assert result.returncode == 0
    assert args_file.read_text(encoding="utf-8").splitlines() == ["1", "/tmp/a b"]
