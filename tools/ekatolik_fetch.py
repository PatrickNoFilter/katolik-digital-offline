#!/usr/bin/env python3
"""ekatolik_fetch.py — pull Kalendar Liturgi data straight from the eKatolik API.

Per kalendar.md §21: this REPLACES the old multi-source scraping chain
(penakatolik / berkatkatolik / renunganpagi / parokijetis / detik). The eKatolik
app's own backend serves, for every day of 2026:

  - calendar metadata: warna, peringatan (feast name), ket_minggu, refs
  - FULL TEXT readings: teks_bacaan_pertama / teks_mazmur / teks_bacaan_kedua /
    teks_pengantar_injil / teks_bacaan_injil (+ judul_* and bait_pengantar_injil)
  - breviary ("Doa Pagi/Siang/Sore/Malam") full text via app/ibadat_harian

Reverse-engineered from eKatolik v5.3.3 (assets/index.android.bundle, Hermes v96,
decompiled with hbc-decompiler):
  API base   https://xaluna.infinitlab.id/
  auth       axios interceptor adds client_version=29 & os=android to EVERY call
             (query string for GET, merged into JSON body for POST); device_id may be null.
  endpoints  POST app/kalender_liturgi_range {from,to,since_versi}   (≤ ~1 month width)
             POST app/check_kalender_liturgi_v2 {tanggal_kalit, versi_kalit}
             POST app/ibadat_harian {tanggal}  → [{kategori,judul,teks(html)}]

Merge policy unchanged: gap-only into renungan_2026.json; existing non-empty
sections are never overwritten; atomic write after every gained section.

Usage:
    python3 tools/ekatolik_fetch.py                # fill all missing/past days
    python3 tools/ekatolik_fetch.py --include-future
    python3 tools/ekatolik_fetch.py --date 2026-08-23
    python3 tools/ekatolik_fetch.py --status
"""
import json, re, sys, os, html as H, subprocess, tempfile, argparse
from datetime import date, timedelta

JSON_PATH = "/storage/emulated/0/katolik-digital-offline/renungan_2026.json"
API = "https://xaluna.infinitlab.id/"
AUTH = {"client_version": "29", "os": "android", "device_id": "null"}

# renungan_2026.json core sections; b2 only exists on Sundays/solemnities
SECS_ALL = ('af', 'dg', 'b1', 'b2', 'mz', 'ij', 'rn')
SECS_CORE = ('af', 'dg', 'b1', 'mz', 'ij', 'rn')
NEVER_EXPECTED = {('2026-04-03', 'af'), ('2027-03-26', 'af'), ('2028-04-14', 'af')}


def missing_secs(day, iso=None):
    return [k for k in SECS_CORE
            if not day.get(k) and (iso, k) not in NEVER_EXPECTED]


def http_post(path, payload, timeout=30):
    """POST JSON to the eKatolik API with interceptor-style auth params."""
    body = dict(payload)
    body.update({"client_version": 29, "os": "android", "device_id": None})
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-X", "POST",
           "-H", "Content-Type: application/json",
           "-d", json.dumps(body),
           f"{API}{path}?client_version=29&os=android"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout)
    except Exception:
        return None


def strip_html(content):
    t = re.sub(r'<br\s*/?>', '\n', content or "")
    t = re.sub(r'</(p|div|h\d|li|tr|blockquote)>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = H.unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    return "\n".join(l.strip() for l in t.split('\n') if l.strip())


# ---------- load/save/merge (same contract as fill_fulltext.py) ----------
def load_db():
    with open(JSON_PATH, encoding='utf-8') as f:
        return json.load(f)


def save_atomic(db):
    ddir = os.path.dirname(JSON_PATH)
    fd, tmp = tempfile.mkstemp(dir=ddir, suffix='.tmp')
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False)
    os.replace(tmp, JSON_PATH)


def merge(db, iso, incoming, src_label):
    cur = db.setdefault(iso, {})
    added = []
    for k, v in incoming.items():
        if k in SECS_ALL and v and not cur.get(k):   # never overwrite non-empty
            cur[k] = v
            added.append(k)
    if added:
        db[iso]['_src'] = src_label
    return added


# ---------- eKatolik sources ----------
def fetch_calendar_day(iso):
    """Full-text readings for one ISO date from check_kalender_liturgi_v2."""
    r = http_post("app/check_kalender_liturgi_v2",
                  {"tanggal_kalit": iso, "versi_kalit": -1})
    if not r or not r.get("data_kalit"):
        return None
    k = r["data_kalit"]
    secs = {}
    if k.get("judul_bacaan_pertama"):
        secs['b1'] = "\n".join(x for x in (
            k.get("judul_bacaan_pertama", ""),
            strip_html(k.get("teks_bacaan_pertama", ""))) if x)
    if k.get("teks_mazmur") or k.get("mazmur_teks_refren"):
        mz_parts = []
        if k.get("mazmur_tanggapan"):
            mz_parts.append(f"Mazmur Tanggapan: {k['mazmur_tanggapan']}")
        if k.get("teks_mazmur"):
            mz_parts.append(strip_html(k["teks_mazmur"]))
        secs['mz'] = "\n\n".join(mz_parts)
        # Store refrain separately for proper display
        if k.get("mazmur_teks_refren"):
            secs['mz_refren'] = strip_html(k['mazmur_teks_refren'])
    if k.get("judul_bacaan_kedua") and k.get("teks_bacaan_kedua"):
        secs['b2'] = "\n".join(x for x in (
            k["judul_bacaan_kedua"],
            strip_html(k["teks_bacaan_kedua"])) if x)
    if k.get("bait_pengantar_injil") or k.get("teks_pengantar_injil"):
        ij_head = []
        if k.get("bait_pengantar_injil"):
            ij_head.append(f"Bait Pengantar Injil: {k['bait_pengantar_injil']}")
        if k.get("teks_pengantar_injil"):
            ij_head.append(strip_html(k["teks_pengantar_injil"]))
        if ij_head:
            secs.setdefault('ij_pre', '')  # placeholder to keep dict honest
            del secs['ij_pre']
            secs['_ij_head'] = "\n".join(ij_head)
    if k.get("judul_bacaan_injil") or k.get("teks_bacaan_injil"):
        head = secs.pop('_ij_head', None)
        parts = []
        if k.get("judul_bacaan_injil"):
            parts.append(k["judul_bacaan_injil"])
        if head:
            parts.append(head)
        if k.get("teks_bacaan_injil"):
            parts.append(strip_html(k["teks_bacaan_injil"]))
        secs['ij'] = "\n\n".join(parts)
    secs.pop('_ij_head', None)
    return secs or None


