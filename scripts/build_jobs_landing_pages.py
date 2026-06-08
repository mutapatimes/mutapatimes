#!/usr/bin/env python3
"""Build /jobs-landing/{md5}.html - one landing page per jobs-feed
item. Each page declares the job's 1080×1350 card as og:image so
Metricool's autolist preview picks our branded card up instead of
scraping the external job board (vacancymail.co.zw etc.).

Each landing page shows the card centred on ink-black, with a red
"Apply now →" CTA that links out to the underlying source.
"""
import hashlib
import json
import os
from html import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "jobs-landing")
os.makedirs(OUT_DIR, exist_ok=True)

BASE_URL = "https://mutapatimes.com"


def _md5_12(s):
    return hashlib.md5((s or "").encode("utf-8")).hexdigest()[:12]


# Same internship list as build_job_cards.py so card paths align
INTERNSHIPS = [
    {
        "slug": "social-intern", "role": "Social Intern",
        "destination": f"{BASE_URL}/jobs#social-intern",
        "body": "Help grow our social channels. Pitch fresh formats and ideas, spot trends, and shape how The Mutapa Times shows up across Instagram, Threads, X, TikTok and LinkedIn. Bring your own thinking - we like innovation.",
        "spec": "Fully remote · 3 days a week · 3 months · Rolling intake",
        "card": "internship-social-intern.png",
        "kind_label": "Internship - The Mutapa Times",
    },
    {
        "slug": "editor-intern", "role": "Editor Intern",
        "destination": f"{BASE_URL}/jobs#editor-intern",
        "body": "Pitch, draft and edit original explainers and analysis. Fact-check stories, help shape the twice-weekly newsletter, and bring new editorial angles for telling Zimbabwean stories to a diaspora audience.",
        "spec": "Fully remote · 3 days a week · 3 months · Rolling intake",
        "card": "internship-editor-intern.png",
        "kind_label": "Internship - The Mutapa Times",
    },
    {
        "slug": "data-intern", "role": "Data Intern",
        "destination": f"{BASE_URL}/jobs#data-intern",
        "body": "Turn Zimbabwean public data into clear, visual stories. Extend the live economy briefing, prototype new ways to make numbers readable, and bring your own data ideas.",
        "spec": "Fully remote · 3 days a week · 3 months · Rolling intake",
        "card": "internship-data-intern.png",
        "kind_label": "Internship - The Mutapa Times",
    },
]


def collect_items():
    items = []

    # Internships first
    for it in INTERNSHIPS:
        items.append({
            "title": it["role"],
            "description": it["body"],
            "kind_label": it["kind_label"],
            "card_path": f"/img/cards/jobs/{it['card']}",
            "destination": it["destination"],
            "spec": it["spec"],
            "key": it["destination"],   # used for landing-page hash
            "cta": "Apply via The Mutapa Times",
        })

    # External jobs from data/jobs.json
    jobs_path = os.path.join(ROOT, "data", "jobs.json")
    if not os.path.exists(jobs_path):
        return items
    try:
        data = json.load(open(jobs_path))
    except (json.JSONDecodeError, OSError):
        return items

    for j in (data.get("jobs") or []):
        url = (j.get("url") or "").strip()
        title = (j.get("title") or "").strip()
        if not url or not title:
            continue
        company = (j.get("company") or "").strip()
        location = (j.get("location") or "").strip()
        jtype = (j.get("type") or "").strip()
        salary = (j.get("salary") or "").strip()
        summary = (j.get("summary") or "").strip()
        spec_bits = [b for b in [company, location, jtype, salary] if b]
        spec = " · ".join(spec_bits)
        # Body - summary if we have one, otherwise the spec line
        body = summary or spec
        source = (j.get("source") or "vacancymail.co.zw").strip()
        items.append({
            "title": title,
            "description": (summary or spec)[:280],
            "kind_label": company or "Job",
            "card_path": f"/img/cards/jobs/{_md5_12(url)}.png",
            "destination": url,
            "spec": spec,
            "key": url,
            "cta": f"Apply via {source}",
        })
    return items


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4428529474445353" crossorigin="anonymous"></script>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{title_esc} - The Mutapa Times</title>
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
      margin: 0 0 24px; letter-spacing: 0.02em;
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
  <p class="brand"><a href="/">The Mutapa Times</a> &middot; <a href="/jobs">All jobs</a></p>
</body>
</html>
"""


def build_one(item, out_dir):
    h = _md5_12(item["key"])
    canonical = f"{BASE_URL}/jobs-landing/{h}.html"
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
        kind_label_esc=escape(item.get("kind_label") or "Job"),
        spec_html=spec_html,
        destination_esc=escape(item["destination"]),
        cta_esc=escape(item.get("cta") or "Apply now"),
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
    print("=== BUILD JOBS LANDING PAGES ===")
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
