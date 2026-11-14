"""Tests for the supported COSMIC configuration exporter."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "files" / "scripts" / "export_cosmic_config.py"
SPEC = importlib.util.spec_from_file_location("export_cosmic_config", SCRIPT)
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


def test_export_supported_reads_only_managed_keys(tmp_path):
    def put(key, value):
        path = tmp_path.joinpath(*key.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    put("com.system76.CosmicTheme.Mode/v1/is_dark", "true\n")
    put("com.system76.CosmicComp/v1/autotile", "false\n")
    put("com.system76.CosmicComp/v1/unmanaged_setting", "ignored\n")
    exported = EXPORTER.export_supported(tmp_path)
    assert exported == {
        "appearance": {"mode": "dark"},
        "window_management": {"autotile": False},
    }


def test_export_supported_preserves_raw_ron_and_applet_layout(tmp_path):
    def put(key, value):
        path = tmp_path.joinpath(*key.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    put("com.system76.CosmicComp/v1/input_default", "Some((speed: 1.0,))\n")
    put("com.system76.CosmicPanel.Dock/v1/plugins_wings",
        'Some((["left.app"], ["right.app"],))\n')
    put("com.system76.CosmicPanel.Dock/v1/plugins_center", 'Some(["center.app"])\n')
    exported = EXPORTER.export_supported(tmp_path)
    assert exported["input"]["default"] == "Some((speed: 1.0,))"
    assert exported["dock"]["applets"] == {
        "left": ["left.app"], "right": ["right.app"], "center": ["center.app"]
    }


def test_update_local_config_preserves_other_sections_and_management_flags():
    source = (
        'workstation = {"cosmic": {"enabled": False, "appearance": '
        '{"enabled": True, "mode": "light"}}, "desktop": {"enabled": True}}\n'
        'other = {"keep": True}\n'
    )
    updated = EXPORTER.update_local_config(source, {"appearance": {"mode": "dark"}})
    assert "'mode': 'dark'" in updated
    assert "'enabled': False" in updated
    assert '"desktop"' in updated
    assert 'other = {"keep": True}' in updated


def test_update_local_config_requires_unambiguous_literal_target():
    with pytest.raises(ValueError):
        EXPORTER.update_local_config("workstation = load_config()\n", {"appearance": {"mode": "dark"}})
    with pytest.raises(ValueError):
        EXPORTER.update_local_config("workstation = {}\n", {"appearance": {"mode": "dark"}})


def test_update_local_config_is_idempotent():
    source = 'workstation = {"cosmic": {"appearance": {"enabled": True}}}\n'
    first = EXPORTER.update_local_config(source, {"appearance": {"mode": "dark"}})
    assert EXPORTER.update_local_config(first, {"appearance": {"mode": "dark"}}) == first


def test_parse_applets_accepts_cosmic_ron_trailing_commas():
    assert EXPORTER.parse_applets(
        'Some(([\n    "left.app",\n], [\n    "right.app",\n]))'
    ) == {"left": ["left.app"], "right": ["right.app"]}
    assert EXPORTER.parse_center(
        'Some([\n    "center.app",\n])'
    ) == ["center.app"]


def test_parse_applets_rejects_other_ron_syntax():
    with pytest.raises(ValueError):
        EXPORTER.parse_applets("Some((None, None))")



def test_main_dry_run_does_not_write(tmp_path, capsys):
    config_dir = tmp_path / "cosmic"
    config_dir.mkdir()
    setting = config_dir / "com.system76.CosmicTheme.Mode" / "v1" / "is_dark"
    setting.parent.mkdir(parents=True)
    setting.write_text("true\n", encoding="utf-8")
    local_file = tmp_path / "@local.py"
    original = 'workstation = {"cosmic": {"appearance": {"enabled": True}}}\n'
    local_file.write_text(original, encoding="utf-8")

    assert EXPORTER.main([
        "--config-dir", str(config_dir),
        "--local-file", str(local_file),
        "--dry-run",
    ]) == 0
    assert local_file.read_text(encoding="utf-8") == original
    assert "'mode': 'dark'" in capsys.readouterr().out

def test_convert_value_maps_dark_mode_values():
    assert EXPORTER.convert_value("true", "mode") == "dark"
    assert EXPORTER.convert_value("false", "mode") == "light"



def test_main_defaults_to_workstation_py(tmp_path, monkeypatch, capsys):
    config_dir = tmp_path / "cosmic"
    config_dir.mkdir()
    setting = config_dir / "com.system76.CosmicTheme.Mode" / "v1" / "is_dark"
    setting.parent.mkdir(parents=True)
    setting.write_text("true\\n", encoding="utf-8")
    workstation_file = tmp_path / "workstation.py"
    original = 'workstation = {"cosmic": {"appearance": {"enabled": True}}}\\n'
    workstation_file.write_text(original, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert EXPORTER.main(["--config-dir", str(config_dir), "--dry-run"]) == 0
    assert workstation_file.read_text(encoding="utf-8") == original
    assert "'mode': 'dark'" in capsys.readouterr().out


def test_main_accepts_workstation_file_option(tmp_path, capsys):
    config_dir = tmp_path / "cosmic"
    config_dir.mkdir()
    setting = config_dir / "com.system76.CosmicTheme.Mode" / "v1" / "is_dark"
    setting.parent.mkdir(parents=True)
    setting.write_text("true\\n", encoding="utf-8")
    workstation_file = tmp_path / "custom-workstation.py"
    original = 'workstation = {"cosmic": {"appearance": {"enabled": True}}}\\n'
    workstation_file.write_text(original, encoding="utf-8")

    assert EXPORTER.main([
        "--config-dir", str(config_dir),
        "--workstation-file", str(workstation_file),
        "--dry-run",
    ]) == 0
    assert workstation_file.read_text(encoding="utf-8") == original
    assert "'mode': 'dark'" in capsys.readouterr().out
