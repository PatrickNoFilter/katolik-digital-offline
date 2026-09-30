#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validator untuk tab Kalender Liturgi di index.html (rencana §5 Tahap C).

Memeriksa:
  1. Data KL (365 hari, semua field wajib).
  2. Struktur HTML (tab-kl, view-kl, kl-q-wrap, kl-stats, div seimbang).
  3. Integrasi showTab + Android back (popstate) + inisialisasi klInit.
  4. Sintaks JS seluruh aplikasi (via node --check bila tersedia).
  5. Konsistensi data: warna/musim pada tanggal-tanggal kunci.

Cara pakai:  python3 validate_kalender.py
"""
import json, re, subprocess, sys, os, shutil

INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')

NODE_PARSE = r"""
const fs = require("fs");
const s = fs.readFileSync(process.argv[1], "utf8");
const i = s.indexOf("const KL = {");
if (i < 0) process.exit(3);
const j = s.indexOf("\n};", i) + 3;
const body = s.slice(i + 11, j);
const KL = eval("(" + body.replace(/;$/, "") + ")");
console.log(JSON.stringify({n: Object.keys(KL).length, fields: Object.values(KL).every(e => "w" in e && "s" in e && "k" in e && "t" in e && "b" in e && "a" in e)}));
"""

def main():
    data = open(INDEX, encoding='utf-8').read()
    failures = []

    def check(cond, msg):
        if cond:
            print('  PASS:', msg)
        else:
            failures.append(msg)
            print('  FAIL:', msg)

    # ---------- 1. Data KL ----------
    m = re.search(r'(const KL = \{\n.*?\n\};)', data, re.S)
    check(m is not None, 'const KL block present')
    if not m:
        print('\n❌ Gagal: blok const KL tidak ditemukan.')
        sys.exit(1)
    kl_js = m.group(1)
    try:
        r = subprocess.run(['node', '--check', '-'], input=kl_js, capture_output=True, text=True, timeout=60)
        check(r.returncode == 0, 'sintaks data KL valid (node --check)')
        if r.returncode != 0:
            print('    stderr:', r.stderr.strip()[:400])
    except Exception as e:
        check(False, f'tidak dapat menjalankan node: {e}')

    if shutil.which('node'):
        try:
            r = subprocess.run(['node', '-e', NODE_PARSE, INDEX], capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                out = json.loads(r.stdout.strip())
                check(out['n'] == 365, f'data KL berisi 365 hari (got {out["n"]})')
                check(out['fields'], 'semua entri punya field w/s/k/t/b/a')
            else:
                check(False, 'node parsing data KL gagal: ' + r.stderr.strip()[:300])
        except Exception as e:
            check(False, f'node parsing data KL gagal: {e}')

    # ---------- 2. Struktur HTML ----------
    check('id="tab-kl"' in data, 'tombol tab-kl ada')
    check('id="view-kl"' in data, 'view-kl ada')
    check('id="kl-q-wrap"' in data, 'search wrap kl-q-wrap ada')
    check('id="kl-stats"' in data, 'footer kl-stats ada')
    check(data.count('id="kl-chips"') == 1, 'kl-chips unik')
    check(data.count('id="kl-musim-chips"') == 1, 'kl-musim-chips unik')
    check(data.count('id="kl-songlist"') == 1, 'kl-songlist unik')
    check(data.count('id="kl-detail"') == 1, 'kl-detail unik')
    check(data.count('id="kl-d-title"') == 1, 'kl-d-title unik')
    check(data.count('id="kl-d-content"') == 1, 'kl-d-content unik')
    div_open = len(re.findall(r'<div\b', data))
    div_close = len(re.findall(r'</div>', data))
    check(div_open == div_close, f'div seimbang ({div_open} vs {div_close})')
    check(len(re.findall(r'<main\b', data)) == len(re.findall(r'</main>', data)), 'main seimbang')
    check(len(re.findall(r'<nav\b', data)) == len(re.findall(r'</nav>', data)), 'nav seimbang')
    check(len(re.findall(r'<button\b', data)) == len(re.findall(r'</button>', data)), 'button seimbang')
    check(data.count('<script>') == data.count('</script>'), 'script seimbang')

    # ---------- 3. Integrasi ----------
    check("kl:'view-kl'" in data, 'showTab vmap memuat kl')
    check("kl:'tab-kl'" in data, 'showTab bmap memuat kl')
    check("kl:'kl-q-wrap'" in data, 'showTab qmap memuat kl')
    check("'kl'" in data.split('function showTab')[1][:300], 'tabs array memuat kl')
    check('klShowList(true)' in data, 'popstate menangani restore list kl')
    check("st.tab === 'kl'" in data, 'popstate song memuat cabang kl')
    check('klOpen(st.id, true)' in data, 'popstate song memanggil klOpen')
    check("kl$('kl-q').addEventListener('input'" in data, 'search input terhubung ke render')
    check('klBuildChips();\n  klRenderList();' in data, 'klInit membangun chip & render')
    check('kl-stats' in data and '100% offline' in data, 'statistik footer offline kl ada')

    # ---------- 4. Sintaks JS total via node --check ----------
    m_script = re.search(r'<script>(.*)</script>', data, re.S)
    if m_script and shutil.which('node'):
        jsfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tmp_kl_full_script.js')
        with open(jsfile, 'w', encoding='utf-8') as f:
            f.write(m_script.group(1))
        try:
            r = subprocess.run(['node', '--check', jsfile], capture_output=True, text=True, timeout=120)
            check(r.returncode == 0, 'sintaks JS seluruh aplikasi valid (node --check)')
            if r.returncode != 0:
                print('    stderr:', r.stderr.strip()[:500])
        except Exception as e:
            check(False, f'node --check gagal: {e}')
        finally:
            try:
                os.remove(jsfile)
            except OSError:
                pass
    elif not m_script:
        check(False, 'script tidak ditemukan')

    # ---------- 5. Warna/musim tanggal kunci ----------
    def color(iso):
        mm = re.search(r'"%s":\{w:"([^"]+)"' % iso, data)
        return mm.group(1) if mm else None

    def season(iso):
        mm = re.search(r'"%s":\{w:"[^"]+",s:"([^"]+)"' % iso, data)
        return mm.group(1) if mm else None

    expected = {
        '2026-01-01': ('putih', 'Natal'),
        '2026-02-18': ('ungu', 'Prapaskah'),
        '2026-03-15': ('rose', 'Prapaskah'),
        '2026-03-29': ('merah', 'Trihari Paskah'),
        '2026-04-03': ('merah', 'Trihari Paskah'),
        '2026-04-05': ('putih', 'Paskah'),
        '2026-05-24': ('merah', 'Paskah'),
        '2026-11-01': ('putih', 'Masa Biasa'),
        '2026-11-02': ('hitam', 'Masa Biasa'),
        '2026-11-29': ('ungu', 'Adven'),
        '2026-12-13': ('rose', 'Adven'),
        '2026-12-25': ('putih', 'Natal'),
    }
    ok = 0
    for iso, (c, s) in expected.items():
        gc, gs = color(iso), season(iso)
        if gc == c and gs == s:
            ok += 1
        else:
            print(f'    warna/musim {iso}: dapat {gc}/{gs}, harap {c}/{s}')
    check(ok == len(expected), f'warna/musim tanggal kunci benar ({ok}/{len(expected)})')

    print('\n' + ('✅ SEMUA CEK (validate_kalender) LULUS' if not failures else f'❌ {len(failures)} GAGAL:\n- ' + '\n- '.join(failures)))
    sys.exit(0 if not failures else 1)


if __name__ == '__main__':
    main()
