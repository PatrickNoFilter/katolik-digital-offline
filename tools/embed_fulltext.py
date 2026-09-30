#!/usr/bin/env python3
"""Embed full-text readings from renungan_2026.json into KL_FT inside index.html.

Idempotent + gap-only merge (never overwrites existing non-empty full-text fields).
Run after each `fill_fulltext.py` session, before rebuilding the APK.

Usage:
    python3 tools/embed_fulltext.py            # merge into ../index.html
    python3 tools/embed_fulltext.py --status   # report only, no write

Safety rules (learned 2026-08-22):
- ALL textual replacements on the HTML are done BEFORE computing splice offsets.
- The blob is located by anchors, spliced, then the WRITTEN file is re-parsed
  to verify structure before the tool reports success.
"""
import json
import os
import sys
import tempfile
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
RENUNGAN = os.path.join(ROOT, "renungan_2026.json")

FT_FIELDS = ("af", "dg", "b1", "mz", "ij", "rn")
FT_FIELDS_EXTRA = ("mz_refren",)  # Extra fields for psalm refrain

OLD_COMMENT_MARKER = "// FULL TEXT DATA"          # pre-fix comment (legacy)
NEW_COMMENT_MARKER = "// KALENDER LITURGI DATA"   # current comment


def js_safe_json(obj) -> str:
    """Compact JSON that is also safe inside an HTML <script> block."""
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    s = s.replace("</", "<\\/")          # prevent premature </script> close
    s = s.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return s


def load_blob(html: str):
    """Return (kl_dict, anchor_start, anchor_end) where html[anchor_start:anchor_end]
    is everything from the comment line above KL_FT up to (not incl.) 'function klRenderFt'."""
    b = html.find("function klRenderFt")
    assert b > 0, "anchor 'function klRenderFt' not found"
    m = html.rfind(NEW_COMMENT_MARKER, 0, b)
    if m < 0:
        # legacy layout: derive from declaration itself
        d = html.rfind("const KL_FT", 0, b)
        assert d > 0, "KL_FT not found before klRenderFt"
        return None, d, b
    return None, m, b


def main() -> None:
    status_only = "--status" in sys.argv

    with open(RENUNGAN, encoding="utf-8") as f:
        readings = json.load(f)
    with open(HTML, encoding="utf-8") as f:
        html = f.read()

    _, a, b = load_blob(html)

    # --- locate current blob JSON between anchors and parse it ---
    j0 = html.find('{"01-01"', a, b)
    assert j0 > a, "blob start '{\"01-01\"' not found between anchors"
    kl_ft, consumed = json.JSONDecoder().raw_decode(html[j0:])
    print(f"current KL_FT: {len(kl_ft)} days ({consumed} chars)")

    # --- gap-only merge ---
    merged = 0
    unmapped = []
    for iso, day in sorted(readings.items()):
        entry = kl_ft.get(iso[5:])            # "2026-08-22" -> "08-22"
        if entry is None:
            unmapped.append(iso)
            continue
        added = False
        for fld in FT_FIELDS + FT_FIELDS_EXTRA:
            val = (day.get(fld) or "").strip()
            if val and not entry.get(fld):    # never overwrite existing content
                entry[fld] = val
                added = True
        if added:
            merged += 1

    have_ft = sum(1 for v in kl_ft.values() if any(v.get(f) for f in FT_FIELDS))
    print(f"renungan days: {len(readings)} | newly merged: {merged} | with full text now: {have_ft}/365")
    if unmapped:
        print(f"WARNING dates without KL_FT slot: {unmapped[:5]}{'...' if len(unmapped) > 5 else ''}")

    if status_only:
        return
    if merged == 0:
        print("Nothing to embed (already up to date).")
        return

    # --- build replacement REGION first; only then splice (no offset drift possible) ---
    comment = (
        '// KALENDER LITURGI DATA \u2014 keys "MM-DD" (e.g. "08-22"); resolved from ISO key via slice(5)\n'
        "// Refs: warna/nama/bacaan1/bacaan2/mazmur/injil. Full text (when filled):\n"
        "//   af antifon pembuka | dg doa | b1 bacaan I | mz mazmur tanggapan | ij injil | rn renungan\n"
        f"// Merged from renungan_2026.json by tools/embed_fulltext.py ({have_ft}/365 days @ {date.today().isoformat()})"
    )
    region = comment + "\nconst KL_FT = " + js_safe_json(kl_ft) + ";\n"

    new_html = html[:a] + region + html[b:]

    # --- verify BEFORE writing ---
    assert new_html.count("const KL_FT") == 1, "marker count != 1 after splice"

    fd, tmp = tempfile.mkstemp(dir=ROOT, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(new_html)
    os.replace(tmp, HTML)

    # --- verify AFTER writing (re-parse from disk) ---
    with open(HTML, encoding="utf-8") as f:
        chk = f.read()
    _, a2, b2 = load_blob(chk)
    j = chk.find('{"01-01"', a2, b2)
    re_parsed, _ = json.JSONDecoder().raw_decode(chk[j:])
    n = sum(1 for v in re_parsed.values() if any(v.get(f) for f in FT_FIELDS))
    assert len(re_parsed) == 365 and n == have_ft, "post-write verification failed"
    print(f"Wrote {HTML} ({os.path.getsize(HTML)} bytes); post-write check OK: {len(re_parsed)} days, {n} with full text")


if __name__ == "__main__":
    main()
