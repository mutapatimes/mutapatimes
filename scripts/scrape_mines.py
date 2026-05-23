#!/usr/bin/env python3
"""Aggregate Zimbabwean mine articles from all relevant Wikipedia categories,
plus a hand-curated list of major mines and quarry/mineral operations that
matter commercially but have less-than-obvious Wikipedia titles."""
import re, json, urllib.request, time
from pathlib import Path

UA = "MutapaTimes/1.0 (https://www.mutapatimes.com; news@mutapatimes.com)"
ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")

CATEGORIES = [
    ("Mines_in_Zimbabwe",            "General"),
    ("Gold_mines_in_Zimbabwe",       "Gold"),
    ("Platinum_mines_in_Zimbabwe",   "Platinum group"),
    ("Lithium_mines_in_Zimbabwe",    "Lithium"),
    ("Diamond_mines_in_Zimbabwe",    "Diamond"),
    ("Iron_mines_in_Zimbabwe",       "Iron"),
]

# Hand-curated additions — major Zimbabwean mines not necessarily in a clean
# Wikipedia category, with their primary commodity. Verified Wikipedia titles.
EXTRA = [
    ("Bikita Minerals",          "Lithium",      "Bikita_Minerals"),
    ("Mimosa Mine",              "Platinum group","Mimosa_Mine"),
    ("Zimplats",                 "Platinum group","Zimplats"),
    ("Unki Mine",                "Platinum group","Unki_Mine"),
    ("Marange diamond fields",   "Diamond",      "Marange_diamond_fields"),
    ("Sandawana Mine",           "Emerald",      "Sandawana"),
    ("Renco Mine",               "Gold",         "Renco_Mine"),
    ("How Mine",                 "Gold",         "How_Mine"),
    ("Freda Rebecca Mine",       "Gold",         "Freda_Rebecca_Mine"),
    ("Blanket Mine",             "Gold",         "Blanket_Mine"),
    ("Eureka Mine",              "Gold",         "Eureka_Mine,_Zimbabwe"),
    ("Mazowe Mine",              "Gold",         "Mazowe_Mine"),
    ("Shabanie Mine",            "Asbestos",     "Shabanie_Mine"),
    ("Hwange Colliery",          "Coal",         "Hwange_Colliery_Company"),
    ("Trojan Mine",              "Nickel",       "Trojan_Nickel_Mine"),
    ("Bindura Nickel Corporation","Nickel",      "Bindura_Nickel_Corporation"),
    ("Empress Mine",             "Nickel",       "Empress_Mine"),
    ("Arcadia Lithium Mine",     "Lithium",      "Arcadia_Lithium_Mine"),
    ("Sabi Gold Mine",           "Gold",         "Sabi_Gold_Mine"),
    ("Cam and Motor Mine",       "Gold",         "Cam_and_Motor_Mine"),
    ("Athens Mine",              "Gold",         "Athens_Mine"),
    ("Zinca Mine",               "Gold",         "Zinca_Mine"),
    ("Wankie Colliery",          "Coal",         "Wankie_Colliery"),
    ("Buchwa Iron Mine",         "Iron",         "Buchwa"),
    ("Redwing Mine",             "Gold",         "Redwing_Mine"),
]

def fetch_category_articles(cat_slug):
    url = f"https://en.wikipedia.org/wiki/Category:{cat_slug}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            h = r.read().decode("utf-8", errors="replace")
    except Exception:
        return []
    # Pages in this category — find the section after "Pages in category"
    sec = re.search(r'Pages in category(.*?)(?:</div>\s*</div>\s*</div>|<noscript)', h, re.S)
    if not sec: return []
    block = sec.group(1)
    links = re.findall(r'<a href="(/wiki/[^"#?]+)"\s+title="([^"]+)">', block)
    seen = set(); out = []
    for href, title in links:
        if title in seen: continue
        if any(x in title.lower() for x in ['category:', 'list of', 'special:', 'wikipedia:']): continue
        if href.startswith('/wiki/Category:'): continue
        seen.add(title)
        out.append((title, href.replace("/wiki/", "")))
    return out

aggregated = {}  # title -> {commodity, wp_slug}
for cat_slug, commodity in CATEGORIES:
    arts = fetch_category_articles(cat_slug)
    print(f"  {cat_slug}: {len(arts)} articles")
    for title, slug in arts:
        if title not in aggregated:
            aggregated[title] = {"commodity": commodity, "wp_slug": slug}
        else:
            # Keep the more specific commodity
            if aggregated[title]["commodity"] == "General":
                aggregated[title]["commodity"] = commodity
    time.sleep(0.3)

# Merge in hand-curated
for name, commodity, slug in EXTRA:
    if name not in aggregated:
        aggregated[name] = {"commodity": commodity, "wp_slug": slug}

# Save raw roster
out_file = Path("/tmp/mines-roster.json")
out_file.write_text(json.dumps(aggregated, indent=2))
print(f"\nTotal unique mines: {len(aggregated)}")
print(f"saved {out_file}")
for name, meta in sorted(aggregated.items()):
    print(f"  {meta['commodity']:<18} {name}")
