#!/usr/bin/env python3
"""Generate the /sport section (hub + one page per league) for an edition.

Reuses build_static_pages' page_head/page_nav/page_footer so nav, footer, GA and
theme match the rest of the site; the league list comes from sport_config. Pages
are thin shells — js/sport.js fills them from data/sport/*.json. The section is
cross-region (same data), each edition just LEADS with its home league.

  python3 scripts/build_sport_pages.py --region zw   # sport.html + sport/<slug>.html
  python3 scripts/build_sport_pages.py --region za   # za/sport.html + za/sport/<slug>.html
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_static_pages import page_head, page_nav, page_footer, esc, BASE_URL  # noqa: E402
from sport_config import LEAGUES  # noqa: E402
from regions import region_path_prefix, region_is_indexable  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPORT_LEAD = {"zw": "castle-lager-psl", "za": "dstv-premiership"}
SPORT_CSS = '\n    <link rel="stylesheet" href="/css/sport.css?v=3">'
SPORT_JS = '\n  <script defer src="/js/sport.js?v=3"></script>'
OG = "https://mutapatimes.com/img/harare-palms.jpg"


def _robots(region):
    return "index, follow" if region_is_indexable(region) else "noindex, follow"


def _edition_dir(region):
    return ROOT if region == "zw" else os.path.join(ROOT, region)


def _write(path, html):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("  wrote", os.path.relpath(path, ROOT))


def build_hub(region):
    pfx = "" if region == "zw" else region_path_prefix(region)
    depth = 0 if region == "zw" else 1
    lead = SPORT_LEAD.get(region, "premier-league")
    canonical = f"{BASE_URL}{pfx}/sport"
    title = "Sport | The Mutapa Times"
    desc = ("Live football tables, results and fixtures for the Premier League, "
            "DStv Premiership and Castle Lager PSL, plus opinion from Kundai Kaycee.")
    head = page_head(title, desc, canonical, "website", OG, depth=depth,
                     robots=_robots(region), pfx=pfx)
    nav = page_nav(active="sport", depth=depth, pfx=pfx, region=region)
    body = f'''  <main class="sport-main">
    <div class="sport-head">
      <h1>Sport</h1>
      <p class="sport-deck">Live football tables, results and fixtures across the Premier League, DStv Premiership and Castle Lager PSL, with opinion and analysis from Kundai Kaycee.</p>
    </div>
    <div id="sport-app" data-page="hub" data-lead="{esc(lead)}"></div>
    <section id="sport-editorial" class="sport-editorial"></section>
  </main>
'''
    foot = page_footer(depth=depth, extra_scripts=SPORT_JS, pfx=pfx, region=region)
    _write(os.path.join(_edition_dir(region), "sport.html"), head + SPORT_CSS + nav + body + foot)


def build_league(region, lg):
    pfx = "" if region == "zw" else region_path_prefix(region)
    depth = 1 if region == "zw" else 2
    slug = lg["slug"]
    canonical = f"{BASE_URL}{pfx}/sport/{slug}"
    title = f"{lg['name']}: Table, Results & Fixtures | The Mutapa Times"
    desc = (f"{lg['name']} ({lg['country']}): live standings, recent results and "
            f"upcoming fixtures on The Mutapa Times.")
    head = page_head(title, desc, canonical, "website", OG, depth=depth,
                     robots=_robots(region), pfx=pfx)
    nav = page_nav(active="sport", depth=depth, pfx=pfx, region=region)
    body = f'''  <main class="sport-main">
    <div class="sport-head">
      <p><a href="{pfx}/sport" class="sport-back">&larr; All sport</a></p>
      <h1>{esc(lg.get("flag", ""))} {esc(lg["name"])}</h1>
      <p class="sport-deck">{esc(lg["country"])}. Standings, recent results and upcoming fixtures, refreshed through the day.</p>
    </div>
    <div id="sport-app" data-page="league" data-slug="{esc(slug)}"></div>
    <section id="sport-editorial" class="sport-editorial"></section>
  </main>
'''
    foot = page_footer(depth=depth, extra_scripts=SPORT_JS, pfx=pfx, region=region)
    _write(os.path.join(_edition_dir(region), "sport", f"{slug}.html"),
           head + SPORT_CSS + nav + body + foot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="zw")
    args = ap.parse_args()
    print(f"Building /sport for region '{args.region}'")
    build_hub(args.region)
    for lg in LEAGUES:
        build_league(args.region, lg)
    print(f"Done: 1 hub + {len(LEAGUES)} league pages")


if __name__ == "__main__":
    main()
