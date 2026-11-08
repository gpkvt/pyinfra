#!/usr/bin/env bash
#
# extract-md.sh . Extrahiert per XPath ein Titel- und ein Hauptelement
#                 aus einer Webseite und schreibt sie als Markdown-Datei.
#
# Abh.ngigkeiten:
#   curl            (Paket: curl)
#   xmllint         (Paket: libxml2-utils)
#   html2markdown   (Paket: python-html2text)
#
# Aufruf:
#   ./extract-md.sh <URL> <TITEL_XPATH> <HAUPT_XPATH> <AUSGABEDATEI>
#
set -euo pipefail

# ---------------------------------------------------------------------------
# 0. Argumentpr.fung
# ---------------------------------------------------------------------------
if [[ $# -ne 4 ]]; then
    echo "Usage: $0 <URL> <TITLE_XPATH> <MAIN_XPATH> <OUTPUT_FILE>" >&2
    echo "Beispiel:" >&2
    echo "  $0 'https://example.org/artikel' \\" >&2
    echo "     '//h1' '//article' '/tmp/artikel.md'" >&2
    exit 64   # EX_USAGE
fi

URL="$1"
XPATH_TITLE="$2"
XPATH_MAIN="$3"
OUTFILE="$4"

# ---------------------------------------------------------------------------
# 1. Abh.ngigkeiten pr.fen
# ---------------------------------------------------------------------------
for bin in curl xmllint html2markdown; do
    if ! command -v "$bin" >/dev/null 2>&1; then
        echo "FEHLER: '$bin' nicht gefunden." >&2
        case "$bin" in
            xmllint)       echo "  -> sudo apt install libxml2-utils" >&2 ;;
            html2markdown) echo "  -> sudo apt install python-html2text" >&2 ;;
            curl)          echo "  -> sudo apt install curl" >&2 ;;
        esac
        exit 69   # EX_UNAVAILABLE
    fi
done

# ---------------------------------------------------------------------------
# 2. Tempor.re Dateien anlegen und beim Exit aufr.umen
# ---------------------------------------------------------------------------
TMPDIR_RUN="$(mktemp -d)"
cleanup() { rm -rf "$TMPDIR_RUN"; }
trap cleanup EXIT

RAW_HTML="$TMPDIR_RUN/page.html"
FRAG_TITLE="$TMPDIR_RUN/title.frag"
FRAG_MAIN="$TMPDIR_RUN/main.frag"

# ---------------------------------------------------------------------------
# 3. Seite herunterladen
#    -L  Folgt Redirects
#    -sS Silent, aber Fehler auf stderr
#    --fail  HTTP-Fehler => Exit != 0
#    -A  User-Agent setzen (viele Seiten blocken den curl-Default)
# ---------------------------------------------------------------------------
echo "[1/4] Lade $URL" >&2
curl -L -sS --fail \
     -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' \
     -o "$RAW_HTML" \
     "$URL"

if [[ ! -s "$RAW_HTML" ]]; then
    echo "FEHLER: Heruntergeladene Datei ist leer." >&2
    exit 65   # EX_DATAERR
fi

# ---------------------------------------------------------------------------
# 4. XPath-Extraktion
#    --html   : HTML-Parser statt XML-Parser verwenden
#    --xpath  : Ausdruck auswerten, Ergebnis auf stdout
#    '-'      : Eingabe von stdin lesen
#
#    Hinweis: xmllint gibt bei leerem Nodeset Exit-Code 11 zur.ck.
#    Wir fangen das ab, damit 'set -e' nicht abbricht, und behandeln
#    ein leeres Ergebnis explizit.
# ---------------------------------------------------------------------------
extract_xpath() {
    local xpath_expr="$1"
    local infile="$2"
    local outfile="$3"
    local rc=0

    xmllint --html --xpath "$xpath_expr" "$infile" > "$outfile" 2>/dev/null || rc=$?

    # 11 = leeres Nodeset (dokumentiert in der xmllint-Manpage)
    if [[ $rc -eq 11 ]]; then
        echo "WARNUNG: XPath '$xpath_expr' lieferte kein Ergebnis." >&2
        : > "$outfile"
        return 0
    fi

    if [[ $rc -ne 0 ]]; then
        echo "FEHLER: xmllint brach mit Exit-Code $rc ab fuer '$xpath_expr'." >&2
        return "$rc"
    fi

    return 0
}

echo "[2/4] Extrahiere Titel  ($XPATH_TITLE)" >&2
extract_xpath "$XPATH_TITLE" "$RAW_HTML" "$FRAG_TITLE"

echo "[3/4] Extrahiere Hauptteil ($XPATH_MAIN)" >&2
extract_xpath "$XPATH_MAIN" "$RAW_HTML" "$FRAG_MAIN"

# ---------------------------------------------------------------------------
# 5. Zusammenf.hren und nach Markdown wandeln
#    Beide Fragmente werden an html2markdown auf stdin uebergeben,
#    dazwischen eine Leerzeile als Blocktrennung.
# ---------------------------------------------------------------------------
echo "[4/4] Konvertiere nach Markdown -> $OUTFILE" >&2

{
    cat "$FRAG_TITLE"
    printf '\n\n'
    cat "$FRAG_MAIN"
} | html2markdown --body-width=0 > "$OUTFILE"

# ---------------------------------------------------------------------------
# 6. Ergebnis melden
# ---------------------------------------------------------------------------
if [[ ! -s "$OUTFILE" ]]; then
    echo "WARNUNG: Ausgabedatei ist leer. XPaths pruefen." >&2
    exit 66   # EX_NOINPUT
fi

BYTES=$(wc -c < "$OUTFILE")
LINES=$(wc -l < "$OUTFILE")
echo "OK: $OUTFILE ($BYTES Bytes, $LINES Zeilen)" >&2
