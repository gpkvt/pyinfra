#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Translate EBU-TT-D subtitles from German to English.

Setup:
    python3 -m venv ~/translate-env
    source ~/translate-env/bin/activate
    pip install argostranslate lxml

Download the German -> English language package:
    python3 -c "
import argostranslate.package as pkg

pkg.update_package_index()
available = pkg.get_available_packages()
for p in available:
    if p.from_code == 'de' and p.to_code == 'en':
        pkg.install_from_path(p.download())
        break
"

Extracts subtitle cues from an EBU-TT-D XML file, translates them
using Argos Translate and exports them as an SRT file.
"""

import re
from pathlib import Path

from lxml import etree
from argostranslate import translate

# XML namespace for EBU-TT-D / TTML subtitles.
NS = {"tt": "http://www.w3.org/ns/ttml"}

# Input and output files.
SRC = Path("/home/gpkvt/Videos/evil_e/urn_ard_subtitle_8dea4edea1ab9214.xml")
OUT_SRT = Path("/home/gpkvt/Videos/evil_e/evil_e_en.srt")

# Subtitle formatting configuration.
MAX_LINE = 37          # Maximum subtitle line width.
MAX_LINES = 2          # Maximum number of subtitle lines.
SKIP_AUDIO_DESC = 0    # Set to 1 to preserve audio descriptions.


def is_audio_descriptor(text: str) -> bool:
    """
    Identify standalone audio descriptions.

    Recognizes descriptions enclosed in parentheses or asterisks,
    as well as music and sound-effect labels.

    Args:
        text: Original subtitle cue.

    Returns:
        True if the cue is an audio description.
    """
    if not SKIP_AUDIO_DESC:
        return False

    s = text.strip()

    # Parenthesized descriptions, e.g. "(schnieft)".
    if s.startswith("(") and s.endswith(")"):
        return True

    # Asterisk-delimited descriptions, e.g. "* Schüsse *".
    if s.startswith("*") and s.endswith("*"):
        return True

    # Common standalone music and sound descriptions.
    if re.fullmatch(
        r"(?:Musik|Musik spielt|Applaus|Gelächter|Lachen|Weinen|Seufzen|Stöhnen|Atmen|Schritte|Geräusche|Stille)",
        s,
        flags=re.IGNORECASE,
    ):
        return True

    return False


def translate_cue(text: str) -> str:
    """
    Translate a German subtitle cue into English.

    Audio descriptions can optionally be preserved without translation.
    Asterisk-delimited markers are restored after translation.

    Args:
        text: German subtitle cue.

    Returns:
        English translation or original text.
    """
    s = text.strip()

    if not s or is_audio_descriptor(s):
        return text

    # Preserve asterisk-delimited markers.
    marker = s.startswith("*") and s.endswith("*")
    body = s[1:-1].strip() if marker else s

    en = translate.translate(body, "de", "en").strip()

    return f"* {en} *" if marker else en


def wrap_sub_line(text: str) -> str:
    """
    Wrap subtitle text into at most MAX_LINES lines.

    Lines are kept within MAX_LINE characters whenever possible.
    Words are never split. If the text cannot fit into the
    configured limits, the remaining text is appended to the
    final line.

    Args:
        text: Translated subtitle text.

    Returns:
        Newline-separated subtitle text.
    """
    words = text.split()

    if not words:
        return ""

    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()

        if len(candidate) <= MAX_LINE:
            current = candidate
            continue

        if current:
            lines.append(current)

        if len(lines) >= MAX_LINES - 1:
            current = word
            break

        current = word

    # Append all remaining words to the final line.
    remaining = words[len(" ".join(lines).split()):]
    if remaining:
        current = " ".join(remaining)

    if current:
        lines.append(current)

    return "\n".join(lines[:MAX_LINES])


def ts(value: str) -> str:
    """
    Convert TTML timestamps to SRT timestamp notation.

    Args:
        value: Original TTML timestamp.

    Returns:
        Timestamp with comma as decimal separator.
    """
    return value.replace(".", ",")


def main() -> None:
    """
    Convert and translate the source TTML subtitle file.

    Extracts paragraph text and timing information, translates
    the cues, wraps the text and writes an UTF-8 SRT file.
    """
    tree = etree.parse(str(SRC))
    paras = tree.findall(".//tt:body//tt:p", NS)

    parts = []

    for i, p in enumerate(paras, 1):
        begin = p.get("begin")
        end = p.get("end")

        # Extract complete paragraph text.
        # TTML line breaks become spaces to preserve sentence context.
        raw = " ".join(
            t.strip()
            for t in p.itertext()
            if t.strip()
        )

        en = translate_cue(raw)
        wrapped = wrap_sub_line(en)

        parts.append(
            f"{i}\n"
            f"{ts(begin)} --> {ts(end)}\n"
            f"{wrapped}\n"
        )

    OUT_SRT.write_text(
        "\n".join(parts),
        encoding="utf-8",
    )

    print(f"Fertig: {OUT_SRT}")


if __name__ == "__main__":
    main()
