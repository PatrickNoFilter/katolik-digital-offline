# Katolik Digital Offline — index.html Code Map

**App version:** v4.6.1 (versionCode 47) — 2026-11-21
**File:** `index.html` — 5,925 lines, 75,144,487 bytes, md5 `14562b812977c8578d9419efb4674922`
**Package:** `id.katolikdigital.offline` · **Build:** manual aapt2 on the phone (proot Ubuntu) · **Repo:** `PatrickNoFilter/katolik-digital-offline` (private) · **Releases:** APKs v3.6+ live on GitHub Releases only, not as repo blobs (`apk/` in the repo ends at v3.5)

Single-file WebView app. All navigation goes through `showTab(w, silent)` under three pillars (Kitab Suci / Tradisi Suci / Magisterium) reached from a slide-in drawer (`#side-panel`, ☰ `#menu-btn`).

> Personal use only — the bundled Indonesian Magisterium/TB texts and hymn lyrics are verbatim copyrighted works. No redistribution, no Play Store.

---

## 🆕 What's new (v4.4 – v4.6.1)

| Version | Change |
|---------|--------|
| v4.4 | Kalender Liturgi 2027 (365 days, eKatolik) + gcatholic cross-check fixes; BVM "Santa Perawan Maria" as fakultatif alternative on 24 Ordinary-Time Saturdays; S. John Henry Newman (9 Oct) |
| v4.5 | KL navigation: ‹ Sebelumnya / Berikutnya › month bar at the bottom of the monthly sub-tab; daily prev/next now crosses into the neighbouring month (`klShiftMonth`) |
| v4.6 | Multi-word search (AND) in every search function — all words must match, any field, any order; single-word queries unchanged |
| v4.6.1 | Label "Menu" under the ☰ menu button (42×42 → 42×48, icon 22px, label 10px bold) |

Madah Bakti & Kidung Adi tabs are **postponed** (contents incomplete) — work preserved in `index.html.bak-mbka-klnav-20261115`, `patch_mbka.py`, `tools/mb_lyrics_lagumisa.json`. Indonesian **Barukh still missing** (no TB source found).

---

## 📐 File Structure Overview

| Section | Lines | Description |
|---------|-------|-------------|
| HTML head/meta | 1–7 | Title, viewport, description |
| CSS styles (main) | 8–399 | All inline styles for tabs, layout, components, drawer, KL month bars |
| Header + menu button | 400–444 | `#menu-btn` (☰ + "Menu", line 404), pillar buttons, search wraps |
| Side panel (drawer) | 445–462 | `<aside id="side-panel">`, drawer items |
| **Script Block 1** | 463–487 | Drawer: `openDrawer` (464), `closeDrawer` (465), `toggleDrawer` (466); `syncHeaderPad` (473) |
| Subnav buttons | 488–505 | Kitab Suci / Tradisi Suci / Magisterium sub-tabs |
| Tab views (HTML) | 508–1503 | All view containers and their inner HTML |
| CSS styles (Rosario) | 805–925 | Second inline `<style>` for the Rosario view |
| **Script Block 2** | 1128–1377 | Rosario logic (`rosFs`, `rosBuildSteps`, `rosRender`) |
| Stats divs | 1491–1499 | `<div id="xxx-stats">` for each tab |
| External Bible data | 1504 | `<script src="alkitab_data.js">` (1,320 lines) |
| **Script Block 3** | 1505–1507 | `AL_DATA_JW` (1506), `AL_DATA_EN` (1509), `AL_BOOKS_EN` (1510) |
| **Script Block 4** | 1508–1512 | Small init block |
| **Script Block 5** | 1513–5923 | Main app: Magisterium, tab system, all tab logic + data, Alkitab, init (`showTab('kl', true)` at 5921) |

---

## 🧭 Navigation

### Pillars (lines 408–410)

| Line | Button ID | Label | Call |
|------|-----------|-------|------|
| 408 | `#tab-ks` | 📖 Kitab Suci | `showKS()` (1653) |
| 409 | `#tab-tradisi` | 🕊️ Tradisi Suci | `showTradisi()` (1659) — default pillar |
| 410 | `#tab-mag` | ⛪ Magisterium | `showMag()` (1665) |

