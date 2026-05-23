#!/usr/bin/env python3
"""Install the impact.com Universal Tracking Tag (UTT) on revenue pages.

Idempotent: skips any file that already contains the UTT (matched by the
account ID 'P-A7333443'). Inserts the UTT block just before </head>.

Target pages (only those with outbound merchant links):
  - /fx.html             — main FX/send-money calculator
  - /fx/<slug>/index.html — 16 corridor pages (rate + send-money)
  - /moving-to-zimbabwe/*.html — health insurance, banking, schools refs
"""
import re
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")

UTT_BLOCK = """<!-- impact.com Universal Tracking Tag (UTT) -->
<script type="text/javascript">(function(i,m,p,a,c,t){c.ire_o=p;c[p]=c[p]||function(){(c[p].a=c[p].a||[]).push(arguments)};t=a.createElement(m);var z=a.getElementsByTagName(m)[0];t.async=1;t.src=i;z.parentNode.insertBefore(t,z)})('https://utt.impactcdn.com/P-A7333443-d775-4dfb-addf-0aa89ab29f151.js','script','impactStat',document,window);impactStat('transformLinks');impactStat('trackImpression');</script>
"""

ACCOUNT_ID = "P-A7333443"

# Pages to target
targets = []
targets.append(ROOT / "fx.html")
targets += sorted((ROOT / "fx").glob("*/index.html"))
targets += sorted((ROOT / "moving-to-zimbabwe").glob("*.html"))

installed = []
skipped = []
errors = []

for path in targets:
    if not path.exists():
        errors.append((path, "missing"))
        continue
    try:
        html = path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append((path, f"read: {e}"))
        continue
    if ACCOUNT_ID in html:
        skipped.append(path)
        continue
    # Insert before the first </head>
    if "</head>" not in html:
        errors.append((path, "no </head>"))
        continue
    new = html.replace("</head>", UTT_BLOCK + "</head>", 1)
    path.write_text(new, encoding="utf-8")
    installed.append(path)

print(f"\n=== UTT install run ===")
print(f"Targets checked: {len(targets)}")
print(f"Installed:       {len(installed)}")
for p in installed:
    print(f"  + {p.relative_to(ROOT)}")
print(f"Already had UTT (skipped): {len(skipped)}")
for p in skipped[:3]:
    print(f"  = {p.relative_to(ROOT)}")
if len(skipped) > 3:
    print(f"  … +{len(skipped) - 3} more")
if errors:
    print(f"Errors: {len(errors)}")
    for p, e in errors:
        print(f"  ! {p.relative_to(ROOT)}: {e}")
