# Katolik Digital Offline — index.html Code Map

**File:** `index.html`
**Total lines:** ~4700+

---

## 📐 File Structure Overview

| Section | Lines | Description |
|---------|-------|-------------|
| HTML head/meta | 1–20 | Title, viewport, description, styles |
| CSS styles | 21–289 | All inline styles for tabs, layout, components |
| Navigation bar | 290–300 | 9 tab buttons with `onclick="showTab(...)"` |
| Tab views (HTML) | 301–1230 | All view containers and their inner HTML |
| Rosario data | 569–1142 | Full Rosario prayer data (JSON-like object) |
| Stats divs | 1223–1230 | `<div id="xxx-stats">` for each tab |
| **Script Block 1** | 1234–1142 | Rosario inline logic (ROS) |
| **Script Block 2** | 1234–end | All tab logic, data, and initialization |

---

## 🗂 Tab Navigation Buttons

| Line | Button ID | Label | Call |
|------|-----------|-------|------|
| 291 | `#tab-ps` | 📖 Puji Syukur | `showTab('ps')` |
| 292 | `#tab-mz` | 🎵 Mazmur & BPI | `showTab('mz')` |
| 293 | `#tab-doa` | 🙏 Doa | `showTab('doa')` |
| 294 | `#tab-rosario` | 📿 Rosario | `showTab('rosario')` |
| 295 | `#tab-tpe` | 📕 TPE | `showTab('tpe')` |
| 296 | `#tab-greg` | 🎼 Gregorian | `showTab('greg')` |
| 297 | `#tab-lain` | 📚 Sumber Lain | `showTab('lain')` |
| 298 | `#tab-kl` | 🗓 Kalender Liturgi | `showTab('kl')` **(default ON)** |
| 299 | `#tab-al` | 📖 Alkitab | `showTab('al')` |

---

## 📖 Tab View Containers (HTML)

### 📖 Puji Syukur (`view-ps`)
| Line | Element | Description |
|------|---------|-------------|
| 329 | `<div id="view-ps">` | Main container |
| 332 | `<div id="list-wrap">` | Song list wrapper |
| 359 | `<div id="d-content">` | Song detail content |
| 361 | `<div id="d-note">` | Song notes/chords |

### 🎵 Mazmur & BPI (`view-mz`)
| Line | Element | Description |
|------|---------|-------------|
| 369 | `<div id="view-mz">` | Main container |
| 373 | `<div id="mz-list-wrap">` | Song list wrapper |
| 398 | `<div id="mz-d-content">` | Song detail content |
| 400 | `<div id="mz-d-note">` | Song notes/chords |

### 🙏 Doa (`view-doa`)
| Line | Element | Description |
|------|---------|-------------|
| 408 | `<div id="view-doa">` | Main container |
| 412 | `<div id="doa-list-wrap">` | Prayer list wrapper |

### 📕 TPE (`view-tpe`)
| Line | Element | Description |
|------|---------|-------------|
| 441 | `<div id="view-tpe">` | Main container |
| 449 | `<div id="tpe-list-wrap">` | TPE list wrapper |
| 472 | `<div id="tpe-d-content">` | TPE detail content |
| 474 | `<div id="tpe-d-note">` | TPE notes |

### 🎼 Gregorian (`view-greg`)
| Line | Element | Description |
|------|---------|-------------|
| 486 | `<div id="view-greg">` | Main container |
| 490 | `<div id="greg-list-wrap">` | Chant list wrapper |
| 513 | `<div id="greg-d-content">` | Chant detail content |
| 515 | `<div id="greg-d-note">` | Chant notes |

### 📚 Sumber Lain (`view-lain`)
| Line | Element | Description |
|------|---------|-------------|
| 527 | `<div id="view-lain">` | Main container |
| 531 | `<div id="lain-list-wrap">` | Source list wrapper |
| 554 | `<div id="lain-d-content">` | Source detail content |
| 556 | `<div id="lain-d-note">` | Source notes |

### 📿 Rosario (`view-rosario`)
| Line | Element | Description |
|------|---------|-------------|
| 569 | `<div id="view-rosario">` | Main container |
| 731 | `<div id="ros-ref">` | Reference/mystery info panel |
| 870 | `<div id="ros-events-content">` | Events content area |

### 🗓 Kalender Liturgi (`view-kl`)
| Line | Element | Description |
|------|---------|-------------|
| 1145 | `<div id="view-kl">` | Main container (**DEFAULT TAB**) |
| 1149 | `<div id="kl-list-wrap">` | Calendar month grid |
| 1176 | `<div id="kl-d-content">` | Liturgical day detail |

### 📖 Alkitab (`view-al`)
| Line | Element | Description |
|------|---------|-------------|
| 1184 | `<div id="view-al">` | Main container |
| 1192 | `<div id="al-list-wrap">` | Book list / chapter grid |
| 1213 | `<div id="al-d-content">` | Chapter/verse content |
| 1214 | `<div id="al-d-verses">` | Verse display area |

---

## 📊 Stats Containers

| Line | ID | Tab |
|------|----|-----|
| 1223 | `#stats` | Puji Syukur |
| 1224 | `#mz-stats` | Mazmur & BPI |
| 1225 | `#doa-stats` | Doa |
| 1226 | `#tpe-stats` | TPE |
| 1227 | `#greg-stats` | Gregorian |
| 1228 | `#lain-stats` | Sumber Lain |
| 1229 | `#kl-stats` | Kalender Liturgi |
| 1230 | `#al-stats` | Alkitab |

---

## ⚙️ JavaScript Functions — Key Locations

### Global / Tab System
| Line | Function | Description |
|------|----------|-------------|
| 1238 | `showTab(w, silent)` | **Master tab switcher** — hides all views, shows selected |
| 1255 | *(PS section begins)* | Puji Syukur script block starts |