### Subnav tabs (lines 490–505)

| Line | Button ID | Label | Call |
|------|-----------|-------|------|
| 490 | `#tab-al` | 📖 Alkitab | `showTab('al')` |
| 491 | `#tab-mz` | 🎵 Mazmur & BPI | `showTab('mz')` |
| 494 | `#tab-ps` | 📖 Puji Syukur | `showTab('ps')` |
| 495 | `#tab-greg` | 🎼 Gregorian | `showTab('greg')` |
| 496 | `#tab-lain` | 📚 Sumber Lain | `showTab('lain')` |
| 497 | `#tab-doa` | 🙏 Doa | `showTab('doa')` |
| 498 | `#tab-rosario` | 📿 Rosario | `showTab('rosario')` |
| 499 | `#tab-kl` | 🗓 Kalender Liturgi | `showTab('kl')` **(default ON)** |
| 502 | `#tab-tpe` | 📕 TPE | `showTab('tpe')` |
| 503 | `#tab-kgk` | 📖 KGK | `magOpen('kgk')` |
| 504 | `#tab-khk` | ⚖️ KHK | `magOpen('khk')` |
| 505 | `#tab-pumr` | 📜 PUMR | `magOpen('pumr')` |

`showTab` (1671) maps tabs to views/subnavs via `KS_TABS`, `TRADISI_TABS`, `MAG_TABS`, `LAGU_TABS` and the `ks-` / `tradisi-` / `mag-` / `lagu-subnav` containers. Drawer items mirror the same tabs and call `showTab(...); closeDrawer()`.

---

## 📖 Tab View Containers (HTML)

| Line | View | Description |
|------|------|-------------|
| 508 | `<div id="view-ps">` | Puji Syukur — `#list-wrap` (511), `#d-content` (538) |
| 548 | `<div id="view-mz">` | Mazmur & BPI — `#mz-list-wrap` (552), `#mz-d-content` (577) |
| 587 | `<div id="view-doa">` | Doa — `#doa-list-wrap` (611) |
| 641 | `<div id="view-tpe">` | TPE — `#tpe-list-wrap` (653) |
| 690 | `<div id="view-mag">` | Magisterium — `#mag-list-wrap` (693), `#mag-d-content` (713) |
| 721 | `<div id="view-greg">` | Gregorian — `#greg-list-wrap` (725) |
| 762 | `<div id="view-lain">` | Sumber Lain — `#lain-list-wrap` (766) |
| 804 | `<div id="view-rosario">` | Rosario — `#ros-ref` (966), `#ros-events-content` (1105) |
| 1380 | `<div id="view-kl">` | Kalender Liturgi (**DEFAULT TAB**) — `#kl-list-wrap` (1388), top month bar (1389), bottom month bar (1401, v4.5), `#kl-d-content` (1420) |
| 1428 | `<div id="view-al">` | Alkitab — `#al-list-wrap` (1459), `#al-d-content` (1480) |

---

## 📊 Stats Containers

| Line | ID | Tab |
|------|----|-----|
| 1491 | `#stats` | Puji Syukur |
| 1492 | `#mz-stats` | Mazmur & BPI |
| 1493 | `#doa-stats` | Doa |
| 1494 | `#tpe-stats` | TPE |
| 1495 | `#greg-stats` | Gregorian |
| 1496 | `#lain-stats` | Sumber Lain |
| 1497 | `#kl-stats` | Kalender Liturgi |
| 1498 | `#al-stats` | Alkitab |
| 1499 | `#mag-stats` | Magisterium |

---

## ⚙️ JavaScript Functions — Key Locations

### Drawer & tab system (Blocks 1 & 5)

