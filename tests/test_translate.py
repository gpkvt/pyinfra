"""Behavioral tests for the standalone TTML-to-SRT translator."""

import sys
import types

import pytest

from conftest import load_module


@pytest.fixture
def translator(monkeypatch):
    """Load the utility with deterministic translation and XML dependencies."""
    argos = types.ModuleType("argostranslate")
    argos.translate = types.SimpleNamespace(
        translate=lambda text, source, target: f"EN:{text}"
    )
    lxml = types.ModuleType("lxml")
    lxml.etree = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "argostranslate", argos)
    monkeypatch.setitem(sys.modules, "lxml", lxml)
    return load_module("files/scripts/translate.py", "tested_translate")


def test_is_audio_descriptor_respects_configuration(translator):
    assert translator.is_audio_descriptor("(Applaus)") is False
    translator.SKIP_AUDIO_DESC = 1
    assert translator.is_audio_descriptor("(Applaus)") is True
    assert translator.is_audio_descriptor("* Schüsse *") is True
    assert translator.is_audio_descriptor("Musik spielt") is True
    assert translator.is_audio_descriptor("Das ist gesprochener Text") is False


def test_translate_cue_preserves_empty_and_audio_description_text(translator):
    assert translator.translate_cue("   ") == "   "
    translator.SKIP_AUDIO_DESC = 1
    assert translator.translate_cue("(Applaus)") == "(Applaus)"


def test_translate_cue_translates_and_restores_asterisk_markers(translator):
    assert translator.translate_cue("  Guten Morgen  ") == "EN:Guten Morgen"
    assert translator.translate_cue("* Guten Morgen *") == "* EN:Guten Morgen *"


def test_wrap_sub_line_handles_empty_short_and_overflow_text(translator):
    assert translator.wrap_sub_line("") == ""
    assert translator.wrap_sub_line("Short subtitle") == "Short subtitle"

    words = ["word"] * 30
    result = translator.wrap_sub_line(" ".join(words))
    lines = result.splitlines()
    assert len(lines) == translator.MAX_LINES
    assert " ".join(lines).split() == words


def test_wrap_sub_line_never_splits_an_overlong_word(translator):
    word = "x" * (translator.MAX_LINE + 1)
    assert translator.wrap_sub_line(word) == word


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("00:00:01.500", "00:00:01,500"),
        ("00:01:02", "00:01:02"),
        ("00:00:01.500.250", "00:00:01,500,250"),
    ],
)
def test_ts_converts_decimal_separators(value, expected, translator):
    assert translator.ts(value) == expected


def test_main_writes_numbered_srt_cues_from_ttml(translator, monkeypatch, tmp_path):
    class Paragraph:
        def __init__(self, begin, end, text):
            self.attributes = {"begin": begin, "end": end}
            self.text = text

        def get(self, name):
            return self.attributes.get(name)

        def itertext(self):
            return iter([self.text])

    class Tree:
        def findall(self, path, namespace):
            assert path == ".//tt:body//tt:p"
            assert namespace == translator.NS
            return [
                Paragraph("00:00:01.000", "00:00:02.000", "Guten Morgen"),
                Paragraph("00:00:03.000", "00:00:04.000", "Auf Wiedersehen"),
            ]

    output = tmp_path / "translated.srt"
    monkeypatch.setattr(translator, "SRC", tmp_path / "source.xml")
    monkeypatch.setattr(translator, "OUT_SRT", output)
    monkeypatch.setattr(translator.etree, "parse", lambda _path: Tree())

    translator.main()

    assert output.read_text(encoding="utf-8") == (
        "1\n00:00:01,000 --> 00:00:02,000\nEN:Guten Morgen\n\n"
        "2\n00:00:03,000 --> 00:00:04,000\nEN:Auf Wiedersehen\n"
    )