def _plain(teks_html):
    t = re.sub(r'<br\s*/?>', '\n', teks_html or "")
    t = re.sub(r'</(p|div|h\d|li|tr|blockquote)>', '\n', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = H.unescape(t)
    return "\n".join(l.strip() for l in t.split('\n') if l.strip())


def _collect_from_office(txt):
    """Extract 'DOA PENUTUP' collect text from one office's plain text.
    Returns None when the section is a placeholder (some Sundays show
    'Silakan tap tombol (i) kanan bawah.' instead of the collect)."""
    m = re.search(r'(?is)DOA PENUTUP\s*\n(.+?)(?=^PENUTUP\b)', txt, re.M)
    if not m:
        m = re.search(r'(?is)DOA PENUTUP\s*\n(.+)', txt)
    body = (m.group(1) if m else "").strip()
    if len(body) > 60 and 'tap tombol' not in body.lower():
        return body
    return None


def fetch_ibadat(iso):
    """Breviary supplements from app/ibadat_harian:
       af <- 'Pembukaan: Ant.' invitatory antiphon of Doa Pagi
       dg <- the DOA PENUTUP collect; tries Pagi, then Sore, then Malam
             (Sunday Pagi/Sore often carry only a placeholder)."""
    r = http_post("app/ibadat_harian", {"tanggal": iso})
    if not r or not isinstance(r.get("data"), list):
        return None
    out = {}
    for e in r["data"]:
        if not e.get("teks"):
            continue
        txt = _plain(e["teks"])
        if 'af' not in out and e.get("judul") == "Doa Pagi":
            m = (re.search(r'(?im)^Pembukaan:\s*Ant\.?\s*(.+)$', txt)
                 or re.search(r'(?im)^Pembukaan\s+Ant\.?\s*:?\s*(.+)$', txt)
                 or re.search(r'(?im)^Ant\.?\s+Pembukaan[:.]?\s*(.+)$', txt))
            if m:
                out['af'] = "[Antifon Doa Pagi] " + m.group(1).strip()
        if 'dg' not in out:
            body = _collect_from_office(txt)
            if body:
                out['dg'] = f"[Kolekta {e.get('judul','')}]\n" + body
    return out or None


def fill_day(db, d, force=False):
    """Fetch + merge one day. Returns list of added section keys."""
    iso = d.isoformat()
    added_all = []
    cal = fetch_calendar_day(iso)
    if cal:
        got = merge(db, iso, cal, "eKatolik-API")
        added_all += got
    if missing_secs(db.get(iso, {}), iso):
        iba = fetch_ibadat(iso)
        if iba:
            added_all += merge(db, iso, iba, "eKatolik-API-ibadat")
    return sorted(set(added_all))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date')
    ap.add_argument('--missing-only', action='store_true')
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--include-future', action='store_true')
    args = ap.parse_args()

    today = date.today()
    db = load_db()

    if args.status:
        start, end, have = date(2026, 1, 1), date(2026, 12, 31), set(db)
        ok = partial = 0
        miss = []
        cur = start
        while cur <= end:
            iso = cur.isoformat()
            if iso in have:
                ok += 1
                if missing_secs(db[iso], iso):
                    partial += 1
            elif cur <= today:
                miss.append(iso)
            cur += timedelta(days=1)
        print(f"OK {ok}/365 | missing {len(miss)} | partial {partial}")
        return

    targets = [date.fromisoformat(args.date)] if args.date else None
    if not targets:
        end = date(2026, 12, 31) if args.include_future else min(date(2026, 12, 31), today)
        cur, targets = date(2026, 1, 1), []
        while cur <= end:
            iso = cur.isoformat()
            if iso not in db or missing_secs(db[iso], iso):
                targets.append(cur)
            cur += timedelta(days=1)

    print(f"Filling {len(targets)} day(s) via eKatolik API...")
    filled = failed = 0
    for i, d in enumerate(targets):
        iso = d.isoformat()
        try:
            added = fill_day(db, d)
        except Exception as e:
            print(f"  [{iso}] error: {e}")
            failed += 1
            continue
        if added:
            filled += 1
            save_atomic(db)
            print(f"  [{iso}] +{','.join(added)}")
        else:
            failed += 1
            print(f"  [{iso}] nothing new")
    print(f"\nDone. filled={filled} empty/failed={failed}")


if __name__ == "__main__":
    main()
