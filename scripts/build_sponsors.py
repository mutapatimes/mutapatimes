#!/usr/bin/env python3
"""Read content/sponsors/*.md (CMS-edited) and write data/sponsors.json
for the front-end editorial-strip renderer at /js/sponsors.js.

Format on disk (frontmatter only — body is optional):
  ---
  name: Safari & Co
  active: true
  strip_copy: "Sponsored briefing by Safari & Co — building tomorrow's lodges"
  url: "https://safariandco.com"
  placements: [news, articles]
  start_date: 2026-05-14T00:00:00.000Z
  end_date: 2026-06-14T00:00:00.000Z
  ---

Only sponsors with active=true AND today within [start_date, end_date]
make it into the published JSON. Editorial-strip pattern only — no
banner ad slots, ever.
"""
import glob
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC_DIR = os.path.join(ROOT, "content", "sponsors")
OUT = os.path.join(ROOT, "data", "sponsors.json")


def _parse_iso(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _grab(fm, key, default=""):
    mm = re.search(rf'^{key}:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
    return mm.group(1).strip() if mm else default


def _grab_list(fm, key):
    # Inline form:  placements: [news, articles, fx]
    inline = re.search(rf'^{key}:\s*\[(.*?)\]\s*$', fm, re.MULTILINE)
    if inline:
        return [x.strip().strip('"').strip("'")
                for x in inline.group(1).split(",") if x.strip()]
    # Block form:
    #   placements:
    #     - news
    #     - articles
    block = re.search(rf'^{key}:\s*\n((?:\s*-\s*.+\n?)+)', fm, re.MULTILINE)
    if block:
        return [ln.strip().lstrip("-").strip().strip('"').strip("'")
                for ln in block.group(1).splitlines() if ln.strip().startswith("-")]
    return []


def collect():
    now = datetime.now(timezone.utc)
    out = []
    if not os.path.isdir(SRC_DIR):
        return out
    for path in sorted(glob.glob(os.path.join(SRC_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        active = _grab(fm, "active", "false").lower() == "true"
        if not active:
            continue
        start = _parse_iso(_grab(fm, "start_date"))
        end = _parse_iso(_grab(fm, "end_date"))
        if start and now < start:
            continue
        if end and now > end:
            continue
        name = _grab(fm, "name")
        copy = _grab(fm, "strip_copy")
        url = _grab(fm, "url")
        if not (name and copy and url):
            continue
        weight_raw = _grab(fm, "weight", "1")
        try:
            weight = float(weight_raw)
        except (TypeError, ValueError):
            weight = 1.0
        # Card / creative fields (optional). When present, the surface
        # can render the actual affiliate creative inside an editorial
        # "Presented by X" card instead of (or alongside) the text strip.
        def _int(key):
            raw = _grab(fm, key)
            try:
                return int(raw) if raw else None
            except ValueError:
                return None
        out.append({
            "name": name,
            "strip_copy": copy,
            "url": url,
            "logo": _grab(fm, "logo") or None,
            "placements": _grab_list(fm, "placements") or [],
            "card_placements": _grab_list(fm, "card_placements") or [],
            "impression_pixel": _grab(fm, "impression_pixel") or None,
            "weight": weight,
            "creative_url": _grab(fm, "creative_url") or None,
            "creative_iframe_src": _grab(fm, "creative_iframe_src") or None,
            "creative_width": _int("creative_width"),
            "creative_height": _int("creative_height"),
            "creative_caption": _grab(fm, "creative_caption") or None,
            "creative_eyebrow": _grab(fm, "creative_eyebrow") or None,
        })
    return out


def main():
    print("=== BUILD SPONSORS ===")
    rows = collect()
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "sponsors": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Wrote {len(rows)} active sponsors -> {OUT}")
    for r in rows:
        print(f"    {r['name']:<24s}  pages={','.join(r['placements'])}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