| Line | Function | Description |
|------|----------|-------------|
| 464 | `openDrawer()` | Opens the slide-in drawer |
| 465 | `closeDrawer()` | Closes the drawer |
| 466 | `toggleDrawer()` | Toggles drawer (menu button) |
| 473 | `syncHeaderPad()` | Re-measures header height (folded banner) |
| 1653 | `showKS()` | Shows Kitab Suci pillar |
| 1659 | `showTradisi()` | Shows Tradisi Suci pillar |
| 1665 | `showMag()` | Shows Magisterium pillar |
| 1671 | `showTab(w, silent)` | **Master tab switcher** — hides all views, shows selected |

### ⛪ Magisterium

| Line | Function | Description |
|------|----------|-------------|
| 1516 | `MAGDOCS` | Magisterium documents data (KGK / KHK / PUMR) |
| 1521 | `magOpen(doc, silent)` | Opens a Magisterium document |
| 1558 | `magFiltered()` | Returns filtered Magisterium entries (multi-word AND, v4.6) |
| 1576 | `magRenderList()` | Renders Magisterium list |
| 1589 | `magOpenDetail(id, silent)` | Opens a Magisterium entry detail |

### 📖 Puji Syukur

| Line | Function | Description |
|------|----------|-------------|
| 1725 | `SONGS` | Puji Syukur song data |
| 1741 | `chordHtml(text)` | Renders chord notation HTML |
| 1749 | `buildChips()` | Builds filter chips (category buttons) |
| 1767 | `filtered()` | Returns filtered song list (multi-word AND, v4.6) |
| 1779 | `renderList()` | Renders song list in DOM |
| 1800 | `openSong(s, silent)` | Opens a song detail view |
| 1844 | `renderContent()` | Renders song content (text/chord modes) |
| 1863 | `setMode(m)` | Switches text/chord mode |
| 1864 | `scrollToSheet()` | Scrolls to sheet music image |
| 1866 | `toggleFav()` | Toggles favorite status |
| 1874 | `showList(silent)` | Shows song list view |
| 1883 | `openLB(src, silent)` | Opens lightbox for images |
| 1888 | `closeLB(silent)` | Closes lightbox |
| 1949 | `recordSearch()` | Search history (replaces category chips) |

### 🎵 Mazmur

| Line | Function | Description |
|------|----------|-------------|
| 1967 | `MZ` | Mazmur data |
| 2006 | `mzFiltered()` | Returns filtered Mazmur list (multi-word AND, v4.6) |

### 🙏 Doa

| Line | Function | Description |
|------|----------|-------------|
| 2155 | `DOA` | Doa data |
| 2235 | `doaFiltered()` | Returns filtered Doa list (multi-word AND, v4.6) |

### 🎼 Gregorian / TPE / Sumber Lain (shared xtra engine)

| Line | Function | Description |
|------|----------|-------------|
| 2339 | `XTRA_KEYS` | `['tpe', 'greg', 'lain']` |
| 2340 | `XTRA` | Shared hymnal data |
| 2411 | `xtraFiltered(k)` | Returns filtered list (multi-word AND, v4.6) |

### 📿 Rosario (Block 2, lines 1128–1377)

| Function | Description |
|----------|-------------|
| `rosFs(d)` | Adjusts Rosario font size |
| `rosBuildSteps(type)` | Builds prayer steps for a mystery |
| `rosRender()` | Renders Rosario interface |

### 🗓 Kalender Liturgi

| Line | Function / Variable | Description |
|------|---------------------|-------------|
| 2521 | `KL` | Liturgical metadata per ISO date: `{w,s,k,t,b,a}` |
| 3253–3255 | `KL_MONTHS`, `KL_DAYNAMES`, `KL_SEASONS` | Month/day/season labels |
| 3324 | `KL_FT_SECTIONS` | Full-text section order |
| 3371 | `klIsTextSearch(q)` | Date detection (not multi-word) |
| 3396 | `klSearchAll(q)` | Text search across all KL days (already multi-term) |
| 3429 | `klFiltered()` | Month-mode filter (multi-word AND, v4.6) |
| 3454 | `klRenderList()` | Renders month list; syncs both month-bar labels |
| 3609 | `klOpen(day)` | Opens a day; syncs `klCur` to that month (v4.5) |
| 3676 | `klMonth(delta)` | Month jump (top bar) |
| 3684 | `klGoToday()` | Jumps to today |
| 3715 | `klShiftMonth(delta)` | Cross-month step, skips empty months, stops at Jan 2026 / Dec 2027 (v4.5) |
| 3724 | `klPrev()` | Previous day (crosses months, v4.5) |
| 3736 | `klNext()` | Next day (crosses months, v4.5) |
| 3515 | `KL_FT` | Full text; lookup ISO-first, then `MM-DD` fallback |
| 3516 | `KL_SS` | Saints by `MM-DD` |