### 📖 Puji Syukur Functions
| Line | Function | Description |
|------|----------|-------------|
| 1273 | `chordHtml(text)` | Renders chord notation HTML |
| 1281 | `buildChips()` | Builds filter chips (category buttons) |
| 1299 | `filtered()` | Returns filtered song list |
| 1313 | `renderList()` | Renders song list in DOM |
| 1334 | `openSong(s, silent)` | Opens a song detail view |
| 1378 | `renderContent()` | Renders song content (text/chord modes) |
| 1397 | `setMode(m)` | Switches text/chord mode |
| 1398 | `scrollToSheet()` | Scrolls to sheet music image |
| 1400 | `toggleFav()` | Toggles favorite status |
| 1408 | `showList(silent)` | Shows song list view |
| 1417 | `openLB(src, silent)` | Opens lightbox for images |
| 1422 | `closeLB(silent)` | Closes lightbox |
| 1483 | `recordSearch()` | Handles search input |

### 🎵 Mazmur Functions
| Line | Function | Description |
|------|----------|-------------|
| 1499 | *(MZ section begins)* | Mazmur script block starts |
| 1515 | `mzDisplayNum(s)` | Formats Mazmur number display |
| 1522 | `mzBuildChips()` | Builds Mazmur filter chips |
| 1540 | `mzFiltered()` | Returns filtered Mazmur list |
| 1554 | `mzRenderList()` | Renders Mazmur list |
| 1575 | `mzLyricText(s)` | Extracts lyric text |
| 1581 | `mzOpenSong(s, silent)` | Opens Mazmur detail |
| 1628 | `mzRenderContent()` | Renders Mazmur content |
| 1636 | `mzSetMode(m)` | Switches text/chord mode |
| 1639 | `mzToggleFav()` | Toggles Mazmur favorite |
| 1647 | `mzShowList(silent)` | Shows Mazmur list |
| 1656 | `mzOpenLB(src, silent)` | Opens Mazmur lightbox |
| 1661 | `mzCloseLB(silent)` | Closes Mazmur lightbox |
| 1675 | `mzrecordSearch()` | Handles Mazmur search |

### 🙏 Doa Functions
| Line | Function | Description |
|------|----------|-------------|
| 1697 | `applyLyricSize()` | Applies font size setting |
| 1700 | `lyricFs(d)` | Adjusts lyric font size |
| 1714 | `doaRenderChips()` | Builds Doa filter chips |
| 1733 | `doaFiltered()` | Returns filtered Doa list |
| 1741 | `doaRenderList()` | Renders Doa list |
| 1754 | `doaOpenDetail(d, silent)` | Opens Doa detail |
| 1766 | `doaShowList(silent)` | Shows Doa list |
| 1773 | `doaPrevPrayer()` | Previous prayer navigation |
| 1778 | `doaNextPrayer()` | Next prayer navigation |
| 1786 | `applyDoaSize()` | Applies Doa font size |
| 1789 | `doaFs(d)` | Adjusts Doa font size |
| 1799 | `doarecordSearch()` | Handles Doa search |

### 📿 Rosario Functions
| Line | Function | Description |
|------|----------|-------------|
| 897 | `rosFs(d)` | Adjusts Rosario font size |
| 983 | `rosBuildSteps(type)` | Builds prayer steps for a mystery |
| 1016 | `rosRender()` | Renders Rosario interface |

### 🎼 Gregorian & TPE Functions
| Line | Function | Description |
|------|----------|-------------|
| 1835 | `xtraSubSel(k, d)` | Sub-category selector (shared) |
| 1841 | `xtraChipLabel(k, c)` | Chip label builder |
| 1846 | `xtraCatMatch(k, d)` | Category matching logic |
| 1854 | `xtraSubTab(sub)` | Sub-tab switcher |
| 1862 | `xtraBuildChips(k)` | Builds chips for extra tabs |
| 1874 | `xtraFiltered(k)` | Returns filtered list |
| 1886 | `xtraRenderList(k)` | Renders list for extra tabs |

---

## 🗓 Kalender Liturgi Data

| Line | Variable | Description |
|------|----------|-------------|
| 2484 | `KL_FT` | **Full liturgical data object** — keys are `MM-DD` format |
| — | Each entry | Contains: `warna`, `nama`, `bacaan1`, `bacaan2`, `mazmur`, `injil`, `af`, `b1`, `b2`, `mz`, `al`, `ij`, `dg`, `rn`, `mz_refren` |

---

## 📖 Alkitab Data

| Line | Variable | Description |
|------|----------|-------------|
| ~3500+ | `ALKITAB_PB` | Perjanjian Baru (New Testament) data |
| ~4000+ | `ALKITAB_PL` | Perjanjian Lama (Old Testament) data |
| — | Structure | `{ book: { name, chapters: { ch: { verses: [...] } } } }` |

---

## 🔄 Initialization Flow

1. **Line ~1430–1470:** DOMContentLoaded handler
2. Default: `showTab('kl', true)` — opens Kalender Liturgi
3. Restores last state from localStorage if available
4. Calls appropriate init functions for active tab

---

## 🎯 Quick Reference — Where to Edit

| To modify... | Edit lines |
|---|---|
| Tab button labels/icons | 291–299 |
| Tab view HTML structure | 329–1230 |
| Song data (PS) | ~1250–1490 |
| Mazmur data | ~1499–1680 |
| Doa data | ~1680–1830 |
| Gregorian/TPE/Lain data | ~1830–2480 |
| Rosario data | 569–1142 |
| Liturgical calendar data | 2484+ |
| Bible data | 3500+ |
| Tab switching logic | 1238–1270 |
| Styles/CSS | 21–289 |
