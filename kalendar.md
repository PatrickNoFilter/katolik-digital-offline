# Kalendar Liturgi 2026 — Data Extraction Plan

## §17. eKatolik Data Extraction — COMPLETE (superseded by §18)

**Source:** eKatolik v5.3.3 APK → `assets/index.android.bundle` + gcatholic.org/calendar/2026/ID-id
**Date:** 2026-08-15

### Data Extracted

- **365 entries** (full year) — feast name, liturgical color, week number, rank
- **Source 1:** gcatholic.org API → accurate Indonesian feast names + colors for each day
- **Source 2:** eKatolik JS bundle → Doa Pagi/Siang/Sore/Malam entry names
- Reading references (`bacaan1/mazmur/injil`) are lectionary placeholders — embedded as
  `const KL_FT = {...}` in `index.html` (365 keys, references only, no full text).

---

## §18. APPROACH CHANGE — Fill Full Text Day-by-Day from Internet (CURRENT)

> **Decision (2026-08-22):** Abandon batch extraction (eKatolik bundle/API is encrypted,
> auth-gated, and Cloudflare-blocked). Instead, fill the FULL TEXT of every day's readings
> **one day at a time**, searching the internet per date and merging results into
> `renungan_2026.json`. The tool is idempotent + resumable so it can be re-run any time.

### Current Coverage

| Bucket | Count | Dates | Status |
|--------|-------|-------|--------|
| Full text OK | **233** | Jan–Aug 22 (excl. gaps) | renunganpagi.id (231) + berkatkatolik (2026-01-31, 2026-04-26) |
| Missing TODAY+ | 1 | 2026-08-22 … (rolling) | appears as time passes; re-run tool |
| FUTURE | ~131 | 2026-08-23 → 2026-12-31 | NOT yet published anywhere; fill incrementally as sources publish |

**Fill log:**
- 2026-08-22 — built `tools/fill_fulltext.py`; filled `2026-01-31` (af,b1,mz,ij,rn) and
  `2026-04-26` (af,b1,b2,ij,rn) from berkatkatolik. Note: that Sunday post has NO mazmur
  text at all — gap-only merge lets a later source slot it in without overwriting.
  Parser lesson learned: Sunday posts use `BACAAN INJIL` / `Inilah Injil … menurut` headers
  and even typos (`Renungan hari in :`) — patterns now cover these.

### Source Chain (tried in order, per day)

1. **berkatkatolik.wordpress.com** — WordPress public REST API (not Cloudflare-blocked).
   Query: `https://public-api.wordpress.com/rest/v1.1/sites/berkatkatolik.wordpress.com/posts/?search=<D%20<Bulan>%20<YYYY>>`
   ⚠ Posts are published 1–2 days BEFORE the target date → match on TITLE, never on post date.
   Sections parse cleanly: Antifon Pembuka / Bacaan dari Kitab… / Mazmur Tanggapan /
   Bait Pengantar (Alleluya) / Injil Suci menurut… / Renungan hari ini.
   ⚠ Known gaps: some August days absent (e.g. 2026-08-22).
2. **renunganpagi.id** — best structure (af/dg/b1/mz/ij/rn), already gave us 231 days,
   BUT now behind a managed Cloudflare challenge (curl + plain fetch both fail).
   Keep in chain; retry occasionally — may pass without JS someday or via new egress.
3. **web_search fallback** — query `renungan harian katolik <tanggal lengkap> bacaan mazmur injil`
   → known good publishers: detik.com regional (jogja/sulsel daily renungan),
   flores.tribunnews.com, parokijetis.com (deterministic slug
   `renungan-harian-hari-ini-dan-bacaan-injil-DD-<bulan>-YYYY`, currently unreachable HTTP 000),
   katolikindonesia.org. Parse whatever article matches section headers.
4. **Last resort** — leave the day empty in `renungan_2026.json`; `index.html` still shows
   the KL_FT lectionary REFERENCES (bacaan1/mazmur/injil refs) so the UI degrades gracefully.

### Tool

**`tools/fill_fulltext.py`**

```
python3 tools/fill_fulltext.py                 # fill all missing/past days
python3 tools/fill_fulltext.py --date 2026-01-31
python3 tools/fill_fulltext.py --missing-only  # skip future dates (nothing published yet)
python3 tools/fill_fulltext.py --status        # coverage report only
```

- Schema (matches existing `renungan_2026.json`): `{af, dg, b1, mz, ij, rn}` full text strings
- Merge rule: never overwrite non-empty sections of an existing day; fill gaps only
- Atomic write (tmp + rename); safe to interrupt/re-run

### Embedding into the App

**`tools/embed_fulltext.py`** merges `renungan_2026.json` into the `KL_FT` blob inside
`index.html` (gap-only merge, idempotent, verifies the written file by re-parsing it).
Run it after every fill session:

```
python3 tools/embed_fulltext.py            # merge + verify
python3 tools/embed_fulltext.py --status   # coverage report only
```

State of the embed (2026-08-23): **365 keys, 236 days carry full text**, warna/nama/
bacaan refs intact; days without text fall back to reference-only display.
All past+today days are COMPLETE (`partial 0`) as of the 2026-08-23 session below.

### §19. Bugfix session 2026-08-22 — KL_FT was dead on arrival

Two defects made the full-text feature show "Teks lengkap belum tersedia" for every day:

1. **Key mismatch:** main calendar data `KL` is keyed by ISO dates (`2026-08-22`) and
   `klOpen(key)` passed that straight to `KL_FT[key]`, while `KL_FT` is keyed `"MM-DD"`.
   Every lookup missed. Fix in `klRenderFt`: `KL_FT[key] || KL_FT[key.slice(5)]`.
   (Also fixed the stale comment claiming ISO-date keys.)
2. **Data never merged:** the 233 collected days sat only in `renungan_2026.json`;
   `KL_FT` had zero `af/dg/b1/mz/ij/rn` fields. Merged via the new embed tool.

Improvements shipped in the same pass:
- `klRenderFt` now shows lectionary references (`ft.bacaan1/mazmur/injil`) as section
  hints for Bacaan I / Mazmur / Injil, HTML-escaped via `klEsc`.
- Embed output is `<script>`-safe: `</` escaped as `<\/`, U+2028/U+2029 escaped.
- Lesson (bit us once): when editing a large file by offsets, make ALL
  length-changing string replacements BEFORE computing splice positions, and always
  re-parse the written artifact as verification.

### §20. Backfill session 2026-08-23 — all past days complete (236/236)

Ran `fill_fulltext.py --partial` over 44 gap days: **33 completed** via penakatolik
(publishes ~6 days ahead — best source), the rest by hand. Final state:
**OK 236/365 | missing(fillable) 0 | partial 0** (future days fill as they publish).

Root cause of most stubborn `af` gaps: **berkatkatolik titles zero-pad the day**
("SELASA, 02 APRIL 2026") while the WP title-match regex used `(?<!\d)2\s+April`,
which rejects "02". Fixed by matching `0?2` and querying both padded/unpadded.
Also: penakatolik slugs can disagree with the post title ("…minggu-26-juli…" slug
holding the Minggu 2 Agustus post) — slug-date-only matching misses those.

