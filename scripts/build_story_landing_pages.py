#!/usr/bin/env python3
"""Build /stories/{md5}.html landing pages — one per stories-feed item.

Why: Metricool's RSS autolist preview scrapes the link target's
og:image rather than the feed's media:content tags. Our article pages
set og:image to the 4:5 feed card; jobs/property point to external
sites we don't control. So the stories feed gets dedicated landing
pages that:
  • declare og:image = the 1080×1920 story card we already render,
  • display the card with a 'Read more on Mutapa Times' CTA, and
  • link out to the underlying destination (article / job / listing).

These pages are noindex (they're a Metricool-preview indirection,
not editorial content) and they reuse the main site CSS so the
chrome stays on-brand.
"""
import hashlib
import json
import os
import re
import sys
from html import escape

# Reuse the same item collectors as the stories feed so URLs match exactly.
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "https://mutapatimes.com"
OUT_DIR = os.path.join(ROOT, "stories")
os.makedirs(OUT_DIR, exist_ok=True)


def _md5_12(s):
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()[:12]


def _slugify(text, max_len=80):
    s = (text or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return (s[:max_len] or "story").rstrip("-")


# ── Item collection — mirrors generate_rss.collect_stories_items ──
def collect_items():
    items = []

    # 1) Business / Policy / Tech / Economy / Environment CMS articles
    idx_path = os.path.join(ROOT, "content", "articles", "index.json")
    if os.path.exists(idx_path):
        try:
            entries = json.load(open(idx_path))
        except (json.JSONDecodeError, OSError):
            entries = []
        keep = {"Business", "Policy", "Tech", "Economy", "Environment", "Culture"}
        # Newest first
        entries = sorted(
            [e for e in entries if isinstance(e, dict)],
            key=lambda e: e.get("date", ""), reverse=True,
        )
        for e in entries:
            slug = e.get("slug")
            cat = (e.get("category") or "").strip()
            title = (e.get("title") or "").strip()
            if not slug or not title or cat not in keep:
                continue
            url = f"{BASE_URL}/articles/{slug}"
            items.append({
                "title": title,
                "description": e.get("summary", ""),
                "destination": url,
                "kind": "article",
                "kind_label": cat,
                "date": e.get("date", ""),
            })

    # 2) Jobs (external + internships)
    jobs_path = os.path.join(ROOT, "data", "jobs.json")
    internships = [
        ("Junior Social Media Assistant",
         "Help grow our social channels. Pitch fresh formats and ideas. Fully remote, 3 days/week, 3 months. Rolling intake.",
         f"{BASE_URL}/jobs#social-media"),
        ("Junior Editorial Coordinator",
         "Pitch, draft and edit original explainers. Bring fresh editorial angles. Fully remote, 3 days/week, 3 months. Rolling intake.",
         f"{BASE_URL}/jobs#editorial"),
        ("Junior Data Analyst",
         "Turn Zimbabwe public data into clear visual stories. Bring new data ideas. Fully remote, 3 days/week, 3 months. Rolling intake.",
         f"{BASE_URL}/jobs#data"),
        ("Business Development Associate",
         "Open doors for advertisers, sponsors and partners across the Zim diaspora corridor. Fully remote, 3 days/week, 3 months. Rolling intake.",
         f"{BASE_URL}/jobs#biz-dev"),
    ]
    for title, summary, url in internships:
        items.append({
            "title": title,
            "description": summary,
            "destination": url,
            "kind": "internship",
            "kind_label": "Internship",
            "date": "",
        })
    if os.path.exists(jobs_path):
        try:
            data = json.load(open(jobs_path))
        except (json.JSONDecodeError, OSError):
            data = {}
        for j in (data.get("jobs") or []):
            url = (j.get("url") or "").strip()
            title = (j.get("title") or "").strip()
            if not url or not title:
                continue
            bits = [b for b in [j.get("company"), j.get("location"), j.get("type")] if b]
            items.append({
                "title": title,
                "description": " · ".join(bits) or (j.get("summary") or "")[:200],
                "destination": url,
                "kind": "job",
                "kind_label": "Job",
                "date": j.get("posted") or j.get("date") or "",
            })

    # 3) Property listings
    prop_path = os.path.join(ROOT, "data", "property-listings.json")
    if os.path.exists(prop_path):
        try:
            data = json.load(open(prop_path))
        except (json.JSONDecodeError, OSError):
            data = {}
        for li in (data.get("listings") or data.get("items") or []):
            url = (li.get("url") or "").strip()
            title = (li.get("title") or "").strip()
            if not url or not title:
                continue
            price = li.get("price") or ""
            location = li.get("location") or li.get("suburb") or ""
            beds = li.get("bedrooms") or li.get("beds")
            bits = [str(price), f"{beds} bed" if beds else "", str(location)]
            bits = [b for b in bits if b]
            items.append({
                "title": title,
                "description": " · ".join(bits) or "Zimbabwe property listing",
                "destination": url,
                "kind": "property",
                "kind_label": "Property",
                "date": li.get("date") or li.get("publishedAt") or "",
            })

    return items


# ── HTML template ─────────────────────────────────────────
TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4428529474445353" crossorigin="anonymous"></script>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title_esc} — The Mutapa Times</title>
  <link rel="canonical" href="{canonical}">

  <!-- Noindex: these are Metricool-preview indirection pages, not editorial -->
  <meta name="robots" content="noindex,follow">
  <meta name="theme-color" content="#1A1A1A">

  <!-- Open Graph + Twitter — this is the whole point of the page -->
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="The Mutapa Times">
  <meta property="og:title" content="{title_esc}">
  <meta property="og:description" content="{desc_esc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{card_url}">
  <meta property="og:image:secure_url" content="{card_url}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1080">
  <meta property="og:image:height" content="1920">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="{card_url}">
  <meta name="twitter:title" content="{title_esc}">
  <meta name="twitter:description" content="{desc_esc}">
  <meta name="twitter:site" content="@mutapatimes">

  <link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32x32.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet">

  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: #1A1A1A;
      color: #fff;
      font-family: 'Inter', system-ui, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 32px 20px calc(32px + env(safe-area-inset-bottom, 0px));
    }}
    .story-card-img {{
      width: 100%;
      max-width: 480px;
      height: auto;
      border-radius: 12px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.45);
      display: block;
    }}
    .story-kind {{
      font-size: 0.74rem;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: #C41E1E;
      font-weight: 700;
      margin: 24px 0 8px;
    }}
    .story-title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-weight: 700;
      font-size: clamp(1.1rem, 2.4vw, 1.3rem);
      line-height: 1.3;
      margin: 0 0 28px;
      max-width: 540px;
      text-align: center;
      text-shadow: 0 1px 4px rgba(0,0,0,0.4);
    }}
    .story-cta {{
      display: inline-block;
      background: #C41E1E;
      color: #fff !important;
      text-decoration: none;
      font-weight: 700;
      font-size: 0.95rem;
      letter-spacing: 0.04em;
      padding: 14px 32px;
      border-radius: 999px;
      box-shadow: 0 8px 24px rgba(196,30,30,0.35);
      transition: transform 0.15s ease;
    }}
    .story-cta:hover {{ transform: translateY(-1px); }}
    .story-brand {{
      margin-top: 32px;
      font-size: 0.74rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.5);
    }}
    .story-brand a {{ color: rgba(255,255,255,0.7); text-decoration: none; }}
  </style>