KL coverage: Jan 2026 – Dec 2027 (365 days each year; 2027 from eKatolik, see `kalendar.md` §29). Known 2027 gaps: `af`/`dg` empty all year, `rn` empty all year, BcO missing on 2027-03-28, 2027-05-15, 2027-12-26.

### 📖 Alkitab

| Line | Function / Variable | Description |
|------|---------------------|-------------|
| 1504 | `alkitab_data.js` (1,320 lines) | External English Bible data (`var AL_DATA`, line 1) — AKJV, 66 books, public domain; EN Apocrypha restored (74 books) |
| 3783 | `AL_BOOKS` | Indonesian book list (TB via SABDA, 73 books incl. Deuterocanon; ID Ester) |
| 3863 | `AL_DATA` | Indonesian verse data |
| 5431 | `AL_BOOKS_JW` | Javanese book list |
| 5556–5558 | `AL_HIST_KEY`, `AL_HIST_MAX`, `AL_HIST_T` | Search history (`lm_al_hist`, max 8 per language) |
| 5714 | `alSearchAll(q)` | Book-name matching (multi-word AND, v4.6); verse search was already multi-term |

Indonesian **Barukh still missing** (no TB source found).

---

## 🔄 Initialization Flow

1. Block 5 loads; `showTab('kl', true)` at line 5921 — opens Kalender Liturgi by default
2. State restore at ~1896–1902: restores last tab from `history.state` / localStorage if available
3. Back-button bridge: `KlBridge` — a **named static nested class** in `MainActivity.java` (d8 NPE-crashes on anonymous inner classes, so never use one for a `@JavascriptInterface` bridge)
4. Font locked: `setTextZoom(100)`

---

## 🎯 Quick Reference — Where to Edit

| To modify... | Edit lines |
|---|---|
| Styles/CSS (main) | 8–399 |
| Menu button + "Menu" label | 360–368 (CSS), 404 (markup) |
| Drawer / side panel | 445–462 (markup), 463–487 (JS) |
| Pillar & subnav buttons | 408–410, 490–505 |
| Tab view HTML structure | 508–1503 |
| Rosario data + logic | 804–1377 |
| Magisterium data/logic | 1516–1650 |
| Puji Syukur data (`SONGS`) + logic | 1725–1966 |
| Mazmur data/logic | 1967–2154 |
| Doa data/logic | 2155–2338 |
| Gregorian/TPE/Lain data/logic | 2339–2520 |
| Liturgical calendar data (`KL`, `KL_FT`, `KL_SS`) | 2521–3516 |
| KL logic (nav, search, render) | 3253–3782 |
| Alkitab data/logic | 3783–5923 |
| Tab switching logic | 1653–1724 |
| Init / default tab | 5921 |

---

## 🔨 Build & Release

- Build on the phone: `proot-distro login ubuntu -- bash /storage/emulated/0/katolik-digital-offline/apk/scripts/01_build_apk.sh` (aapt2 under qemu; SDK + `keystore.jks` live on `/storage`, not in the container)
- Version bumps touch **both** `apk/app/AndroidManifest.xml` and `apk/scripts/01_build_apk.sh` (flags + every APK output name); back up both first
- Versioning: features → MINOR, bugfixes → PATCH; signing cert SHA-256 `5d8fbd75…13e7` (constant across versions)
- GitHub: commit `index.html` only (helpers, backups, tools stay untracked); Release per version with the APK uploaded from the phone
- The phone's Termux node (`100.121.236.71`) is dead — use the Tailscale app node (`100.76.64.89`); Termux `sshd` must be started by hand