New tools (all idempotent, gap-only merge into `renungan_2026.json`):
- `tools/add_url.py <iso> <url>` — parse any single page and merge its sections.
- `tools/wp_gap.py <iso>` — harder berkatkatolik WP-API query (padded+unpadded, n=20).
- `tools/rp_gap.py <iso>` — renunganpagi.id via Blogger site-search; slices content
  between `post-body`/`post-footer` markers (naive `<div>` matching breaks on
  Blogger's deeply nested markup; post URLs carry a `?m=1` suffix).

Tool changes in `fill_fulltext.py`:
- **renunganpagi.id restored to SOURCES** — reachable again via curl (Cloudflare
  relaxed as of this session); Blogger search + marker-slice parsing.
- `NEVER_EXPECTED` set: Good Friday has no entrance antiphon (liturgy opens in
  silence) → `missing_secs(day, iso)` no longer flags `af` on those dates
  (2026-04-03, 2027-03-26, 2028-04-14 seeded).
- Manually filled today: af for 01-20, 02-16, 04-02, 04-28, 05-12, 07-07, 08-18,
  08-22, 08-23 (renunganpagi); rn for 05-13…07-29 batch (penakatolik);
  rn for 08-02 (penakatolik mis-slugged post + doakatolik.id cross-check;
  note `doakatolik.id/liturgi/YYYY-MM-DD` is a clean deterministic source).

Embed state: `index.html` KL_FT = 365 keys, **236 days full text** (af 234,
dg 235, b1/mz/ij/rn 236), blob re-parsed OK. Rebuild APK to ship when convenient.

---

## §21. APPROACH CHANGE #2 — eKatolik API cracked; single-source pipeline (CURRENT, 2026-08-23)

> **Decision:** ALL scraping sources (penakatolik, berkatkatolik, renunganpagi,
> parokijetis, detik-search) are RETIRED. The eKatolik app's own backend was
> reverse-engineered from `eKatolik [5.3.3].zip` → `base.apk` →
> `assets/index.android.bundle` (Hermes v96 bytecode, decompiled with
> hbc-decompiler) and serves EVERYTHING for all 365 days of 2026 — including
> future days — in one clean JSON API.

### The API

```
Base:   https://xaluna.infinitlab.id/
Auth:   axios interceptor adds to EVERY call:
        client_version=29  os=android  device_id=null
        (query string on GET, merged into the JSON body on POST)
```

| Endpoint | Payload | Returns |
|---|---|---|
| `POST app/kalender_liturgi_range` | `{from, to, since_versi}` | `{range, server_versi, count, data:[…]}`; range ≤ ~1 month (`"range too wide"` on 400) |
| `POST app/check_kalender_liturgi_v2` | `{tanggal_kalit, versi_kalit}` | `{data_kalit:{…}}` single day |
| `POST app/ibadat_harian` | `{tanggal}` | `{tanggal, data:[{kategori,judul,teks(html)}]}` breviary offices |

`data_kalit` fields: warna, peringatan, ket_minggu, judul_minggu,
bacaan_pertama/mazmur_tanggapan/bacaan_kedua/bait_pengantar_injil/bacaan_injil (refs),
judul_* + teks_* (FULL TEXT), mazmur_refren/teks_refren, tahun_liturgi, versi.

### Mapping into renungan_2026.json (`tools/ekatolik_fetch.py`)

- b1 = judul_bacaan_pertama + teks_bacaan_pertama (plain-text stripped)
- mz = ref + refren + teks_mazmur; b2 = judul + teks (Sundays/solemnities)
- ij = judul_bacaan_injil + bait_pengantar_injil/teks_pengantar_injil + teks_bacaan_injil
- af = invitatory antiphon of Doa Pagi ("Pembukaan: Ant." — several label variants)
- dg = "DOA PENUTUP" collect of the office; Pagi → Sore → Malam fallback chain
       (Sunday mornings often carry only a "tap tombol (i)" placeholder)
- rn = NOT provided by the API (renungan meditation remains from earlier sources;
       gap-only merge means existing rn text is kept)

### Result (2026-08-23)

- renungan_2026.json: **365/365 days present**, af/dg/b1/mz/ij complete for all
  365 days (af & dg via breviary supplement where the missal lacks them);
  rn present for 236 pre-existing days.
- index.html KL_FT embed refreshed: **365/365 days carry full text**
  (post-write re-parse OK). Backup: `index.html.bak.ekatolik-20260823`.
- Old tools moved to `tools/retired_20260823/`.

### New Operating Rhythm (until Dec 31)

```
python3 tools/ekatolik_fetch.py          # refresh anything missing (idempotent)
python3 tools/embed_fulltext.py          # merge into index.html KL_FT
python3 tools/fill_check.py              # optional sanity report (if rebuilt)
```

The old daily scrape dance is gone; one API covers past AND future days.

### Next Steps

- [x] Decompile Hermes v96 bundle, recover API base + interceptor auth params
- [x] Build `tools/ekatolik_fetch.py`; retire scraper chain
- [x] Fill all 365 days (b1/mz/ij + af/dg supplements), embed into index.html
- [ ] Rebuild APK with the updated index.html when convenient

---

## §22. PURE eKatolik 2026 — extracted from eKatolikv14.realm (AUTHORITATIVE)

> **Decision (2026-08-27):** The mixed-up KatolikDigital data is superseded by the
> PURE eKatolik 2026 calendar, decrypted directly from `eKatolikv14.realm`
> (AES-256, 64-byte key in `realm_key.json`). This is the canonical source —
> no internet scrape, no gcatholic, no API inference. All 365 days, full reading
> texts (bacaan1 / mazmur / bacaan2 / injil) included.

Source files (in `/root/eling/ekatolik_src/`, also stored in this folder):
- `kalender_liturgi_ekatolik_2026.json` — 365 days, full fields (AUTHORITATIVE)
- `kalender_liturgi_ekatolik_2026_ringkasan.md` — compact table (appended below)
- `realm_key.json` — the decryption key
- `realm_read/read.js` — Realm opener (realm@20.2.0)
- `encript.md` — how the encryption was opened

Verification: 365 KalenderLiturgi 2026 rows in Realm; all `hapus=False`; table below
regenerated from the JSON (365 unique valid 2026 dates, zero dupes/phantom rows).

### Full 2026 calendar (pure eKatolik)

# Kalender Liturgi eKatolik — 2026 (murni, dari eKatolikv14.realm)

Total hari: 365

| Tanggal | Hari | Warna | Masa | Peringkat | Judul | Bacaan 1 | Mazmur | Bacaan 2 | Injil |
|---|---|---|---|---|---|---|---|---|---|
| 2026-01-01 | Kamis | Putih | Masa Natal | HR |  | Bil 6:22-27 | Mzm 67:2-3.5.6.8 | Gal 4:4-7 | Luk 2:16-21 |
| 2026-01-02 | Jumat | Putih | Masa Natal | PW | PW S. Basilius Agung dan S. Gregorius dari Nazianze, Uskup dan Pujangga Gereja | 1Yoh 2:22-28 | Mzm 98:1.2-3ab.3cd-4 |  | Yoh 1:19-28 |
| 2026-01-03 | Sabtu | Putih | Masa Natal | PF | PF Nama Yesus Yang Tersuci | 1Yoh 2:29-3:6 | Mzm 98:1.3cd-4.5-6 |  | Yoh 1:29-34 |
| 2026-01-04 | Minggu | Putih | Masa Natal | HR |  | Yes 60:1-6 | Mzm 72:1-2.7-8.10-11.12-13 | Ef 3:2-3a.5-6 | Mat 2:1-12 |
| 2026-01-05 | Senin | Putih | Masa Natal |  |  | 1Yoh 3:22-4:6 | Mzm 2:7-8.10-11 |  | Mat 4:12-17.23-25 |
| 2026-01-06 | Selasa | Putih | Masa Natal |  |  | 1Yoh 4:7-10 | Mzm 72:1-2.3-4b.7-8 |  | Mrk 6:34-44 |
| 2026-01-07 | Rabu | Putih | Masa Natal | PF | PF S. Raimundus dari Penyafort, Imam | 1Yoh 4:11-18 | Mzm 72:1-2.10-11.12-13 |  | Mrk 6:45-52 |
| 2026-01-08 | Kamis | Putih | Masa Natal |  |  | 1Yoh 4:19-5:4 | Mzm 72:1-2.14.15bc.17 |  | Luk 4:14-22a |
| 2026-01-09 | Jumat | Putih | Masa Natal |  |  | 1Yoh 5:5-13 | Mzm 147:12-13.14-15.19-20 |  | Luk 5:12-16 |
| 2026-01-10 | Sabtu | Putih | Masa Natal |  |  | 1Yoh 5:14-21 | Mzm 149:1-2.3-4.5.6a.9b |  | Yoh 3:22-30 |
| 2026-01-11 | Minggu | Putih | Masa Natal | Pesta |  | Yes 42:1-4.6-7 | Mzm 29:1a.2.3ac-4.3b.9b-10 | Kis 10:34-38 | Mat 3:13-17 |
| 2026-01-12 | Senin | Hijau | Pekan Biasa I |  |  | 1Sam 1:1-8 | Mzm 116:12-13.14.17.18-19 |  | Mrk 1:14-20 |
| 2026-01-13 | Selasa | Hijau | Pekan Biasa I | PF | PF S. Hilarius, UPG | 1Sam 1:9-20 | 1Sam 2:1.4-5.6-7.8abcd |  | Mrk 1:21b-28 |
| 2026-01-14 | Rabu | Hijau | Pekan Biasa I |  |  | 1Sam 3:1-10.19-20 | Mzm 40:2.5.7-8a.8b-9.10 |  | Mrk 1:29-39 |
| 2026-01-15 | Kamis | Hijau | Pekan Biasa I |  |  | 1Sam 4:1-11 | Mzm 44:10-11.14-15.24-25 |  | Mrk 1:40-45 |
| 2026-01-16 | Jumat | Hijau | Pekan Biasa I |  |  | 1Sam 8:4-7.10-22a | Mzm 89:16-17.18-19 |  | Mrk 2:1-12 |
| 2026-01-17 | Sabtu | Putih | Pekan Biasa I | PW | PW S. Antonius, Abas | 1Sam 9:1-4.17-19;10:1a | Mzm 21:2-3.4-5.6-7 |  | Mrk 2:13-17 |
| 2026-01-18 | Minggu | Hijau | Pekan Biasa II |  |  | Yes 49:3.5-6 | Mzm 40:2.4a.7-8a.8b-9.10 | 1Kor 1:1-3 | Yoh 1:29-34 |
| 2026-01-19 | Senin | Hijau | Pekan Biasa II |  |  | 1Sam 15:16-23 | Mzm 50:8-9.16bc-17.21.23 |  | Mrk 2:18-22 |
| 2026-01-20 | Selasa | Hijau | Pekan Biasa II | PF | PF S. Sebastianus, Martir PF S. Fabianus, Paus dan Martir | 1Sam 16:1-13 | Mzm 89:20.21-22.27-28 |  | Mrk 2:23-28 |
| 2026-01-21 | Rabu | Merah | Pekan Biasa II | PW | PW S. Agnes, Perawan dan Martir | 1Sam 17:32-33.37.40-51 | Mzm 144:1.2.9-10 |  | Mrk 3:1-6 |
| 2026-01-22 | Kamis | Hijau | Pekan Biasa II | PF | PF S. Vinsensius, Diakon dan Martir | 1Sam 18:6-9;19:1-7 | Mzm 56:2-3.9-10a.10b-11.12-13 |  | Mrk 3:7-12 |
| 2026-01-23 | Jumat | Hijau | Pekan Biasa II |  |  | 1Sam 24:3-21 | Mzm 57:2.3-4.6.11 |  | Mrk 3:13-19 |
| 2026-01-24 | Sabtu | Putih | Pekan Biasa II | PW | PW S. Fransiskus dari Sales, Uskup dan Pujangga Gereja | 2Sam 1:1-4.11-12.19.23-27 | Mzm 80:2-3.5-7 |  | Mrk 3:20-21 |
| 2026-01-25 | Minggu | Hijau | Pekan Biasa III |  |  | Yes 8:23b-9:3 | Mzm 27:1.4.13-14 | 1Kor 1:10-13.17 | Mat 4:12-23 |
| 2026-01-26 | Senin | Putih | Pekan Biasa III | PW | PW S. Timotius dan Titus, Uskup | 2Tim 1:1-8 | Mzm 96:1-2a.2b-3.7-8a.10 |  | Luk 10:1-9 |
| 2026-01-27 | Selasa | Hijau | Pekan Biasa III | PF | PF S. Angela Merici, Perawan | 2Sam 6:12b-15.17-19 | Mzm 24:7.8.9.10 |  | Mrk 3:31-35 |
| 2026-01-28 | Rabu | Putih | Pekan Biasa III | PW | PW S. Tomas dari Aquino, Imam dan Pujangga Gereja | 2Sam 7:4-17 | Mzm 89:4-5.27-28.29-30 |  | Mrk 4:1-20 |
| 2026-01-29 | Kamis | Hijau | Pekan Biasa III |  |  | 2Sam 7:18-19.24-29 | Mzm 132:1-2.3-5.11.12.13-14 |  | Mrk 4:21-25 |
| 2026-01-30 | Jumat | Hijau | Pekan Biasa III |  |  | 2Sam 11:1-4a.5-10a.13-17 | Mzm 51:3-4.5-6a.6bc-7.10-11 |  | Mrk 4:26-34 |
| 2026-01-31 | Sabtu | Putih | Pekan Biasa III | PW | PW S. Yohanes Bosko, Imam | 2Sam 12:1-7a.10-17 | Mzm 51:12-13.14-15.16-17 |  | Mrk 4:35-41 |
| 2026-02-01 | Minggu | Hijau | Pekan Biasa IV |  |  | Zef 2:3;3:12-13 | Mzm 146:1.7.8-9a.9b-10 | 1Kor 1:26-31 | Mat 5:1-12a |
| 2026-02-02 | Senin | Putih | Pekan Biasa IV | Pesta |  | Mal 3:1-4 | Mzm 24:7.8.9.10 | Ibr 2:14-18 | Luk 2:22-40 |
| 2026-02-03 | Selasa | Hijau | Pekan Biasa IV | PF | PF S. Ansgarius, Uskup PF S. Blasius, Uskup dan Martir | 2Sam 18:9-10.14b.24-25a.30-19:3 | Mzm 86:1-2.3-4.5-6 |  | Mrk 5:21-43 |
| 2026-02-04 | Rabu | Hijau | Pekan Biasa IV |  |  | 2Sam 24:2.9-17 | Mzm 32:1-2.5.6.7 |  | Mrk 6:1-6 |
| 2026-02-05 | Kamis | Merah | Pekan Biasa IV | PW | PW S. Agata, Perawan dan Martir | 1Raj 2:1-4.10-12 | 1Taw 29:10.11ab.11d-12a.12bcd |  | Mrk 6:7-13 |
| 2026-02-06 | Jumat | Merah | Pekan Biasa IV | PW | PW S. Paulus Miki dan teman-temannya, Martir | Sir 47:2-11 | Mzm 18:31.47.50.51 |  | Mrk 6:14-29 |
| 2026-02-07 | Sabtu | Hijau | Pekan Biasa IV |  |  | 1Raj 3:4-13 | Mzm 119:9.10.11.12.13.14 |  | Mrk 6:30-34 |
| 2026-02-08 | Minggu | Hijau | Pekan Biasa V |  |  | Yes 58:7-10 | Mzm 112:4-5.6-7.8a.9 | 1Kor 2:1-5 | Mat 5:13-16 |
| 2026-02-09 | Senin | Hijau | Pekan Biasa V |  |  | 1Raj 8:1-7.9-13 | Mzm 132:6-7.8-10 |  | Mrk 6:53-56 |
| 2026-02-10 | Selasa | Putih | Pekan Biasa V | PW | PW S. Skolastika, Perawan | 1Raj 8:22-23.27-30 | Mzm 84:3.4.5.10.11 |  | Mrk 7:1-13 |
| 2026-02-11 | Rabu | Hijau | Pekan Biasa V | PF | PF S.P. Maria dari Lourdes | 1Raj 10:1-10 | Mzm 37:5-6.30-31.39-40 |  | Mrk 7:14-23 |
| 2026-02-12 | Kamis | Hijau | Pekan Biasa V |  |  | 1Raj 11:4-13 | Mzm 106:3-4.35-36.37.40 |  | Mrk 7:24-30 |
| 2026-02-13 | Jumat | Hijau | Pekan Biasa V |  |  | 1Raj 11:29-32;12:19 | Mzm 81:10-11ab.12-13.14-15 |  | Mrk 7:31-37 |
| 2026-02-14 | Sabtu | Putih | Pekan Biasa V | PW | PW S. Sirilus, Rahib, dan Metodius, Uskup | 1Raj 12:26-32;13:33-34 | Mzm 106:6-7a.19-20.21-22 |  | Mrk 8:1-10 |
| 2026-02-15 | Minggu | Hijau | Pekan Biasa VI |  |  | Sir 15:15-20 | Mzm 119:1-2.4-5.17-18.33-34 | 1Kor 2:6-10 | Mat 5:17-37 |
| 2026-02-16 | Senin | Hijau | Pekan Biasa VI |  |  | Yak 1:1-11 | Mzm 119:67.68.71.72.75.76 |  | Mrk 8:11-13 |
| 2026-02-17 | Selasa | Hijau | Pekan Biasa VI | PF | PF Tujuh Saudara Suci Pendiri Tarekat Hamba-Hamba SP Maria | Yak 1:12-18 | Mzm 94:12-13a.14-15.18-19 |  | Mrk 8:14-21 |
| 2026-02-18 | Rabu | Ungu | Rabu Abu | HR |  | Yl 2:12-18 | Mzm 51:3-4.5-6a.12-13.14.17 | 2Kor 5:20-6:2 | Mat 6:1-6.16-18 |
| 2026-02-19 | Kamis | Ungu | Rabu Abu |  |  | UL 30:15-20 | Mzm 1:1-2.3.4.6 |  | Luk 9:22-25 |
| 2026-02-20 | Jumat | Ungu | Rabu Abu |  |  | Yes 58:1-9a | Mzm 51:3-4.5-6a.18-19 |  | Mat 9:14-15 |
| 2026-02-21 | Sabtu | Ungu | Rabu Abu | PF | PF S. Petrus Damianus, Uskup dan Pujangga Gereja | Yes 58:9b-14 | Mzm 86:1-2.3-4.5-6 |  | Luk 5:27-32 |
| 2026-02-22 | Minggu | Ungu | Prapaskah I |  |  | Kej 2:7-9;3:1-7 | Mzm 51:3-4.5-6a.12-13.14.17 | Rom 5:12-19 | Mat 4:1-11 |
| 2026-02-23 | Senin | Ungu | Prapaskah I | PF | PF S. Polikarpus, Uskup dan Martir | Im 19:1-2.11-18 | Mzm 19:8.9.10.15 |  | Mat 25:31-46 |
| 2026-02-24 | Selasa | Ungu | Prapaskah I |  |  | Yes 55:10-11 | Mzm 34:4-5.6-7.16-17.18-19 |  | Mat 6:7-15 |
| 2026-02-25 | Rabu | Ungu | Prapaskah I |  |  | Yun 3:1-10 | Mzm 51:3-4.12-13.18-19 |  | Luk 11:29-32 |
| 2026-02-26 | Kamis | Ungu | Prapaskah I |  |  | T.Est 4:10a.10c-12.17-19 | Mzm 138:1-2a.2bc-3.7c-8 |  | Mat 7:7-12 |
| 2026-02-27 | Jumat | Ungu | Prapaskah I |  |  | Yeh 18:21-28 | Mzm 130:1-2.3-4ab.4c-6.7-8 |  | Mat 5:20-26 |
| 2026-02-28 | Sabtu | Ungu | Prapaskah I |  |  | Ul 26:16-19 | Mzm 119:1-2.4-5.7-8 |  | Mat 5:43-48 |
| 2026-03-01 | Minggu | Ungu | Prapaskah II |  |  | Kej 12:1-4a | Mzm 33:4-5.18-19.20.22 | 2Tim 1:8b-10 | Mat 17:1-9 |
| 2026-03-02 | Senin | Ungu | Prapaskah II |  |  | Dan 9:4b-10 | Mzm 79:8.9.11.13 |  | Luk 6:36-38 |
| 2026-03-03 | Selasa | Ungu | Prapaskah II |  |  | Yes 1:10.16-20 | Mzm 50:8-9.16bc-17.21.23 |  | Mat 23:1-12 |
| 2026-03-04 | Rabu | Ungu | Prapaskah II | PF | PF S. Kasimirus | Yer 18:18-20 | Mzm 31:5-6.14.15-16 |  | Mat 20:17-28 |
| 2026-03-05 | Kamis | Ungu | Prapaskah II |  |  | Yer 17:5-10 | Mzm 1:1-2.3.4.6 |  | Luk 16:19-31 |
| 2026-03-06 | Jumat | Ungu | Prapaskah II |  |  | Kej 37:3-4.12-13a.17b-28 | Mzm 105:16-17.18-19.20-21 |  | Mat 21:33-43.45-46 |
| 2026-03-07 | Sabtu | Ungu | Prapaskah II | PF | PF S. Perpetua dan Felisitas, Martir | Mi 7:14-15.18-20 | Mzm 103:1-2.3-4.9-10.11-12 |  | Luk 15:1-3.11-32 |
| 2026-03-08 | Minggu | Ungu | Prapaskah III |  |  | Kel 17:3-7 | Mzm 95:1-2.6-7.8-9 | Rom 5:1-2.5-8 | Yoh 4:5-42 |
| 2026-03-09 | Senin | Ungu | Prapaskah III | PF | PF S. Fransiska dari Roma, Biarawati | 2Raj 5:1-15a | Mzm 42:2.3;43:3.4 |  | Luk 4:24-30 |
| 2026-03-10 | Selasa | Ungu | Prapaskah III |  |  | T.Dan 3:25.34-43 | Mzm 25:4b-5b.6.7c.8-9 |  | Mat 18:21-35 |
| 2026-03-11 | Rabu | Ungu | Prapaskah III |  |  | Ul 4:1.5-9 | Mzm 147:12-13.15-16.19-20 |  | Mat 5:17-19 |
| 2026-03-12 | Kamis | Ungu | Prapaskah III |  |  | Yer 7:23-28 | Mzm 95:1-2.6-7.8-9 |  | Luk 11:14-23 |
| 2026-03-13 | Jumat | Ungu | Prapaskah III |  |  | Hos 14:2-10 | Mzm 81:6c-8a.8bc-9.10-11ab.14.17 |  | Mrk 12:28b-34 |
| 2026-03-14 | Sabtu | Ungu | Prapaskah III |  |  | Hos 6:1-6 | Mzm 51:3-4.18-19.20-21ab |  | Luk 18:9-14 |
| 2026-03-15 | Minggu | Ungu | Prapaskah IV |  |  | 1Sam 16:1b.6-7.10-13a | Mzm 23:1-3a.3b-4.5.6 | Ef 5:8-14 | Yoh 9:1-41 |
| 2026-03-16 | Senin | Ungu | Prapaskah IV |  |  | Yes 65:17-21 | Mzm 30:2.4.5-6.11-12a.13b |  | Yoh 4:43-54 |
| 2026-03-17 | Selasa | Ungu | Prapaskah IV | PF | PF S. Patrisius, Uskup | Yeh 47:1-9.12 | Mzm 46:2-3.5-6.8-9 |  | Yoh 5:1-3a.5-16 |
| 2026-03-18 | Rabu | Ungu | Prapaskah IV | PF | PF S. Sirilus dari Yerusalem, Uskup dan Pujangga Gereja | Yes 49:8-15 | Mzm 145:8-9.13cd-14.17-18 |  | Yoh 5:17-30 |
| 2026-03-19 | Kamis | Putih | Prapaskah IV | HR |  | 2Sam 7:4-5a.12-14a.16 | Mzm 89:2-3.4-5.27.29 | Rom 4:13.16-18.22 | Mat 1:16.18-21.24a |
| 2026-03-20 | Jumat | Ungu | Prapaskah IV |  |  | Keb 2:1a.12-22 | Mzm 34:17-18.19-20.21.23 |  | Yoh 7:1-2.10.25-30 |
| 2026-03-21 | Sabtu | Ungu | Prapaskah IV |  |  | Yer 11:18-20 | Mzm 7:2-3.9bc-10.11-12 |  | Yoh 7:40-53 |
| 2026-03-22 | Minggu | Ungu | Prapaskah V |  |  | Yeh 37:12-14 | Mzm 130:1-2.3-4b.4c-6.7-8 | Rom 8:8-11 | Yoh 11:1-45 |
| 2026-03-23 | Senin | Ungu | Prapaskah V | PF | PF S. Turibius dari Mongrovejo, Uskup | T.Dan 13:1-9.15-17.19-30.33-62 | Mzm 23:1-3a.3b-4.5.6 |  | Yoh 8:1-11 |
| 2026-03-24 | Selasa | Ungu | Prapaskah V |  |  | Bil 21:4-9 | Mzm 102:2-3.16-18.19-20 |  | Yoh 8:21-30 |
| 2026-03-25 | Rabu | Putih | Prapaskah V | HR |  | Yes 7:10-14;8:10 | Mzm 40:7-8a.8b-9.10.11 | Ibr 10:4-10 | Luk 1:26-38 |
| 2026-03-26 | Kamis | Ungu | Prapaskah V |  |  | Kej 17:3-9 | Mzm 105:4-5.6-7.8-9 |  | Yoh 8:51-59 |
| 2026-03-27 | Jumat | Ungu | Prapaskah V |  |  | Yer 20:10-13 | Mzm 18:2-3a.3bc-4.5-6.7 |  | Yoh 10:31-42 |
| 2026-03-28 | Sabtu | Ungu | Prapaskah V |  |  | Yeh 37:21-28 | Yer 31:10.11-12ab.13 |  | Yoh 11:45-56 |
| 2026-03-29 | Minggu | Merah | Pekan Suci | HR |  | Yes 50:4-7 | Mzm 22:8-9.17-18a.19-20.23-24 | Flp 2:6-11 | Mat 26:14-27:66 |
| 2026-03-30 | Senin | Ungu | Pekan Suci |  |  | Yes 42:1-7 | Mzm 27:1.2.3.13-14 |  | Yoh 12:1-11 |
| 2026-03-31 | Selasa | Ungu | Pekan Suci |  |  | Yes 49:1-6 | Mzm 71:1-2.3-4a.5-6ab.15.17 |  | Yoh 13:21-33.36-38 |
| 2026-04-01 | Rabu | Ungu | Pekan Suci |  |  | Yes 50:4-9a | Mzm 69:8-10.21bcd-22.31.33-34 |  | Mat 26:14-25 |
| 2026-04-02 | Kamis | Putih | Pekan Suci | HR |  | Kel 12:1-8.11-14 | Mzm 116:12-13.15-16bc.17-18 | 1Kor 11:23-26 | Yoh 13:1-15 |
| 2026-04-03 | Jumat | Merah | Pekan Suci | HR |  | Yes 52:13-53:12 | Mzm 31:2.6.12-13.15-16.17.25 | Ibr 4:14-16;5:7-9 | Yoh 18:1-19:42 |
| 2026-04-04 | Sabtu | Putih | Pekan Suci | HR |  | Kej 1:1-2:2 | Mzm 104:1-2a.5-6.10.12.13-14.24.35c | Kej 22:1-18 | Mat 28:1-10 |
| 2026-04-05 | Minggu | Putih | Oktaf Paskah | HR |  | Kis 10:34a.37-43 | Mzm 118:1-2.16ab-17.22-23 | Kol 3:1-4 | Yoh 20:1-9 |
| 2026-04-06 | Senin | Putih | Oktaf Paskah |  |  | Kis 2:14.22-32 | Mzm 16:1-2a.5.7-8.9-10.11 |  | Mat 28:8-15 |
| 2026-04-07 | Selasa | Putih | Oktaf Paskah |  | (Ditiadakan) PW S. Yohanes Baptista de la Salle, Imam | Kis 2:36-41 | Mzm 33:4-5.18-19.20.22 |  | Yoh 20:11-18 |
| 2026-04-08 | Rabu | Putih | Oktaf Paskah |  |  | Kis 3:1-10 | Mzm 105:1-2.3-4.6-7.8-9 |  | Luk 24:13-35 |
| 2026-04-09 | Kamis | Putih | Oktaf Paskah |  |  | Kis 3:11-26 | Mzm 8:2a.5.6-7.8-9 |  | Luk 24:35-48 |
| 2026-04-10 | Jumat | Putih | Oktaf Paskah |  |  | Kis 4:1-12 | Mzm 118:1-2.4.22-24.25-27a |  | Yoh 21:1-14 |
| 2026-04-11 | Sabtu | Putih | Oktaf Paskah |  | (Ditiadakan) PW S. Stanislaus, Uskup dan Martir | Kis 4:13-21 | Mzm 118:1.14-15a.16a.18.19-21 |  | Mrk 16:9-15 |
| 2026-04-12 | Minggu | Putih | Paskah II |  |  | Kis 2:42-47 | Mzm 118:2-4.13-15.22-24 | 1Ptr 1:3-9 | Yoh 20:19-31 |
| 2026-04-13 | Senin | Putih | Paskah II | PF | PF S. Martinus I, Paus dan Martir | Kis 4:23-31 | Mzm 2:1-3.4-6.7-9 |  | Yoh 3:1-8 |
| 2026-04-14 | Selasa | Putih | Paskah II |  |  | Kis 4:32-37 | Mzm 93:1ab.1c-2.5 |  | Yoh 3:7-15 |
| 2026-04-15 | Rabu | Putih | Paskah II |  |  | Kis 5:17-26 | Mzm 34:2-3.4-5.6-7.8-9 |  | Yoh 3:16-21 |
| 2026-04-16 | Kamis | Putih | Paskah II |  |  | Kis 5:27-33 | Mzm 34:2.9.17-18.19-20 |  | Yoh 3:31-36 |
| 2026-04-17 | Jumat | Putih | Paskah II |  |  | Kis 5:34-42 | Mzm 27:1.4.13-14 |  | Yoh 6:1-15 |
| 2026-04-18 | Sabtu | Putih | Paskah II |  |  | Kis 6:1-7 | Mzm 33:1-2.4-5.18-19 |  | Yoh 6:16-21 |
| 2026-04-19 | Minggu | Putih | Paskah III |  |  | Kis 2:14.22-33 | Mzm 16:1-2a.5.7-8.9-10.11 | 1Ptr 1:17-21 | Luk 24:13-35 |
| 2026-04-20 | Senin | Putih | Paskah III |  |  | Kis 6:8-15 | Mzm 119:23-24.26-27.29-30 |  | Yoh 6:22-29 |
| 2026-04-21 | Selasa | Putih | Paskah III | PF | PF S. Anselmus, Uskup dan Pujangga Gereja | Kis 7:51-8:1a | Mzm 31:3cd-4.6ab.7b.8a.17.21ab |  | Yoh 6:30-35 |
| 2026-04-22 | Rabu | Putih | Paskah III |  |  | Kis 8:1b-8 | Mzm 66:1-3a.4-5.6-7a |  | Yoh 6:35-40 |
| 2026-04-23 | Kamis | Putih | Paskah III | PF | PF S. Georgius, Martir | Kis 8:26-40 | Mzm 66:8-9.16-17.20 |  | Yoh 6:44-51 |
| 2026-04-24 | Jumat | Putih | Paskah III | PF | PF S. Fidelis dari Sigmaringen, Imam dan Martir | Kis 9:1-20 | Mzm 117:1.2 |  | Yoh 6:52-59 |
| 2026-04-25 | Sabtu | Merah | Paskah III | Pesta |  | 1Ptr 5:5b-14 | Mzm 89:2-3.6-7.16-17 |  | Mrk 16:15-20 |
| 2026-04-26 | Minggu | Putih | Paskah IV |  |  | Kis 2:14a.36-41 | Mzm 23:1-3a.3b-4.5.6 | 1Ptr 2:20b-25 | Yoh 10:1-10 |
| 2026-04-27 | Senin | Putih | Paskah IV |  |  | Kis 11:1-18 | Mzm 42:2-3;43:3.4 |  | Yoh 10:11-18 |
| 2026-04-28 | Selasa | Putih | Paskah IV | PF | PF S. Ludovikus Maria Grignion de Montfort, Imam PF S. Petrus Chanel, Imam dan Martir | Kis 11: 19-26 | Mzm 87:1-3.4-5.6-7 |  | Yoh 10:22-30 |
| 2026-04-29 | Rabu | Putih | Paskah IV | PW | PW S. Katarina dari Siena, Perawan dan Pujangga Gereja | Kis 12:24-13:5a | Mzm 67:2-3.5.6.8 |  | Yoh 12:44-50 |
| 2026-04-30 | Kamis | Putih | Paskah IV | PF | PF S. Pius V, Paus | Kis 13:13-25 | Mzm 89:2-3.21-22.25.27 |  | Yoh 13:16-20 |
| 2026-05-01 | Jumat | Putih | Paskah IV | PF | PF S. Yusuf, Pekerja | Kis 13:26-33 | Mzm 2:6-7.8-9.10-11 |  | Yoh 14:1-6 |
| 2026-05-02 | Sabtu | Putih | Paskah IV | PW | PW S. Atanasius, Uskup dan Pujangga Gereja | Kis 13:44-52 | Mzm 98:1.2-3ab.3cd-4 |  | Yoh 14:7-14 |
| 2026-05-03 | Minggu | Putih | Paskah V |  |  | Kis 6:1-7 | Mzm 33:1-2.4-5.18-19 | 1Ptr 2:4-9 | Yoh 14:1-12 |
| 2026-05-04 | Senin | Putih | Paskah V |  |  | Kis 14:5-18 | Mzm 115:1-2.3-4.15-16 |  | Yoh 14:21-26 |
| 2026-05-05 | Selasa | Putih | Paskah V |  |  | Kis 14:19-28 | Mzm 145:10-11.12-13ab.21 |  | Yoh 14:27-31a |
| 2026-05-06 | Rabu | Putih | Paskah V |  |  | Kis 15:1-6 | Mzm 122:1-2.3-4a.4b-5 |  | Yoh 15:1-8 |
| 2026-05-07 | Kamis | Putih | Paskah V |  |  | Kis 15:7-21 | Mzm 96:1-2a.2b-3.10 |  | Yoh 15:9-11 |
| 2026-05-08 | Jumat | Putih | Paskah V |  |  | Kis 15:22-31 | Mzm 57:8-9.10-12 |  | Yoh 15:12-17 |
| 2026-05-09 | Sabtu | Putih | Paskah V |  |  | Kis 16:1-10 | Mzm 100:1-2.3.5 |  | Yoh 15:18-21 |
| 2026-05-10 | Minggu | Putih | Paskah VI |  |  | Kis 8:5-8.14-17 | Mzm 66:1-3a.4-5.6-7a.16.20 | 1Ptr 3:15-18 | Yoh 14:15-21 |
| 2026-05-11 | Senin | Putih | Paskah VI |  |  | Kis 16:11-15 | Mzm 149:1-2.3-4.5-6a.9b |  | Yoh 15:26-16:4a |
| 2026-05-12 | Selasa | Putih | Paskah VI | PF | PF S. Pankrasius, Martir PF S. Nereus dan Akhiles, Martir | Kis 16:22-34 | Mzm 138:1-2a.2bc-3.7c-8 |  | Yoh 16:5-11 |
| 2026-05-13 | Rabu | Putih | Paskah VI | PF | PF SP Maria dari Fatima | Kis 17:15.22-18:1 | Mzm 148:1-2.11-12ab.12c-14a.14bcd |  | Yoh 16:12-15 |
| 2026-05-14 | Kamis | Putih | Paskah VI | HR |  | Kis 1:1-11 | Mzm 47:2-3.6-7.8-9 | Ef 1:17-23 | Mat 28:16-20 |
| 2026-05-15 | Jumat | Putih | Paskah VI |  |  | Kis 18:9-18 | Mzm 47:2-3.4-5.6-7 |  | Yoh 16:20-23a |
| 2026-05-16 | Sabtu | Putih | Paskah VI |  |  | Kis 18:23-28 | Mzm 47:2-3.8-9.10 |  | Yoh 16:23b-28 |
| 2026-05-17 | Minggu | Putih | Paskah VII |  |  | Kis 1:12-14 | Mzm 27:1.4.7-8a | 1Ptr 4:13-16 | Yoh 17:1-11a |
| 2026-05-18 | Senin | Putih | Paskah VII | PF | PF S. Yohanes I, Paus dan Martir | Kis 19:1-8 | Mzm 68:2-3.4-5ac.6-7b |  | Yoh 16:29-33 |
| 2026-05-19 | Selasa | Putih | Paskah VII |  |  | Kis 20:17-27 | Mzm 68:10-11.20-21 |  | Yoh 17:1-11a |
| 2026-05-20 | Rabu | Putih | Paskah VII | PF | PF S. Bernardinus dari Siena, Imam | Kis 20:28-38 | Mzm 68:29-30.33-35a.35b-36c |  | Yoh 17:11b-19 |
| 2026-05-21 | Kamis | Putih | Paskah VII |  |  | Kis 22:30;23:6-11 | Mzm 16:1-2a.5.7-8.9-10.11 |  | Yoh 17:20-26 |
| 2026-05-22 | Jumat | Putih | Paskah VII | PF | PF S. Rita dari Cascia | Kis 25:13-21 | Mzm 103:1-2.11-12.19-20ab |  | Yoh 21:15-19 |
| 2026-05-23 | Sabtu | Putih | Paskah VII |  |  | Kis 28:16-20.30-31 | Mzm 11:4.5.7 |  | Yoh 21:20-25 |
| 2026-05-24 | Minggu | Merah | Pentakosta | HR |  | Kis 2:1-11 | Mzm 104:1ab.24ac.29c-30.31.34 | 1Kor 12:3b-7.12-13 | Yoh 20:19-23 |
| 2026-05-25 | Senin | Putih | Hari Biasa | PF | PF S. Maria Magdalena de Pazzi, Perawan PF S. Gregorius VII, Paus PF S. Beda, Imam dan Pujangga Gereja | Kej 3:9-15.20 | Mzm 87:1-2.3.5.6-7 |  | Yoh 19:25-34 |
| 2026-05-26 | Selasa | Putih | Pekan Biasa VIII | PW | PW S. Filipus Neri, Imam | 1Ptr 1:10-16 | Mzm 98:1.2-3ab.3c-4 |  | Mrk 10:28-31 |
| 2026-05-27 | Rabu | Hijau | Pekan Biasa VIII | PF | PF S. Agustinus dari Canterbury, Uskup | 1Ptr 1:18-25 | Mzm 147:12-13.14-15.19-20 |  | Mrk 10:32-45 |
| 2026-05-28 | Kamis | Hijau | Pekan Biasa VIII |  |  | 1Ptr 2:2-5.9-12 | Mzm 100:2.3.4.5 |  | Mrk 10:46-52 |
| 2026-05-29 | Jumat | Hijau | Pekan Biasa VIII | PF | PF S. Paulus VI, Paus | 1Ptr 4:7-13 | Mzm 96:10.11-12.13 |  | Mrk 11:11-26 |
| 2026-05-30 | Sabtu | Hijau | Pekan Biasa VIII |  |  | Yud 17:20b-25 | Mzm 63:2.3-4.5-6 |  | Mrk 11:27-33 |
| 2026-05-31 | Minggu | Putih | Hari Raya | HR |  | Kel 34:4b-6.8-9 | T.Dan 3:52.53.54.55.56 | 2Kor 13:11-13 | Yoh 3:16-18 |
| 2026-06-01 | Senin | Merah | Pekan Biasa IX | PW | PW S. Yustinus, Martir | 2Ptr 1:1-7 | Mzm 91:1-2.14-15ab.15c-16 |  | Mrk 12:1-12 |
| 2026-06-02 | Selasa | Hijau | Pekan Biasa IX | PF | PF S. Marselinus dan Petrus, Martir | 2Ptr 3:12-15a.17-18 | Mzm 90:2.3-4.10.14.16 |  | Mrk 12:13-17 |
| 2026-06-03 | Rabu | Merah | Pekan Biasa IX | PW | PW S. Karolus Lwanga dan teman-temannya, Martir | 2Tim 1:1-3.6-12 | Mzm 123:1-2a.2bcd |  | Mrk 12:18-27 |
| 2026-06-04 | Kamis | Hijau | Pekan Biasa IX |  |  | 2Tim 2:8-15 | Mzm 25:4bc-5ab.8-9.10.14 |  | Mrk 12:28b-34 |
| 2026-06-05 | Jumat | Merah | Pekan Biasa IX | PW | PW S. Bonifasius, Uskup dan Martir | 2Tim 3:10-17 | Mzm 119:157.160.161.165.166.168 |  | Mrk 12:35-37 |
| 2026-06-06 | Sabtu | Hijau | Pekan Biasa IX | PF | PF S. Norbertus, Uskup | 2Tim 4:1-8 | Mzm 71:8-9.14-15ab.16-17.22 |  | Mrk 12:38-44 |
| 2026-06-07 | Minggu | Putih | Hari Raya | HR |  | Ul 8:2-3.14b-16a | Mzm 147:12-13.14-15.19-20 | 1Kor 10:16-17 | Yoh 6:51-58 |
| 2026-06-08 | Senin | Hijau | Pekan Biasa X |  |  | 1Raj 17:1-6 | Mzm 121:1-2.3-4.5-6.7-8 |  | Mat 5:1-12 |
| 2026-06-09 | Selasa | Hijau | Pekan Biasa X | PF | PF S. Efrem, Diakon dan Pujangga Gereja | 1Raj 17:7-16 | Mzm 4:2-3.4-5.7-8 |  | Mat 5:13-16 |
| 2026-06-10 | Rabu | Hijau | Pekan Biasa X |  |  | 1Raj 18:20-39 | Mzm 16:1-2a.4.5.8.11 |  | Mat 5:17-19 |
| 2026-06-11 | Kamis | Merah | Pekan Biasa X | PW | PW S. Barnabas, Rasul | Kis 11:21b-26;13:1-3 | Mzm 98:2-3ab.3c-4.5-6 |  | Mat 10:7-13 |
| 2026-06-12 | Jumat | Putih | Hari Raya | HR |  | Ul 7:6-11 | Mzm 103:1-2.3-4.6-7.8.10 | 1Yoh 4:7-16 | Mat 11:25-30 |
| 2026-06-13 | Sabtu | Putih | Hari Biasa | PW | PW S. Antonius dari Padua, Imam dan Pujangga Gereja | Yes 61:9-11 | 1Sam 2:1.4-5.6-7.8abcd |  | Luk 2:41-51 |
| 2026-06-14 | Minggu | Hijau | Pekan Biasa XI |  |  | Kel 19:2-6a | Mzm 100:2.3.5 | Rom 5:6-11 | Mat 9:36-10:8 |
| 2026-06-15 | Senin | Hijau | Pekan Biasa XI |  |  | 1Raj 21:1-16 | Mzm 5:2-3.5-6.7 |  | Mat 5:38-42 |
| 2026-06-16 | Selasa | Hijau | Pekan Biasa XI |  |  | 1Raj 21:17-29 | Mzm 51:3-4.5-6a.11.16 |  | Mat 5:43-48 |
| 2026-06-17 | Rabu | Hijau | Pekan Biasa XI |  |  | 2Raj 2:1.6-14 | Mzm 31:20.21.24 |  | Mat 6:1-6.16-18 |
| 2026-06-18 | Kamis | Hijau | Pekan Biasa XI |  |  | Sir 48:1-14 | Mzm 97:1-2.3-4.5-6.7 |  | Mat 6:7-15 |
| 2026-06-19 | Jumat | Hijau | Pekan Biasa XI | PF | PF S. Romualdus, Abas | 2Raj 11:1-4.9-18.20 | Mzm 132:11-12.13-14.17-18 |  | Mat 6:19-23 |
| 2026-06-20 | Sabtu | Hijau | Pekan Biasa XI |  |  | 2Taw 24:17-25 | Mzm 89:4-5.29-30.31-32.33-34 |  | Mat 6:24-34 |
| 2026-06-21 | Minggu | Hijau | Pekan Biasa XII |  |  | Yer 20:10-13 | Mzm 69:8-10.14.17.33-35 | Rom 5:12-15 | Mat 10:26-33 |
| 2026-06-22 | Senin | Hijau | Pekan Biasa XII | PF | PF S. Yohanes Fisher, Uskup, dan S. Tomas More, Martir PF S. Paulinus dari Nola, Uskup | 2Raj 17:5-8.13-15a.18 | Mzm 60:3.4-5.12-13 |  | Mat 7:1-5 |
| 2026-06-23 | Selasa | Hijau | Pekan Biasa XII |  |  | 2Raj 19:9b-11.14-21.31-35a.36 | Mzm 48:2-3a.3b-4.10-11 |  | Mat 7:6.12-14 |
| 2026-06-24 | Rabu | Putih | Pekan Biasa XII | HR |  | Yes 49:1-6 | Mzm 139:1-3.13-14ab.14c-15 | Kis 13:22-26 | Luk 1:57-66.80 |
| 2026-06-25 | Kamis | Hijau | Pekan Biasa XII |  |  | 2Raj 24:8-17 | Mzm 79:1-2.3-5.8.9 |  | Mat 7:21-29 |
| 2026-06-26 | Jumat | Hijau | Pekan Biasa XII |  |  | 2Raj 25:1-12 | Mzm 137:1-2.3.4-5.6 |  | Mat 8:1-4 |
| 2026-06-27 | Sabtu | Hijau | Pekan Biasa XII | PF | PF S. Sirilus dari Aleksandaria, Uskup dan Pujangga Gereja | Rat 2:2.10-14.18-19 | Mzm 74:1-2.3-5a.5b-7.20-21 |  | Mat 8:5-17 |
| 2026-06-28 | Minggu | Hijau | Pekan Biasa XIII |  |  | 2Raj 4:8-11.14-16a | Mzm 89:2-3.16-17.18-19 | Rom 6:3-4.8-11 | Mat 10:37-42 |
| 2026-06-29 | Senin | Merah | Pekan Biasa XIII | HR |  | Kis 12:1-11 | Mzm 34:2-3.4-5.6-7.8-9 | 2Tim 4:6-8.17-18 | Mat 16:13-19 |
| 2026-06-30 | Selasa | Hijau | Pekan Biasa XIII | PF | PF Para Martir Pertama Umat di Roma | Am 3:1-8; 4:11-12 | Mzm 5:5-6.7.8 |  | Mat 8:23-27 |
| 2026-07-01 | Rabu | Hijau | Pekan Biasa XIII |  |  | Am 5:14-15.21-24 | Mzm 50:7.8-9.10-11.12-13.l6bc-17 |  | Mat 8:28-34 |
| 2026-07-02 | Kamis | Hijau | Pekan Biasa XIII |  |  | Am 7:10-17 | Mzm 19:8.9.10.11 |  | Mat 9:1-8 |
| 2026-07-03 | Jumat | Merah | Pekan Biasa XIII | Pesta |  | Ef 2:19-22 | Mzm 117:1.2 |  | Yoh 20:24-29 |
| 2026-07-04 | Sabtu | Hijau | Pekan Biasa XIII | PF | PF S. Elisabet dari Portugal | Am 9:11-15 | Mzm 85:9.11-12.13-14 |  | Mat 9:14-17 |
| 2026-07-05 | Minggu | Hijau | Pekan Biasa XIV |  |  | Za 9:9-10 | Mzm 145:1-2.8-9.10-11.13cd-14 | Rom 8:9.11-13 | Mat 11:25-30 |
| 2026-07-06 | Senin | Hijau | Pekan Biasa XIV | PF | PF S. Maria Goretti, Perawan dan Martir | Hos 2:13.14b-15.18-19 | Mzm  145:2-3.4-5.6-7.8-9 |  | Mat 9:18-26 |
| 2026-07-07 | Selasa | Hijau | Pekan Biasa XIV |  |  | Hos  8:4-7.11-13 | Mzm  115:3-4.5-6.7ab-8.9-10 |  | Mat  9:32-38 |
| 2026-07-08 | Rabu | Hijau | Pekan Biasa XIV |  |  | Hos  10:1-3.7-8.12 | Mzm  105:2-3.4-5.6-7 |  | Mat 10:1-7 |
| 2026-07-09 | Kamis | Hijau | Pekan Biasa XIV | PF | PF S. Agustinus Zhao Rong, Imam Martir, dkk. Tiongkok PF S. Gregorius Grassi, Uskup | Hos  11:1b.3-4.8c-9 | Mzm  80:2ac.3b.15-16 |  | Mat  10:7-15 |
| 2026-07-10 | Jumat | Hijau | Pekan Biasa XIV |  |  | Hos 14:2-10 | Mzm  51:3-4.8-9.12-13.14.17 |  | Mat  10:16-23 |
| 2026-07-11 | Sabtu | Putih | Pekan Biasa XIV | PW | PW S. Benediktus, Abas | Yes  6:1-8 | Mzm  93:1ab.1c-2.5 |  | Mat 10:24-33 |
| 2026-07-12 | Minggu | Hijau | Pekan Biasa XV |  |  | Yes 55:10-11 | Mzm 65:10abcd.10e-11.12-13.14 | Rom 8:18-23 | Mat 13:1-23 |
| 2026-07-13 | Senin | Hijau | Pekan Biasa XV | PF | PF S. Henrikus | Yes  1:11-17 | Mzm 50:8-9.16bc-17.21.23 |  | Mat  10:34 - 11:1 |
| 2026-07-14 | Selasa | Hijau | Pekan Biasa XV | PF | PF S. Kamilus de Lellis, Imam | Yes  7:1-9 | Mzm  48:2-3a.3b-4.5-6.7-8 |  | Mat  11:20-24 |
| 2026-07-15 | Rabu | Putih | Pekan Biasa XV | PW | PW S. Bonaventura, Uskup dan Pujangga Gereja | Yes  10:5-7.13-16 | Mzm  94:5-10.14-15 |  | Mat  11:25-27 |
| 2026-07-16 | Kamis | Hijau | Pekan Biasa XV | PF | PF S.P. Maria di Gunung Karmel | Yes  26:7-9.12.16-19 | Mzm  102:13-14ab.15.l6-18.19-21 |  | Mat  11:28-30 |
| 2026-07-17 | Jumat | Hijau | Pekan Biasa XV |  |  | Yes  38:1-6.21-22.7-8 | Yes 38:10.11.12abc.16 |  | Mat  12:1-8 |
| 2026-07-18 | Sabtu | Hijau | Pekan Biasa XV |  |  | Mi  2:1-5 | Mzm  10:1-2 3-4.7-8.14 |  | Mat  12:14-21 |
| 2026-07-19 | Minggu | Hijau | Pekan Biasa XVI |  |  | Keb 12:13.16-19 | Mzm 86:5-6.9-10.15-16a | Rom 8:26-27 | Mat 13:24-43 |
| 2026-07-20 | Senin | Hijau | Pekan Biasa XVI | PF | PF S. Apolinaris, Uskup dan Martir | Mi  6:1-4.6-8 | Mzm  50:5-6.8-9.16bc.17.21.23 |  | Mat  12:38-42 |
| 2026-07-21 | Selasa | Hijau | Pekan Biasa XVI | PF | PF S. Laurensius dari Brindisi, Imam dan Pujangga Gereja | Mi  7:14-15.18-20 | Mzm  85:2-4.5-6.7-8 |  | Mat 12:46-50 |
| 2026-07-22 | Rabu | Putih | Pekan Biasa XVI | Pesta |  | Kid 3:1-4a | Mzm 63:2.3-4.5-6.8-9 |  | Yoh 20:1.11-18 |
| 2026-07-23 | Kamis | Hijau | Pekan Biasa XVI | PF | PF S. Birgitta, Biarawati | Yer 2:1-3.7-8.12-13 | Mzm  36:6-7ab.8-11 |  | Mat  13:10-17 |
| 2026-07-24 | Jumat | Hijau | Pekan Biasa XVI | PF | PF S. Sharbel Makhluf, Imam | Yer  3:14-17 | Yer 31:10.11-12ab.13 |  | Mat  13:18-23 |
| 2026-07-25 | Sabtu | Merah | Pekan Biasa XVI | Pesta |  | 2Kor 4:7-15 | Mzm 126:1-2ab.2cd-3.4-5.6 |  | Mat 20:20-28 |
| 2026-07-26 | Minggu | Hijau | Pekan Biasa XVII |  |  | 1Raj 3:5.7-12 | Mzm 119:57.72.76-77.127-128.129-130 | Rom 8:28-30 | Mat 13:44-52 |
| 2026-07-27 | Senin | Hijau | Pekan Biasa XVII |  |  | Yer 13:1-11 | Ul 32:18-19.20-21 |  | Mat 13:31-35 |
| 2026-07-28 | Selasa | Hijau | Pekan Biasa XVII |  |  | Yer  14:17-22 | Mzm  79:8.9.11.13 |  | Mat  13:36-43 |
| 2026-07-29 | Rabu | Putih | Pekan Biasa XVII | PW | PW S. Marta, Maria, dan Lazarus | 1Yoh 4:7-16 | Mzm 34:2-3.4-5.6-7.8-9.10-11 |  | Yoh 11:19-27 |
| 2026-07-30 | Kamis | Hijau | Pekan Biasa XVII | PF | PF S. Petrus Krisologus, Uskup dan Pujangga Gereja | Yer 18:1-6 | Mzm 146:2abc.2d-4.5-6 |  | Mat 13:47-53 |
| 2026-07-31 | Jumat | Putih | Pekan Biasa XVII | PW | PW S. Ignasius dari Loyola, Imam | Yer  26:1-9 | Mzm  69:5.8-10.14 |  | Mat  13:54-58 |
| 2026-08-01 | Sabtu | Putih | Pekan Biasa XVII | PW | PW S. Alfonsus Maria de Liguori, Uskup dan Pujangga Gereja | Yer  26:11-16.24 | Mzm  69:15-16.30-31.33-34 |  | Mat  14:1-12 |
| 2026-08-02 | Minggu | Hijau | Pekan Biasa XVIII |  |  | Yes 55:1-3 | Mzm 145:8-9.15-16.17-18 | Rom 8:35.37-39 | Mat 14:13-21 |
| 2026-08-03 | Senin | Hijau | Pekan Biasa XVIII |  |  | Yer 28:1-17 | Mzm 119:29.43.79.80.95.102 |  | Mat 14:13-21 |
| 2026-08-04 | Selasa | Putih | Pekan Biasa XVIII | PW | PW S. Yohanes Maria Vianney, Imam | Yer 30:1-2.12-15.18-22 | Mzm 102:16-21.29.22-23 |  | Mat 15:1-2.10-14 |
| 2026-08-05 | Rabu | Hijau | Pekan Biasa XVIII | PF | PF Pemberkatan Gereja Basilik SP Maria | Yer 31:1-7 | Yer 31:10.11-12ab.13 |  | Mat 15:21-28 |
| 2026-08-06 | Kamis | Putih | Pekan Biasa XVIII | Pesta |  | Dan 7:9-10.13-14 | Mzm 97:1-2.5-6.9 | 2Ptr 1:16-19 | Mat 17:1-9 |
| 2026-08-07 | Jumat | Hijau | Pekan Biasa XVIII | PF | PF S. Kayetanus, Imam PF S. Sistus II, Paus, dkk. Martir | Nah 1:15;2:2;3:1-3.6-7 | Ul 32:35cd-36ab.39abcd.41 |  | Mat 16:24-28 |
| 2026-08-08 | Sabtu | Putih | Pekan Biasa XVIII | PW | PW S. Dominikus, Pendiri Ordo Pengkotbah, Imam | Hab 1:12-2:4 | Mzm 9:8-9.10-11.12-13 |  | Mat 17:14-20 |
| 2026-08-09 | Minggu | Hijau | Pekan Biasa XIX |  |  | 1Raj 19:9a.11-13a | Mzm 85:9ab-10.11-12.13-14 | Rom 9:1-5 | Mat 14:22-33 |
| 2026-08-10 | Senin | Merah | Pekan Biasa XIX | Pesta |  | 2Kor 9:6-10 | Mzm 112:1-2.5-9 |  | Yoh 12:24-26 |
| 2026-08-11 | Selasa | Putih | Pekan Biasa XIX | PW | PW S. Klara, Perawan | Yeh 2:8-3:4 | Mzm 119:14.24.72.103.111.131 |  | Mat 18:1-5.10.12-14 |
| 2026-08-12 | Rabu | Hijau | Pekan Biasa XIX | PF | PF S. Yohana Frasiska dari Chantal | Yeh 9:1-7;10:18-22 | Mzm 113:1-2.3-4.5-6 |  | Mat 18:15-20 |
| 2026-08-13 | Kamis | Hijau | Pekan Biasa XIX | PF | PF S. Hippolitus, Imam dan Martir PF S. Pontianus, Paus | Yeh 12:1-12 | Mzm 78:56-59.61-62 |  | Mat 18:21-19:1 |
| 2026-08-14 | Jumat | Merah | Pekan Biasa XIX | PW | PW S. Maksimilianus Maria Kolbe, Imam dan Martir | Yeh 16:1-15.60.63 | Yes 12:2-3.4bcd.5-6 |  | Mat 19:3-12 |
| 2026-08-15 | Sabtu | Hijau | Pekan Biasa XIX | PF | PF S. Tarsisius, Martir Ekaristi.  Pelindung putra-putri altar dan penerima komuni pertama. | Yeh 18:1-10.13b.30-32 | Mzm 51:12-15.18-19 |  | Mat 19:13-15 |
| 2026-08-16 | Minggu | Putih | Hari Raya | HR |  | Why 11:19a;12:1.3-6a.10ab | Mzm 45:10c-12.16 | 1Kor 15:20-26 | Luk 1:39-56 |
| 2026-08-17 | Senin | Putih | Pekan Biasa XX | HR |  | Sir 10:1-8 | Mzm 101:1a.2ac.3a.6-7 | 1Ptr 2:13-17 | Mat 22:15-21 |
| 2026-08-18 | Selasa | Hijau | Pekan Biasa XX |  |  | Yeh 28:1-10 | Ul 32:26-28,30.35c-36d |  | Mat 19:23-30 |
| 2026-08-19 | Rabu | Hijau | Pekan Biasa XX | PF | PF S. Yohanes Eudes, Imam | Yeh 34:1-11 | Mzm 23:1-6 |  | Mat 20:1-16a |
| 2026-08-20 | Kamis | Putih | Pekan Biasa XX | PW | PW S. Bernardus, Abas dan Pujangga Gereja | Yeh 36:23-28 | Mzm 51:12-15.18-19 |  | Mat 22:1-14 |
| 2026-08-21 | Jumat | Putih | Pekan Biasa XX | PW | PW S. Pius X, Paus | Yeh 37:1-14 | Mzm 107:2-3.4-5.6-7.8-9 |  | Mat 22:34-40 |
| 2026-08-22 | Sabtu | Putih | Pekan Biasa XX | PW | PW SP Maria, Ratu | Yeh 43:1-7a | Mzm 85:9ab-10.11-12.13-14 |  | Mat 23:1-12 |
| 2026-08-23 | Minggu | Hijau | Pekan Biasa XXI |  |  | Yes 22:19-23 | Mzm 138:1-2a.2bc-3.6.8bc | Rom 11:33-36 | Mat 16:13-20 |
| 2026-08-24 | Senin | Merah | Pekan Biasa XXI | Pesta |  | Why 21:9b-14 | Mzm 145:10-11.12-13ab.17-18 |  | Yoh 1:45-51 |
| 2026-08-25 | Selasa | Hijau | Pekan Biasa XXI | PF | PF S. Yosef dari Calasanz, Imam PF S. Ludowikus | 2Tes 2:1-3a.13b-17 | Mzm 96:10.11-12a.12b-13 |  | Mat 23:23-26 |
| 2026-08-26 | Rabu | Hijau | Pekan Biasa XXI |  |  | 2Tes 3:6-10.16-18 | Mzm 128:1-2.4-5 |  | Mat 23:27-32 |
| 2026-08-27 | Kamis | Putih | Pekan Biasa XXI | PW | PW S. Monika | 1Kor 1:1-9 | Mzm 145:2-3.4-5.6-7 |  | Mat 24:42-51 |
| 2026-08-28 | Jumat | Putih | Pekan Biasa XXI | PW | PW S. Agustinus, Uskup dan Pujangga Gereja | 1Kor 1:17-25 | Mzm 33:1-2.4-5.10ab.11 |  | Mat 25:1-13 |
| 2026-08-29 | Sabtu | Merah | Pekan Biasa XXI | PW | PW Wafatnya S. Yohanes Pembaptis, Martir | Yer 1:17-19 | Mzm 71:1-2.3-4a.5-6ab.15ab.17 |  | Mrk 6:17-29 |
| 2026-08-30 | Minggu | Hijau | Pekan Biasa XXII |  |  | Yer 20:7-9 | Mzm 63:2.3-4.5-6.8-9 | Rom 12:1-2 | Mat 16:21-27 |
| 2026-08-31 | Senin | Hijau | Pekan Biasa XXII |  |  | 1Kor 2:1-5 | Mzm 119:97.98.99.100.101.102 |  | Luk 4:16-30 |
| 2026-09-01 | Selasa | Hijau | Pekan Biasa XXII |  |  | 1Kor 2:10b-16 | Mzm 145:8-9.10-11.12-13ab.13cd-14 |  | Luk 4:31-37 |
| 2026-09-02 | Rabu | Hijau | Pekan Biasa XXII |  |  | 1Kor 3:1-9 | Mzm 33:12-13.14-15.20-21 |  | Luk 4:38-44 |
| 2026-09-03 | Kamis | Putih | Pekan Biasa XXII | PW | PW S. Gregorius Agung, Paus dan Pujangga Gereja | 1Kor 3:18-23 | Mzm 24:1-2.3-4ab.5-6 |  | Luk 5:1-11 |
| 2026-09-04 | Jumat | Hijau | Pekan Biasa XXII |  |  | 1Kor 4:1-5 | Mzm 37:3-6.27-28.39-40 |  | Luk 5:33-39 |
| 2026-09-05 | Sabtu | Hijau | Pekan Biasa XXII | PF | PF S. Teresa dari Kalkuta, Biarawati | 1Kor 4:6b-15 | Mzm 145:17-18.19-20.21 |  | Luk 6:1-5 |
| 2026-09-06 | Minggu | Hijau | Pekan Biasa XXIII |  |  | Yeh 33:7-9 | Mzm 95:1-2.6-7.8-9 | Rom 13:8-10 | Mat 18:15-20 |
| 2026-09-07 | Senin | Hijau | Pekan Biasa XXIII |  |  | 1Kor 5:1-8 | Mzm 5:5-6.7.12 |  | Luk 6:6-11 |
| 2026-09-08 | Selasa | Putih | Pekan Biasa XXIII | Pesta |  | Mi 5:1-4a | Mzm 13:6ab.6cd |  | Mat 1:1-16.18-23 |
| 2026-09-09 | Rabu | Hijau | Pekan Biasa XXIII | PF | PF S. Petrus Klaver, Imam | 1Kor 7:25-31 | Mzm 45:11-12.14-17 |  | Luk 6:20-26 |
| 2026-09-10 | Kamis | Hijau | Pekan Biasa XXIII |  |  | 1Kor 8:1b-7.11-13 | Mzm 139:1-3.13-14ab.23-24 |  | Luk 6:27-38 |
| 2026-09-11 | Jumat | Hijau | Pekan Biasa XXIII |  |  | 1Kor 9:16-19.22b-27 | Mzm 84:3.4.5-6.12 |  | Luk 6:39-42 |
| 2026-09-12 | Sabtu | Hijau | Pekan Biasa XXIII | PF | PF Nama SP Maria yang Tersuci | 1Kor 10:14-22a | Mzm 116:12-13.17-18 |  | Luk 6:43-49 |
| 2026-09-13 | Minggu | Hijau | Pekan Biasa XXIV |  |  | Sir 27:30-28:9 | Mzm 103:1-2.3-4.9-10.11-12 | Rom 14:7-9 | Mat 18:21-35 |
| 2026-09-14 | Senin | Merah | Pekan Biasa XXIV | Pesta |  | Bil 21:4-9 | Mzm 78:1-2.34-35.36-37.38 | Flp 2:6-11 | Yoh 3:13-17 |
| 2026-09-15 | Selasa | Putih | Pekan Biasa XXIV | PW | PW S.P. Maria Berdukacita | Ibr 5:7-9 | Mzm 31:2-3a.3b-4.5-6.15-16.20 |  | Yoh 19:25-27 |
| 2026-09-16 | Rabu | Merah | Pekan Biasa XXIV | PW | PW S. Kornelius, Paus, dan Siprianus, Uksup; Martir | 1Kor 12:31-13:13 | Mzm 33:2-5.12.22 |  | Luk 7:31-35 |
| 2026-09-17 | Kamis | Hijau | Pekan Biasa XXIV | PF | PF S. Robertus Bellarmino, Uskup dan Pujangga Gereja | 1Kor 15:1-11 | Mzm 118:1-2.16a-17.28 |  | Luk 7:36-50 |
| 2026-09-18 | Jumat | Hijau | Pekan Biasa XXIV |  |  | 1Kor 15:12-20 | Mzm 17:1.6-7.8b.15 |  | Luk 8:1-3 |
| 2026-09-19 | Sabtu | Hijau | Pekan Biasa XXIV | PF | PF S. Yanuarius, Uskup dan Martir | 1Kor 15:35-37.42-49 | Mzm 56:10-14 |  | Luk 8:4-15 |
| 2026-09-20 | Minggu | Hijau | Pekan Biasa XXV |  |  | Yes 55:6-9 | Mzm 145:2-3.8-9.17-18 | Flp 1:20c-24.27a | Mat 20:1-16 |
| 2026-09-21 | Senin | Merah | Pekan Biasa XXV | Pesta |  | Ef 4:1-7.11-13 | Mzm 19:2-3.4-5 |  | Mat 9:9-13 |
| 2026-09-22 | Selasa | Hijau | Pekan Biasa XXV |  |  | Ams 21:1-6.10-13 | Mzm 119:1.27.30.34.35.44 |  | Luk 8:19-21 |
| 2026-09-23 | Rabu | Putih | Pekan Biasa XXV | PW | PW S. Padre Pio dari Pietrelcina, Imam | Ams 30:5-9 | Mzm 119:29.72.89.101.104.163 |  | Luk 9:1-6 |
| 2026-09-24 | Kamis | Hijau | Pekan Biasa XXV |  |  | Pkh 1:2-11 | Mzm 90:3-6.12-14.17 |  | Luk 9:7-9 |
| 2026-09-25 | Jumat | Hijau | Pekan Biasa XXV |  |  | Pkh 3:1-11 | Mzm 144:1a.2abc.3-4 |  | Luk 9:18-22 |
| 2026-09-26 | Sabtu | Hijau | Pekan Biasa XXV | PF | PF S. Kosmas dan S. Damianus, Martir | Pkh 11:9-12:8 | Mzm 90:3-6.12-14.17 |  | Luk 9:43b-45 |
| 2026-09-27 | Minggu | Hijau | Pekan Biasa XXVI |  |  | Yeh 18:25-28 | Mzm 25:4bc-5.6-7.8-9 | Flp 2:1-11 | Mat 21:28-32 |
| 2026-09-28 | Senin | Hijau | Pekan Biasa XXVI | PF | PF S. Laurensius Ruiz dkk. Martir PF S. Wenseslaus, Martir | Ayb 1:6-22 | Mzm 17:1-3.6-7 |  | Luk 9:46-50 |
| 2026-09-29 | Selasa | Putih | Pekan Biasa XXVI | Pesta |  | Dan 7:9-10.13-14 | Mzm 138:1-2a.2bc-3.4-5 |  | Yoh 1:47-51 |
| 2026-09-30 | Rabu | Putih | Pekan Biasa XXVI | PW | PW S. Hieronimus, Imam dan Pujangga Gereja | Ayb 9:1-12.14-16 | Mzm 88:10bc-11.12-13.14-15 |  | Luk 9:57-62 |
| 2026-10-01 | Kamis | Putih | Pekan Biasa XXVI | Pesta |  | Yes 66:10-14b | Mzm 131:1.2.3 |  | Mat 18:1-5 |
| 2026-10-02 | Jumat | Putih | Pekan Biasa XXVI | PW | PW Para Malaikat Pelindung | Kel 23:20-23a | Mzm 91:1-2.3-4.5-6.10-11 |  | Mat 18:1-5.10 |
| 2026-10-03 | Sabtu | Hijau | Pekan Biasa XXVI |  |  | Ayb 42:1-3.5-6.12-16 | Mzm 119:66.71.75.91.125.130 |  | Luk 10:17-24 |
| 2026-10-04 | Minggu | Hijau | Pekan Biasa XXVII |  |  | Yes 5:1-7 | Mzm 80:9.12.13-14.15-16.19-20 | Flp 4:6-9 | Mat 21:33-43 |
| 2026-10-05 | Senin | Hijau | Pekan Biasa XXVII | PF | PF S. Faustina Kowalska, Perawan | Gal 1:6-12 | Mzm 111:1-2.7-9.10c |  | Luk 10:25-37 |
| 2026-10-06 | Selasa | Hijau | Pekan Biasa XXVII | PF | PF S. Bruno, Imam | Gal 1:13-24 | Mzm 139:1-3.13-14ab.14c-15 |  | Luk 10:38-42 |
| 2026-10-07 | Rabu | Putih | Pekan Biasa XXVII | PF | PW SP Maria, Ratu Rosario | Gal 2:1-2.7-14 | Mzm 117:1.2 |  | Luk 11:1-4 |
| 2026-10-08 | Kamis | Hijau | Pekan Biasa XXVII |  |  | Gal 3:1-5 | Luk 1:69-70.71-72.73-75 |  | Luk 11:5-13 |
| 2026-10-09 | Jumat | Hijau | Pekan Biasa XXVII | PF | PF S. Yohanes Leonardus, Imam PF S. Dionisius, Uskup dkk. Martir | Gal 3:7-14 | Mzm 111:1-2.3-4.5-6 |  | Luk 11:15-26 |
| 2026-10-10 | Sabtu | Hijau | Pekan Biasa XXVII |  |  | Gal 3:22-29 | Mzm 105:2-3.4-5.6-7 |  | Luk 11:27-28 |
| 2026-10-11 | Minggu | Hijau | Pekan Biasa XXVIII |  |  | Yes 25:6-10a | Mzm 23:1-3a.3b-4.5.6 | Flp 4:12-14.19-20 | Mat 22:1-14 |
| 2026-10-12 | Senin | Hijau | Pekan Biasa XXVIII |  |  | Gal 4:22-24.26-27.31-5:1 | Mzm 113:1-2.3-4.5a.6-7 |  | Luk 11:29-32 |
| 2026-10-13 | Selasa | Hijau | Pekan Biasa XXVIII |  |  | Gal 4:31b-5:6 | Mzm 119:41.43.44.45.47.48 |  | Luk 11:37-41 |
| 2026-10-14 | Rabu | Hijau | Pekan Biasa XXVIII | PF | PF S. Kalistus, Paus dan Martir | Gal 5:18-25 | Mzm 1:1-2.3.4.6 |  | Luk 11:42-46 |
| 2026-10-15 | Kamis | Putih | Pekan Biasa XXVIII | PW | PW S. Teresia dr Yesus, Perawan dan Pujangga Gereja | Ef 1:1-10 | Mzm 98:1.2-3ab.3cd-4.5-6 |  | Luk 11:47-54 |
| 2026-10-16 | Jumat | Hijau | Pekan Biasa XXVIII | PF | PF S. Margareta Maria Alacoque, Perawan PF S. Hedwig, Biarawati | Ef 1:11-14 | Mzm 33:1-2.4-5.12-13 |  | Luk 12:1-7 |
| 2026-10-17 | Sabtu | Merah | Pekan Biasa XXVIII | PW | PW S. Ignasius dari Antiokhia, Uskup dan Martir | Ef 1:15-23 | Mzm 8:2-3a.4-5.6-7 |  | Luk 12:8-12 |
| 2026-10-18 | Minggu | Hijau | Pekan Biasa XXIX |  |  | Yes 45:1.4-6 | Mzm 96:1.3-4-5.7-8.9-10ac | 1Tes 1:1-5b | Mat 22:15-21 |
| 2026-10-19 | Senin | Hijau | Pekan Biasa XXIX | PF | PF S. Paulus dari salib, Imam PF S. Yohanes de Brebeuf dan Ishak Jogues, Imam, dan teman-temannya; Martir | Ef 2:1-10 | Mzm 100:2.3.4.5 |  | Luk 12:13-21 |
| 2026-10-20 | Selasa | Hijau | Pekan Biasa XXIX |  |  | Ef 2:12-22 | Mzm 85:9ab-10.11-12.13-14 |  | Luk 12:35-38 |
| 2026-10-21 | Rabu | Hijau | Pekan Biasa XXIX |  |  | Ef 3:2-12 | Yes 12:2-3.4bcd.5-6 |  | Luk 12:39-48 |
| 2026-10-22 | Kamis | Hijau | Pekan Biasa XXIX |  |  | Ef 3:14-21 | Mzm 33:1-2.4-5.11-12.18-19 |  | Luk 12:49-53 |
| 2026-10-23 | Jumat | Hijau | Pekan Biasa XXIX | PF | PF S. Yohanes dari Capestrano, Imam | Ef 4:1-6 | Mzm 24:1-2.3-4ab.5-6 |  | Luk 12:54-59 |
| 2026-10-24 | Sabtu | Hijau | Pekan Biasa XXIX | PF | PF S. Antonius Maria Claret, Uskup | Ef 4:7-16 | Mzm 122:1-2.3-4a.4b-5 |  | Luk 13:1-9 |
| 2026-10-25 | Minggu | Hijau | Pekan Biasa XXX |  |  | Kel 22:21-27 | Mzm 18:2-3a.3bc-4.47.51ab | 1Tes 1:5c-10 | Mat 22:34-40 |
| 2026-10-26 | Senin | Hijau | Pekan Biasa XXX |  |  | Ef 4:32-5:8 | Mzm 1:1-2.3.4.6 |  | Luk 13:10-17 |
| 2026-10-27 | Selasa | Hijau | Pekan Biasa XXX |  |  | Ef 5:21-33 | Mzm 128:1-2.3.4-5 |  | Luk 13:18-21 |
| 2026-10-28 | Rabu | Merah | Pekan Biasa XXX | Pesta |  | Ef 2:19-22 | Mzm 19:2-3.4-5 |  | Luk 6:12-19 |
| 2026-10-29 | Kamis | Hijau | Pekan Biasa XXX |  |  | Ef 6:10-20 | Mzm 144:1.2.9-10 |  | Luk 13:31-35 |
| 2026-10-30 | Jumat | Hijau | Pekan Biasa XXX |  |  | Flp 1:1-11 | Mzm 111:1-2.3-4.5-6 |  | Luk 14:1-6 |
| 2026-10-31 | Sabtu | Hijau | Pekan Biasa XXX |  |  | Flp 1:18b-26 | Mzm 42:2.3.5bcd |  | Luk 14:1.7-11 |
| 2026-11-01 | Minggu | Putih | Pekan Biasa XXXI | HR |  | Why 7:2-4.9-14 | Mzm 24:1-2.3-4ab.5-6 | 1Yoh 3:1-3 | Mat 5:1-12a |
| 2026-11-02 | Senin | Ungu | Pekan Biasa XXXI | HR |  | 2Mak 12:43-46 | Mzm 143:1-2.5-6.7ab.8ab.10 | 1Kor 15:20-24a.25-28 | Yoh 6:37-40 |
| 2026-11-03 | Selasa | Hijau | Pekan Biasa XXXI | PF | PF S. Martinus de Porres, Biarawan | Flp 2:5-11 | Mzm 22:26b-30a.31-32 |  | Luk 14:15-24 |
| 2026-11-04 | Rabu | Putih | Pekan Biasa XXXI | PW | PW S. Karolus Borromues, Uskup | Flp 2:12-18 | Mzm 27:1.4.13-14 |  | Luk 14:25-33 |
| 2026-11-05 | Kamis | Hijau | Pekan Biasa XXXI |  |  | Flp 3:3-8a | Mzm 105:2-3.4-5.6-7 |  | Luk 15:1-10 |
| 2026-11-06 | Jumat | Hijau | Pekan Biasa XXXI |  |  | Flp 3:17 - 4:1 | Mzm 122:1-2.3-4a.4b-5 |  | Luk 16:1-8 |
| 2026-11-07 | Sabtu | Hijau | Pekan Biasa XXXI |  |  | Flp 4:10-19 | Mzm 112:1-2.5-6.8a.9 |  | Luk 16:9-15 |
| 2026-11-08 | Minggu | Hijau | Pekan Biasa XXXII |  |  | Keb 6:12-17 | Mzm 63:2.3-4.5-6.7-8 | 1Tes 4:13-18 | Mat 25:1-13 |
| 2026-11-09 | Senin | Putih | Pekan Biasa XXXII | Pesta |  | Yeh 47:1-2.8-9.12 | Mzm 46:2-3.5-6.8-9 | 1Kor 3:9b-11.16-17 | Yoh 2:13-22 |
| 2026-11-10 | Selasa | Putih | Pekan Biasa XXXII | PW | PW S. Leo Agung, Paus dan Pujangga Gereja | Tit 2:1-8.11-14 | Mzm 37:3-4.18.23.27.29 |  | Luk 17:7-10 |
| 2026-11-11 | Rabu | Putih | Pekan Biasa XXXII | PW | PW S. Martinus dr Tours, Uskup | Tit 3:1-7 | Mzm 23:1-3a.3b-4.5.6 |  | Luk 17:11-19 |
| 2026-11-12 | Kamis | Merah | Pekan Biasa XXXII | PW | PW S. Yosafat, Uskup dan Martir | Flm 7-20 | Mzm 146:7.8-9a.9bc-10 |  | Luk 17:20-25 |
| 2026-11-13 | Jumat | Hijau | Pekan Biasa XXXII |  |  | 2Yoh 1:4-9 | Mzm 119:1.2.10.11.17.18 |  | Luk 17:26-37 |
| 2026-11-14 | Sabtu | Hijau | Pekan Biasa XXXII |  |  | 3Yoh 5-8 | Mzm 112:1-2.3-4.5-6 |  | Luk 18:1-8 |
| 2026-11-15 | Minggu | Hijau | Pekan Biasa XXXIII |  |  | Ams 31:10-13.19-20.30-31 | Mzm 128:1-2.3.4-5 | 1Tes 5:1-6 | Mat 25:14-30 |
| 2026-11-16 | Senin | Hijau | Pekan Biasa XXXIII | PF | PF S. Gertrudis, Perawan PF S. Margareta dari Skotlandia | Why 1:1-4;2:1-5a | Mzm 1:1-2.3.4.6 |  | Luk 18:35-43 |
| 2026-11-17 | Selasa | Putih | Pekan Biasa XXXIII | PW | PW S. Elisabet dari Hungaria, Biarawati | Why 3:1-6.14-22 | Mzm 15:2-3ab.3cd-4ab.5 |  | Luk 19:1-10 |
| 2026-11-18 | Rabu | Hijau | Pekan Biasa XXXIII | PF | PF Gereja Basilik S. Petrus dan Paulus, Rasul | Why 4:1-11 | Mzm 150:1-2.3-4.5-6 |  | Luk 19:11-28 |
| 2026-11-19 | Kamis | Hijau | Pekan Biasa XXXIII |  |  | Why 5:1-10 | Mzm 149:1-2.3-4.5-6a.9b |  | Luk 19:41-44 |
| 2026-11-20 | Jumat | Hijau | Pekan Biasa XXXIII |  |  | Why 10:8-11 | Mzm 119:14.24.72.103.111.131 |  | Luk 19:45-48 |
| 2026-11-21 | Sabtu | Putih | Pekan Biasa XXXIII | PW | PW S. Maria Dipersembahkan kepada Allah | Why 11:4-12 | Mzm 144:1.2.9-10 |  | Luk 20:27-40 |
| 2026-11-22 | Minggu | Putih | Pekan Biasa XXXIV | HR |  | Yeh 34:11-12.15-17 | Mzm 23:1-2a.2b-3.5-6 | 1Kor 15:20-26a.28 | Mat 25:31-46 |
| 2026-11-23 | Senin | Hijau | Pekan Biasa XXXIV | PF | PF S. Kolumbanus, Abas PF S. Klemens I, Paus dan Martir | Why 14:1-3.4b-5 | Mzm 24:1-2.3-4ab.5-6 |  | Luk 21:1-4 |
| 2026-11-24 | Selasa | Merah | Pekan Biasa XXXIV | PW | PW S. Andreas Dũng-Lạc | Why 14:14-20 | Mzm 96:10.11-12.13 |  | Luk 21:5-11 |
| 2026-11-25 | Rabu | Hijau | Pekan Biasa XXXIV | PF | PF S. Katarina dr Aleksandria, Perawan dan Martir | Why 15:1-4 | Mzm 98:1.2-3ab.7-8.9 |  | Luk 21:12-19 |
| 2026-11-26 | Kamis | Hijau | Pekan Biasa XXXIV |  |  | Why 18:1-2.21-23;19:1-3.9a | Mzm 100:2.3.4.5 |  | Luk 21:20-28 |
| 2026-11-27 | Jumat | Hijau | Pekan Biasa XXXIV |  |  | Why 20:1-4.11-21:2 | Mzm 84:3.4.5-6a.8a |  | Luk 21:29-33 |
| 2026-11-28 | Sabtu | Hijau | Pekan Biasa XXXIV |  |  | Why 22:1-7 | Mzm 95:1-2.3-5.6-7 |  | Luk 21:34-36 |
| 2026-11-29 | Minggu | Ungu | Masa Adven I |  |  | Yes 63:16b-17;64:1.3b-8 | Mzm 80:2ac.3b.15-16.18-19 | 1Kor 1:3-9 | Mrk 13:33-37 |
| 2026-11-30 | Senin | Merah | Masa Adven I | Pesta |  | Rom 10:9-18 | Mzm 19:2-3.4-5 |  | Mat 4:18-22 |
| 2026-12-01 | Selasa | Putih | Masa Adven I | PW | PW B. Dionisius dan Redemptus, Biarawan, Martir | Yes 11:1-10 | Mzm 72:2.7-8.12-13.17 |  | Luk 10:21-24 |
| 2026-12-02 | Rabu | Ungu | Masa Adven I |  |  | Yes 25:6-10a | Mzm 23:1-3a.3b-4.5.6 |  | Mat 15:29-37 |
| 2026-12-03 | Kamis | Putih | Masa Adven I | Pesta |  | 1Kor 9:16-19.22-23 | Mzm 117:1.2 |  | Mrk 16:15-20 |
| 2026-12-04 | Jumat | Ungu | Masa Adven I | PF | PF S. Yohanes dari Damsyik, Imam dan Pujangga Gereja | Yes 29:17-24 | Mzm 27:1.4.13-14 |  | Mat 9:27-31 |
| 2026-12-05 | Sabtu | Ungu | Masa Adven I |  |  | Yes 30:19-21.23-26 | Mzm 147:1-2.3-4.5-6 |  | Mat 9:35-10:1.6-8 |
| 2026-12-06 | Minggu | Ungu | Masa Adven II |  |  | Yes 40:1-5.9-11 | Mzm 85:9ab-10.11-12.13-14 | 2Ptr 3:8-14 | Mrk 1:1-8 |
| 2026-12-07 | Senin | Putih | Masa Adven II | PW | PW S. Ambrosius, Uskup dan Pujangga Gereja | Yes 35:1-10 | * |  | Luk 5:17-26 |
| 2026-12-08 | Selasa | Putih | Masa Adven II | HR |  | Kej 3:9-15.20 | Mzm 98:1.2-3a.3bc-4 | Ef 1:3-6.11-12 | Luk 1:26-38 |
| 2026-12-09 | Rabu | Ungu | Masa Adven II | PF | PF Yohanes Didaci Cuauhtlatoatzin | Yes 40:25-31 | Mzm 103:1-2.3-4.8.10 |  | Mat 11:28-30 |
| 2026-12-10 | Kamis | Ungu | Masa Adven II |  |  | Yes 41:13-20 | Mzm 145:1.9.10-11.12-13ab |  | Mat 11:11-15 |
| 2026-12-11 | Jumat | Ungu | Masa Adven II | PF | PF S. Damasus I. Paus | Yes 48:17-19 | Mzm 1:1-2.3.4.6 |  | Mat 11:16-19 |
| 2026-12-12 | Sabtu | Ungu | Masa Adven II | PF | PF S. Maria Guadalupe | Sir 48:1-4.9-11 | Mzm 80:2ac.3b.15-16.18-19 |  | Mat 17:10-13 |
| 2026-12-13 | Minggu | Ungu | Masa Adven III |  |  | Yes 61:1-2a.10-11 | Luk 1:46-48.49-50.53-54 | 1Tes 5:16-24 | Yoh 1:6-8.19-28 |
| 2026-12-14 | Senin | Putih | Masa Adven III | PW | PW S. Yohanes dari Salib, Imam dan Pujangga Gereja | Bil 24:2-7.15-17a | Mzm 25:4b-5b.6-7c.8-9 |  | Mat 21:23-27 |
| 2026-12-15 | Selasa | Ungu | Masa Adven III |  |  | Zef 3:1-2.9-13 | Mzm 34:2-3.6-7.17-18.19.23 |  | Mat 21:28-32 |
| 2026-12-16 | Rabu | Ungu | Masa Adven III |  |  | Yes 45:6b-8.18.21b-25 | Mzm 85:9ab-10.11-12.13-14 |  | Luk 7:19-23 |
| 2026-12-17 | Kamis | Ungu | Masa Adven |  |  | Kej 49:2.8-10 | Mzm 72:1-2.3-4ab.7-8.17 |  | Mat 1:1-17 |
| 2026-12-18 | Jumat | Ungu | Masa Adven |  |  | Yer 23:5-8 | Mzm 72:1-2.12-13.18-19 |  | Mat 1:18-24 |
| 2026-12-19 | Sabtu | Ungu | Masa Adven |  |  | Hak 13:2-7.24-25a | Mzm 71:3-4a.5-6ab.16-17 |  | Luk 1:5-25 |
| 2026-12-20 | Minggu | Ungu | Masa Adven IV |  |  | 2Sam 7:1-5.8b-12.14a.16 | Mzm 89:2-3.4-5.27.29 | Rom 16:25-27 | Luk 1:26-38 |
| 2026-12-21 | Senin | Ungu | Masa Adven | PF | PF S. Petrus Kanisius, Imam dan Pujangga gereja | Kid 2:8-14 | Mzm 33:2-3.11-12.20-21 |  | Luk 1:39-45 |
| 2026-12-22 | Selasa | Ungu | Masa Adven |  |  | 1Sam 1:24-28 | 1Sam 2:1.4-5.6-7.8abcd |  | Luk 1:46-56 |
| 2026-12-23 | Rabu | Ungu | Masa Adven | PF | PF S. Yohanes dari Kety, Imam | Mal 3:1-4;4:5-6 | Mzm 25:4bc-5ab.8-9.10.14 |  | Luk 1:57-66 |
| 2026-12-24 | Kamis | Ungu | Masa Adven | HR |  | 2Sam 7:1-5.8b-12.16 | Mzm 89:2-3.4-5.27.29 |  | Luk 1:67-79 |
| 2026-12-25 | Jumat | Putih | Masa Natal | HR |  | Yes 52:7-10 | Mzm 98:1.2-3ab.3cd-4.5-6 | Ibr 1:1-6 | Yoh 1:1-18 |
| 2026-12-26 | Sabtu | Merah | Masa Natal | Pesta |  | Kis 6:8-10;7:54-59 | Mzm 31:3cd-4.6.8ab.16bc.17 |  | Mat 10:17-22 |
| 2026-12-27 | Minggu | Putih | Masa Natal | Pesta |  | Kej 15:1-6;21:1-3 | Mzm 105:1b-2.3-4.5-6.8-9 | Ibr 11:8.11-12.17-19 | Luk 2:22-40 |
| 2026-12-28 | Senin | Merah | Masa Natal | Pesta |  | 1Yoh 1:5-2:2 | Mzm 124:2-3.4-5.7b-8 |  | Mat 2:13-18 |
| 2026-12-29 | Selasa | Putih | Masa Natal | PF | PF S. Tomas Becket, Uskup dan Martir | 1Yoh 2:3-11 | Mzm 96:1-2a.2b-3.5b-6 |  | Luk 2:22-35 |
| 2026-12-30 | Rabu | Putih | Masa Natal |  |  | 1Yoh 2:12-17 | Mzm 96:7-8a.8b-9.10 |  | Luk 2:36-40 |
| 2026-12-31 | Kamis | Putih | Masa Natal | PF | PF S. Silvester I, Paus | 1Yoh 2:18-21 | Mzm 96:1-2.11-12.13 |  | Yoh 1:1-18 |

## 23. App Data Now Pure eKatolik (Live Update)

The mixed-up KatolikDigital data is now superseded by **pure eKatolik**, decrypted
from `eKatolikv14.realm` (the offline eKatolik app DB, AES-256; key in `realm_key.json`).

Applied 2026-08-27 to the phone at `/storage/emulated/0/katolik-digital-offline/`:

- `index.html` -> JS object `KL_FT` (365 days): `warna, nama, bacaan1, bacaan2, mazmur, injil`
  rewritten from eKatolik; `af` (opening prayer) preserved (not in eKatolik Realm).
  Mix-up fixed, e.g. 01-02 was `nama:"Masa Natal" / b1:"1Yoh 1:1-4"` -> now
  `nama:"PW S. Basilius Agung & S. Gregorius…" / b1:"1Yoh 2:22-28"`.
- `renungan_2026.json` (365 days): reading **texts** `b1/b2/ij/mz` overwritten with
  pure eKatolik (match 365/365); `af/dg/rn` (prayers/reflection) preserved — no eKatolik source.

Backups kept on device: `index.html.bak.ekatolik-20260827_224043`,
`renungan_2026.json.bak.ekatolik-20260827_224015`.

## 24. How to Re-verify / Re-run

1. Decrypt + dump: `node /root/eling/ekatolik_src/realm_read/read.js`
   (writes `eKatolikv14_dump.json`; needs `realm@20.2.0` + `realm_key.json`).
2. Rebuild app data: take `KalenderLiturgi` rows (`hapus:False`), regenerate `KL_FT`
   and `renungan_2026.json` reading texts from the JSON.
3. Source of truth: `kalender_liturgi_ekatolik_2026.json` (365 days, full `teks_bacaan_*`).
4. Verify: parse `KL_FT` + `renungan_2026.json` in the live `index.html`; every
   `2026-` date must appear once and `b1` must equal eKatolik `teks_bacaan_pertama`.

Limitation: eKatolik's offline Realm has no per-day prayers/reflections
(tables: Artikel, DataFirman, Firman, KalenderLiturgi, KumpulanDoa, TerjemahanAlkitab),
so `af/dg/rn` cannot be made "pure eKatolik" without a separate prayers source.

## 25. Saint-bio contamination removed from `af` (2026-08-28)

8 misplaced `Pengantar` saint-bio blocks were removed from `KL_FT.af` (per-day opening prayer) on the phone file:

- `01-01` carried the **Basilius & Gregorius** bio (belongs 01-02)
- `03-18` carried the **St. Joseph** bio (belongs 03-19)
- `05-25` carried the **Philip Neri** bio (belongs 05-26)
- `06-02` carried the **Charles Lwanga** bio (belongs 06-03)
- `03-14`, `03-28` (wrong-Sunday reflections), `05-02`, `08-15` (mismatched reflections)

Why remove, not replace: eKatolik's offline Realm has **no `af`/saint-bio data** — `KumpulanDoa` = 160 general prayers; `KalenderLiturgi` has only `peringatan` + `keterangan`. No pure-eKatolik source to swap in, so the contamination was stripped (valid prayer text kept).

Backup on device: `index.html.bak.af-fix-20260828_083334`.

## 26. Full reading texts + Bait Pengantar Injil added to KL_FT (2026-08-28)

Added to `KL_FT` (365 days) from pure eKatolik:

- `b1` Bacaan I: 365/365
- `b2` Bacaan II: 71/365 (Sundays/solemnities only; empty otherwise — correct)
- `mz` Mazmur Tanggapan: 365/365
- `al` Bait Pengantar Injil (= eKatolik `teks_pengantar_injil`, i.e. `alleluia`): 364/365
- `ij` Injil: 365/365

`04-04` (Holy Saturday / Easter Vigil) has empty `al` — eKatolik legitimately has no acclamation for the Vigil (it uses the Exsultet). Empty is correct.

## 27. Kalender Liturgi tab now renders Bait Pengantar Injil + Bacaan II (2026-08-28)

Symptom: `Bait Pengantar Injil` missing in the Kalender Liturgi tab even though `KL_FT.al` was populated.

Root cause: the tab renderer `klRenderFt()` section list was `[af, dg, b1, mz, ij, rn]` — it never read `ft.al` (Bait Pengantar Injil) or `ft.b2` (Bacaan II), so they were dropped at render time. The data was correct; only the display list omitted them.

Fix: added `b2` (Bacaan II) and `al` (Bait Pengantar Injil) to the renderer section array, in liturgical order: `af, dg, b1, b2, mz, al, ij, rn`.

Verified: write persisted byte-identical (52,197,803 bytes). Simulate-render confirms `al` shows for 01-01, 01-04, 04-05, 06-29, 12-25, 01-02; `b2` on Sundays/solemnities; `04-04` correctly has no `al`.

Backup on device: `index.html.bak.render-al-20260828_111000`. To see it: reload the app / clear its WebView cache.

## 28. Current verified state (2026-08-28)

- `index.html` -> `KL_FT`: 365 entries. 6 ref fields (warna, nama, bacaan1/2, mazmur, injil) 365/365 pure eKatolik. Reading texts b1/b2/mz/al/ij populated from pure eKatolik (`al` empty only on 04-04). `af` saint-bio contamination removed (8 dates).
- `renungan_2026.json`: reading texts b1/b2/ij/mz pure eKatolik (365/365); `af/dg/rn` preserved (no eKatolik source).
- All decrypted from `eKatolikv14.realm` (AES-256; key `realm_key.json`). Source of truth: `kalender_liturgi_ekatolik_2026.json` (365 days, full `teks_bacaan_*`).
- Open task: if the installed app loads `index.html` from inside its APK (not the sdcard file), repackage to apply the changes; otherwise reload / clear cache.
