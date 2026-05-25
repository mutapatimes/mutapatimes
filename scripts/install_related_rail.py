#!/usr/bin/env python3
"""Idempotent installer that drops a 'Read next across the site' rail
into every microsite page just before </main>.

Skips pages that already contain the rail (matched by the data-related-rail
attribute). Picks 4 cards from scripts/lib_related.py.HIGHLIGHTS, excluding
cards from the same microsite the current page is on.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib_related import related_rail_html, MARKER, site_for_path

ROOT = Path(__file__).resolve().parent.parent

def gather_targets():
    paths = []
    paths += sorted((ROOT / "fx").rglob("index.html"))
    paths += sorted((ROOT / "airports").rglob("index.html"))
    paths += sorted((ROOT / "flights").rglob("index.html"))
    paths += sorted((ROOT / "cooking").rglob("index.html"))
    paths += sorted((ROOT / "schools").glob("*.html"))
    paths += sorted((ROOT / "zse").glob("*.html"))
    paths += sorted((ROOT / "mining").glob("*.html"))
    paths += sorted((ROOT / "moving-to-zimbabwe").glob("*.html"))
    seen = set(); out = []
    for p in paths:
        if p in seen: continue
        seen.add(p); out.append(p)
    return out


installed = skipped = errors = 0

for path in gather_targets():
    try:
        h = path.read_text(encoding="utf-8")
    except Exception as e:
        errors += 1
        print(f"  ! {path.relative_to(ROOT)}: {e}")
        continue

    # Idempotency: already wired
    if MARKER in h:
        skipped += 1
        continue

    # Skip pages that don't have </main> (mainly the redirect stubs)
    if "</main>" not in h:
        skipped += 1
        continue

    # Figure out which microsite this page belongs to so we exclude it
    rel = "/" + str(path.relative_to(ROOT)).replace("\\", "/")
    site = site_for_path(rel)

    rail = related_rail_html(exclude_site=site)
    h = h.replace("</main>", rail + "\n</main>", 1)
    path.write_text(h, encoding="utf-8")
    installed += 1


print(f"=== Related rail install ===")
print(f"Installed: {installed}")
print(f"Skipped:   {skipped}")
if errors:
    print(f"Errors:    {errors}")