</head>
<body>
  <img class="story-card-img" src="{card_url_rel}" alt="{title_esc}">
  <p class="story-kind">{kind_label_esc}</p>
  <p class="story-title">{title_esc}</p>
  <a class="story-cta" href="{destination_esc}" rel="noopener">Read more on Mutapa Times  →</a>
  <p class="story-brand"><a href="/">The Mutapa Times</a> &middot; mutapatimes.com</p>
</body>
</html>
"""


def landing_url_for(destination):
    h = _md5_12(destination)
    return h, f"{BASE_URL}/stories/{h}.html"


def build_one(item, out_dir):
    h = _md5_12(item["destination"])
    card_path = f"/img/cards/stories/{h}.png"
    card_url = f"{BASE_URL}{card_path}"
    canonical = f"{BASE_URL}/stories/{h}.html"
    html = TEMPLATE.format(
        title_esc=escape(item["title"]),
        desc_esc=escape((item.get("description") or "")[:280]),
        canonical=canonical,
        card_url=card_url,
        card_url_rel=card_path,
        destination_esc=escape(item["destination"]),
        kind_label_esc=escape((item.get("kind_label") or "Story").upper()),
    )
    out_path = os.path.join(out_dir, f"{h}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return h


def prune_stale(active_hashes, out_dir):
    pruned = 0
    for name in os.listdir(out_dir):
        if not name.endswith(".html"):
            continue
        h = name[:-5]
        if h not in active_hashes:
            try:
                os.remove(os.path.join(out_dir, name))
                pruned += 1
            except OSError:
                pass
    return pruned


def main():
    print("=== BUILD STORY LANDING PAGES ===")
    items = collect_items()
    print(f"  Collected {len(items)} items")

    active = set()
    built = 0
    for it in items:
        try:
            h = build_one(it, OUT_DIR)
            active.add(h)
            built += 1
        except Exception as e:
            print(f"    FAIL {it['title'][:48]}: {e}")

    pruned = prune_stale(active, OUT_DIR)
    print(f"  Wrote {built} landing pages · Pruned {pruned} stale")
    print(f"  Output: {OUT_DIR}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
