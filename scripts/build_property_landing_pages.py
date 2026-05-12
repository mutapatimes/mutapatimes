#!/usr/bin/env python3
"""Build /property-landing/{md5}.html — one landing page per
properties-feed item. Each page declares the listing's 1080×1350
hybrid card (photo top + brand strip) as og:image so Metricool's
autolist preview picks up our branded card instead of scraping
property.co.zw or the agent's site.

The page shows the card centred on ink-black with a red
"View listing →" CTA linking to the source.
"""
import hashlib
import json
import os
from html import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "property-landing")
os.makedirs(OUT_DIR, exist_ok=True)

BASE_URL = "https://mutapatimes.com"


def _md5_12(s):
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()[:12]


def collect_items():
    items = []
    p = os.path.join(ROOT, "data", "property-listings.json")
    if not os.path.exists(p):
        return items
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return items

    for li in (data.get("listings") or data.get("items") or []):
        url = (li.get("url") or "").strip()
        title = (li.get("title") or "").strip()
        if not url or not title:
            continue
        price = li.get("price") or li.get("price_usd") or ""
        location = li.get("location") or li.get("suburb") or ""
        beds = li.get("bedrooms") or li.get("beds")
        baths = li.get("bathrooms") or li.get("baths")
        ptype = li.get("type") or li.get("category") or "Property"
        agent = li.get("agent") or li.get("agency") or ""
        source = (li.get("source") or "property.co.zw").strip()

        spec_parts = []
        if price:
            spec_parts.append(str(price))
        if beds:
            spec_parts.append(f"{beds} bed")
        if baths:
            spec_parts.append(f"{baths} bath")
        if location:
            spec_parts.append(str(location))
        spec = " · ".join(spec_parts)

        desc = (li.get("description") or li.get("summary") or "").strip()
        body = desc or spec or "Zimbabwe property listing"

        items.append({
            "title": title,
            "description": body[:280],
            "kind_label": ptype.upper() if isinstance(ptype, str) else "PROPERTY",
            "card_path": f"/img/cards/properties/{_md5_12(url)}.png",
            "destination": url,
            "spec": spec,
            "key": url,
            "cta": f"View listing on {source}",
            "agent": agent,
        })
    return items


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title_esc} — The Mutapa Times</title>
  <link rel="canonical" href="{canonical}">

  <meta name="robots" content="noindex,follow">
  <meta name="theme-color" content="#1A1A1A">

  <meta property="og:type" content="article">
  <meta property="og:site_name" content="The Mutapa Times">
  <meta property="og:title" content="{title_esc}">
  <meta property="og:description" content="{desc_esc}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{card_url}">
  <meta property="og:image:secure_url" content="{card_url}">
  <meta property="og:image:type" content="image/png">
  <meta property="og:image:width" content="1080">
  <meta property="og:image:height" content="1350">
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
      margin: 0; background: #1A1A1A; color: #fff;
      font-family: 'Inter', system-ui, sans-serif;
      min-height: 100vh; display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      padding: 32px 20px calc(32px + env(safe-area-inset-bottom, 0px));
    }}
    .card-img {{
      width: 100%; max-width: 480px; height: auto;
      border-radius: 12px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.45);
      display: block;
    }}
    .kind {{
      font-size: 0.74rem; letter-spacing: 0.22em;
      text-transform: uppercase; color: #C41E1E;
      font-weight: 700; margin: 24px 0 8px;
    }}
    .title {{
      font-family: 'Playfair Display', Georgia, serif;
      font-weight: 700; font-size: clamp(1.1rem, 2.4vw, 1.3rem);
      line-height: 1.3; margin: 0 0 8px; max-width: 540px;
      text-align: center; text-shadow: 0 1px 4px rgba(0,0,0,0.4);
    }}
    .spec {{
      font-size: 0.82rem; color: rgba(255,255,255,0.65);
      margin: 0 0 24px; letter-spacing: 0.02em; text-align: center;
    }}
    .cta {{
      display: inline-block; background: #C41E1E; color: #fff !important;
      text-decoration: none; font-weight: 700;
      font-size: 0.95rem; letter-spacing: 0.04em;
      padding: 14px 32px; border-radius: 999px;
      box-shadow: 0 8px 24px rgba(196,30,30,0.35);
      transition: transform 0.15s ease;
    }}
    .cta:hover {{ transform: translateY(-1px); }}
    .brand {{
      margin-top: 32px; font-size: 0.74rem;
      letter-spacing: 0.18em; text-transform: uppercase;
      color: rgba(255,255,255,0.5);
    }}
    .brand a {{ color: rgba(255,255,255,0.7); text-decoration: none; }}
  </style>
</head>
<body>
  <img class="card-img" src="{card_path}" alt="{title_esc}">
  <p class="kind">{kind_label_esc}</p>
  <p class="title">{title_esc}</p>
  {spec_html}
  <a class="cta" href="{destination_esc}" rel="noopener" target="_blank">{cta_esc}  →</a>
  <p class="brand"><a href="/">The Mutapa Times</a> &middot; <a href="/property">All property</a></p>
</body>
</html>
"""


def build_one(item, out_dir):
    h = _md5_12(item["key"])
    canonical = f"{BASE_URL}/property-landing/{h}.html"
    card_url = f"{BASE_URL}{item['card_path']}"
    spec_html = (
        f'<p class="spec">{escape(item["spec"])}</p>'
        if item.get("spec") else ""
    )
    html = TEMPLATE.format(
        title_esc=escape(item["title"]),
        desc_esc=escape((item.get("description") or "")[:280]),
        canonical=canonical,
        card_url=card_url,
        card_path=item["card_path"],
        kind_label_esc=escape(item.get("kind_label") or "Property"),
        spec_html=spec_html,
        destination_esc=escape(item["destination"]),
        cta_esc=escape(item.get("cta") or "View listing"),
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
    print("=== BUILD PROPERTY LANDING PAGES ===")
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
