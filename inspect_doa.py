#!/usr/bin/env python3
import re, os, sys

base = '/storage/emulated/0/katolik-digital-offline'
for fn in ['index.html', 'doa.html']:
    p = os.path.join(base, fn)
    data = open(p, encoding='utf-8', errors='replace').read()
    print(f"### {fn}: len={len(data)}")
    for term in ['Penyerahan', 'Keluarga Kudus', 'Keluarga', 'Holy Family']:
        hits = [m.start() for m in re.finditer(re.escape(term), data)]
        print(f"  term '{term}': {len(hits)} hit(s)")
        for h in hits[:3]:
            print("    ...", repr(data[max(0,h-70):h+100]))
    # find DOA array start
    m = re.search(r'(const|let|var)\s+DOA\s*=\s*\[', data)
    if m:
        print("  DOA array starts @", m.start(), repr(data[m.start():m.start()+60]))
    m2 = re.search(r'doa-stats', data)
    if m2:
        print("  doa-stats @", m2.start())
