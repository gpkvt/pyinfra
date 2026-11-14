"""Tests for the runas X11 privilege helper."""

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNAS = ROOT / "files" / "scripts" / "runas"


def _environment(tmp_path, command_exit=0):
    """Create logging stand-ins for xhost and the requested command."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    xhost_log = tmp_path / "xhost.log"
    command_log = tmp_path / "command.log"

    xhost = bin_dir / "xhost"
    xhost.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$*" >> "$XHOST_LOG"\n',
        encoding="utf-8",
    )
    xhost.chmod(0o755)

    command = bin_dir / "test-command"
    command.write_text(
        '#!/bin/sh\nprintf "<%s>\\n" "$@" > "$COMMAND_LOG"\n'
        'exit "$COMMAND_EXIT"\n',
        encoding="utf-8",
    )
    command.chmod(0o755)

    env = os.environ.copy()
    env.update({
        "PATH": f"{bin_dir}:{env['PATH']}",
        "XHOST_LOG": str(xhost_log),
        "COMMAND_LOG": str(command_log),
        "COMMAND_EXIT": str(command_exit),
    })
    return env, xhost_log, command_log


def test_runas_preserves_arguments_and_revokes_root_access(tmp_path):
    env, xhost_log, command_log = _environment(tmp_path)

    result = subprocess.run(
        [str(RUNAS), "test-command", "argument with spaces", "--flag"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    assert command_log.read_text(encoding="utf-8").splitlines() == [
        "<argument with spaces>",
        "<--flag>",
    ]
    assert xhost_log.read_text(encoding="utf-8").splitlines() == [
        "+SI:localuser:root",
        "-SI:localuser:root",
    ]


def test_runas_revokes_root_access_when_command_fails(tmp_path):
    env, xhost_log, command_log = _environment(tmp_path, command_exit=7)

    result = subprocess.run(
        [str(RUNAS), "test-command", "argument"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 7
    assert command_log.read_text(encoding="utf-8").splitlines() == ["<argument>"]
    assert xhost_log.read_text(encoding="utf-8").splitlines() == [
        "+SI:localuser:root",
        "-SI:localuser:root",
    ]


def test_runas_requires_a_command_without_changing_xhost_access(tmp_path):
    env, xhost_log, command_log = _environment(tmp_path)

    result = subprocess.run(
        [str(RUNAS)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 64
    assert "Usage:" in result.stderr
    assert not xhost_log.exists()
    assert not command_log.exists()
