#!/usr/bin/env python3

"""
python3 -m venv ~/translate-env\nsource ~/translate-env/bin/activate
pip install argostranslate lxml

# Sprachpaket Deutsch -> Englisch herunterladen
python3 -c "
import argostranslate.package as pkg

pkg.update_package_index()\navailable = pkg.get_available_packages()
for p in available:
    if p.from_code == 'de' and p.to_code == 'en':
        pkg.install_from_path(p.download())
        break"
"""

import textwrap
from pathlib import Path
from lxml import etree
from argostranslate import translate

"""Translate EBU-TT-D subtitles DE -> EN with proper sentence context."""

NS = {"tt": "http://www.w3.org/ns/ttml"}
SRC = Path("/home/gpkvt/Videos/evil_e/urn_ard_subtitle_8dea4edea1ab9214.xml")
OUT_SRT = Path("/home/gpkvt/Videos/evil_e/evil_e_en.srt")
MAX_LINE = 37          # typische Untertitel-Zeilenbreite
MAX_LINES = 2          # SRT liest sich mit 2 Zeilen am besten
SKIP_AUDIO_DESC = 0

def is_audio_descriptor(text: str) -> bool:
    """Reine Musik-/Atmo-Zeilen unver.ndert lassen."""
    if not SKIP_AUDIO_DESC:
        return False
    s = text.strip()
    if s.startswith("."):
        return True
    # kurze Klammer-/Stern-Deskriptoren wie "* Sch.sse *", "(schnieft)"
    # core = s.strip("*() ")
    if not s.startswith("*") and not s.startswith("("):
        return False
    return False

def translate_cue(text: str) -> str:
    s = text.strip()
    if not s or is_audio_descriptor(s):
        return text
    # Einspieler-Marker * ... * abtrennen
    marker = s.startswith("*") and s.rstrip().endswith("*")
    body = s[1:-1].strip() if marker else s
    en = translate.translate(body, "de", "en").strip()
    return f"* {en} *" if marker else en

def wrap_sub_line(text: str) -> str:
    """Bricht Text in Untertitel-Zeilen . MAX_LINE Zeichen um, max. MAX_LINES."""
    wrapped = textwrap.wrap(text, width=MAX_LINE, break_long_words=False)
    if len(wrapped) <= MAX_LINES:
        return "\n".join(wrapped)
    # Notfall: gleichm..iger statt sauber umbrechen
    mid = len(wrapped) // 2
    return "\n".join([" ".join(wrapped[:mid]), " ".join(wrapped[mid:])])

def ts(v: str) -> str:
    return v.replace(".", ",")

def main():
    tree = etree.parse(str(SRC))
    paras = tree.findall(".//tt:body//tt:p", NS)
    parts = []
    for i, p in enumerate(paras, 1):
        begin, end = p.get("begin"), p.get("end")
        # Ganzen Textinhalt des <p> holen . <tt:br/> wird zu Leerzeichen,
        # dadurch bleibt die Satzstruktur f.r die .bersetzung intakt
        raw = " ".join(t.strip() for t in p.itertext() if t.strip())
        en = translate_cue(raw)
        wrapped = wrap_sub_line(en)
        parts.append(f"{i}\n{ts(begin)} --> {ts(end)}\n{wrapped}\n")
    OUT_SRT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Fertig: {OUT_SRT}")

if __name__ == "__main__":
    main()
