#!/usr/bin/env python3
"""Install the working nav drawer (drawer aside + backdrop + nav.js)
on all microsite pages that have the topbar but no drawer wiring.

Idempotent: skip pages that already contain `id="navDrawer"`.
"""
import re
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")

# Drawer markup — uses absolute /paths so it works at any directory depth.
DRAWER = """<div class="nav-drawer-backdrop" data-close-drawer aria-hidden="true"></div>
<aside class="nav-drawer" id="navDrawer" aria-hidden="true" aria-label="Site navigation">
  <button class="nav-drawer-close" type="button" data-close-drawer aria-label="Close menu">
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
  </button>
  <form class="nav-drawer-search" action="/articles" method="get" role="search">
    <input type="search" name="q" placeholder="Search The Mutapa Times" aria-label="Search The Mutapa Times">
  </form>
  <nav class="nav-drawer-main" aria-label="Sections">
    <a href="/">News</a>
    <a href="/economy">Economy</a>
    <a href="/fx/">FX</a>
    <a href="/markets">Markets</a>
    <a href="/property">Property</a>
    <a href="/jobs">Jobs</a>
    <a href="/articles">Articles</a>
    <a href="/originals">Originals</a>
  </nav>
  <span class="nav-drawer-section">Directories</span>
  <nav class="nav-drawer-info" aria-label="Directories">
    <a href="/flights/">Flights</a>
    <a href="/schools/">Schools</a>
    <a href="/zse/">ZSE companies</a>
    <a href="/mining/">Mining</a>
    <a href="/moving-to-zimbabwe/">Moving to Zimbabwe</a>
  </nav>
  <span class="nav-drawer-section">Cities</span>
  <nav class="nav-drawer-cities" aria-label="Cities">
    <a href="/harare-news">Harare</a>
    <a href="/bulawayo-news">Bulawayo</a>
    <a href="/mutare-news">Mutare</a>
    <a href="/gweru-news">Gweru</a>
    <a href="/masvingo-news">Masvingo</a>
    <a href="/victoria-falls-news">Victoria Falls</a>
  </nav>
  <span class="nav-drawer-section">Information</span>
  <nav class="nav-drawer-info" aria-label="Information">
    <a href="/about">About</a>
    <a href="/advertising">Advertising</a>
    <a href="/terms">Terms</a>
    <a href="/privacy">Privacy</a>
  </nav>
</aside>
"""

NAV_SCRIPT = '<script defer src="/js/nav.js"></script>'

MARKER_DRAWER = 'id="navDrawer"'
MARKER_SCRIPT = 'js/nav.js'
TOPBAR_CLOSE = '<a href="/subscribe" class="topbar-cta">Subscribe</a>\n</div>'

def gather_targets():
    paths = []
    paths += sorted((ROOT / "flights").rglob("index.html"))
    paths += sorted((ROOT / "fx").rglob("index.html"))   # /fx/<slug>/index.html
    paths += sorted((ROOT / "schools").glob("*.html"))
    paths += sorted((ROOT / "zse").glob("*.html"))
    paths += sorted((ROOT / "mining").glob("*.html"))
    paths += sorted((ROOT / "cooking").rglob("index.html"))  # /cooking/<recipe>/index.html
    paths += sorted((ROOT / "airports").rglob("index.html"))  # /airports/<airport>/index.html
    paths.append(ROOT / "moving-to-zimbabwe" / "sim-card-and-mobile.html")
    # Dedupe while preserving order
    seen = set(); out = []
    for p in paths:
        if p in seen: continue
        seen.add(p); out.append(p)
    return out

inserted_drawer = []
inserted_script = []
skipped = []
errors = []

for path in gather_targets():
    if not path.exists():
        errors.append((path, "missing")); continue
    try:
        h = path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append((path, f"read: {e}")); continue

    changed = False
    # Step 1: inject drawer markup after topbar
    if MARKER_DRAWER not in h:
        if TOPBAR_CLOSE in h:
            h = h.replace(TOPBAR_CLOSE, TOPBAR_CLOSE + "\n" + DRAWER, 1)
            inserted_drawer.append(path)
            changed = True
        else:
            errors.append((path, "topbar close not found")); continue
    # Step 2: inject nav.js script before </body>
    if MARKER_SCRIPT not in h:
        if "</body>" in h:
            h = h.replace("</body>", NAV_SCRIPT + "\n</body>", 1)
            inserted_script.append(path)
            changed = True
        else:
            errors.append((path, "no </body>")); continue
    if not changed:
        skipped.append(path); continue
    path.write_text(h, encoding="utf-8")

print(f"=== Nav drawer install ===")
print(f"Targets checked:        {len(gather_targets())}")
print(f"Drawer markup inserted: {len(inserted_drawer)}")
print(f"nav.js script inserted: {len(inserted_script)}")
print(f"Already wired (skipped): {len(skipped)}")
if errors:
    print(f"Errors: {len(errors)}")
    for p, e in errors[:8]:
        print(f"  ! {p.relative_to(ROOT)}: {e}")
