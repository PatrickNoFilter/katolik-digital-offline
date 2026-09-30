#!/bin/bash
# scrape_renungan.sh — Fetch all 2026 renungan data from renunganpagi.id Atom API
# Output: renungan_2026.json
set -e
OUTDIR="/storage/emulated/0/katolik-digital-offline/renungan_raw"
mkdir -p "$OUTDIR"
echo "=== Fetching renungan data from renunganpagi.id ==="
# Fetch in batches of 50 (Atom API max-results)
for START in $(seq 1 50 1000); do
  URL="https://www.renunganpagi.id/feeds/posts/default?alt=json&max-results=50&start-index=$START"
  echo "Fetching start-index=$START..."
  curl -s "$URL" > "$OUTDIR/page_${START}.json"
  # Check if we got entries
  COUNT=$(python3 -c "
import json, sys
try:
    d=json.load(open('$OUTDIR/page_${START}.json'))
    entries=d.get('feed',{}).get('entry',[])
    print(len(entries))
except:
    print(0)
" 2>/dev/null || echo "0")
  echo "  Got $COUNT entries"
  if [ "$COUNT" = "0" ]; then
    echo "  No more entries, stopping."
    rm -f "$OUTDIR/page_${START}.json"
    break
  fi
  sleep 0.5
done
echo ""
echo "=== Parsing and cleaning... ==="
python3 << 'PYEOF'
import json, re, os, html as htmlmod
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_html(html_str):
    if not html_str: return ""
    s = MLStripper()
    try:
        s.feed(html_str)
    except:
        return html_str
    text = s.get_data()
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return htmlmod.unescape(text).strip()

def extract_date(published_str):
    """Extract YYYY-MM-DD from published date string"""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', published_str or '')
    return m.group(1) if m else None

def extract_sections(clean_text):
    """Parse cleaned text into liturgical sections"""
    sections = {}
    text = clean_text
    # Try to split by known headers
    # Antifon
    m = re.search(r'Antifon Pembuka.*?\n(.*?)(?=Doa Pagi|Bacaan|Mazmur|Injil|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['af'] = m.group(1).strip()
    # Doa
    m = re.search(r'Doa Pagi.*?\n(.*?)(?=Bacaan|Mazmur|Injil|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['dg'] = m.group(1).strip()
    # Bacaan I
    m = re.search(r'Bacaan dari.*?\n(.*?)(?=Mazmur|Bait Pengantar|Injil|Verbum|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['b1'] = m.group(1).strip()
    # Mazmur
    m = re.search(r'Mazmur Tanggapan.*?\n(.*?)(?=Bait Pengantar|Injil|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['mz'] = m.group(1).strip()
    # Injil
    m = re.search(r'Injil.*?menurut.*?\n(.*?)(?=Verbum Domini|Renungan|Baca renungan|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['ij'] = m.group(1).strip()
    # Renungan
    m = re.search(r'Renungan.*?\n(.*?)(?=Baca renungan|Orang Kudus|Doa Malam|Antifon Komuni|RENUNGAN PAGI|$)', text, re.DOTALL|re.IGNORECASE)
    if m: sections['rn'] = m.group(1).strip()
    return sections

# Load all pages
outdir = "/storage/emulated/0/katolik-digital-offline/renungan_raw"
all_entries = []
for fname in sorted(os.listdir(outdir)):
    if not fname.endswith('.json'): continue
    try:
        with open(os.path.join(outdir, fname)) as f:
            data = json.load(f)
        entries = data.get('feed', {}).get('entry', [])
        all_entries.extend(entries)
    except Exception as e:
        print(f"  Error loading {fname}: {e}")

print(f"Total raw entries: {len(all_entries)}")

# Filter to 2026 and parse
result = {}
skipped = 0
for entry in all_entries:
    pub = entry.get('published', {}).get('$t', '')
    date = extract_date(pub)
    if not date or not date.startswith('2026'):
        skipped += 1
        continue
    content = entry.get('content', {}).get('$t', '')
    clean = strip_html(content)
    if not clean or len(clean) < 50:
        skipped += 1
        continue
    sections = extract_sections(clean)
    # Only keep if we have at least one section
    if sections:
        if date in result:
            # Keep the one with more content
            existing_len = sum(len(v) for v in result[date].values())
            new_len = sum(len(v) for v in sections.values())
            if new_len > existing_len:
                result[date] = sections
        else:
            result[date] = sections

print(f"Dates with data: {len(result)}")
print(f"Skipped (non-2026/empty): {skipped}")

# Save
outpath = "/storage/emulated/0/katolik-digital-offline/renungan_2026.json"
with open(outpath, 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=None)
print(f"Saved to {outpath}")
print(f"File size: {os.path.getsize(outpath)} bytes")
PYEOF
echo ""
echo "=== Done ==="
