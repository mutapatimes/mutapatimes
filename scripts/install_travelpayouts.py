#!/usr/bin/env python3
"""Install the Travelpayouts 'Drive' tracking script on revenue pages.

Idempotent: skips files that already contain the unique tracker URL
(emrldtp.cc/NTMyMTA3.js). Inserts just before </head>.

Targets:
  - index.html  (homepage, required for Travelpayouts verification)
  - fx.html
  - fx/<slug>/index.html  (16 corridor pages)
  - moving-to-zimbabwe/*.html  (6 pages)
"""
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")

TP_BLOCK = """<!-- Travelpayouts Drive tracking -->
<script nowprocket data-noptimize="1" data-cfasync="false" data-wpfc-render="false" seraph-accel-crit="1" data-no-defer="1">
  (function () {
      var script = document.createElement("script");
      script.async = 1;
      script.src = 'https://emrldtp.cc/NTMyMTA3.js?t=532107';
      document.head.appendChild(script);
  })();
</script>
"""

MARKER = "emrldtp.cc/NTMyMTA3.js"

targets = [ROOT / "index.html", ROOT / "fx.html"]
targets += sorted((ROOT / "fx").glob("*/index.html"))
targets += sorted((ROOT / "moving-to-zimbabwe").glob("*.html"))

installed, skipped, errors = [], [], []
for path in targets:
    if not path.exists():
        errors.append((path, "missing")); continue
    try:
        html = path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append((path, f"read: {e}")); continue
    if MARKER in html:
        skipped.append(path); continue
    if "</head>" not in html:
        errors.append((path, "no </head>")); continue
    new = html.replace("</head>", TP_BLOCK + "</head>", 1)
    path.write_text(new, encoding="utf-8")
    installed.append(path)

print("=== Travelpayouts Drive install ===")
print(f"Targets:   {len(targets)}")
print(f"Installed: {len(installed)}")
for p in installed:
    print(f"  + {p.relative_to(ROOT)}")
print(f"Skipped (already had it): {len(skipped)}")
if errors:
    print(f"Errors: {len(errors)}")
    for p, e in errors:
        print(f"  ! {p.relative_to(ROOT)}: {e}")
