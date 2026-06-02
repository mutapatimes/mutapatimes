#!/usr/bin/env python3
"""
Build data/hotels.json — the combined Hotels.com / Commission Junction
affiliate inventory used by the site-wide "Sponsored stays" carousel
(js/harare-hotels.js).

Source feeds live in data/hotel-feeds/<city>.xlsx (Hotels.com CJ product
feeds, despite the .xlsx wrapper they are the CSV-style "Travel Feed"
export). Harare has no spreadsheet — its hand-curated inventory already
lives in data/harare-hotels.json and is folded in unchanged.

IMPORTANT accuracy rule: the CJ feeds are cumulative supersets, not
city-scoped. A "gweru" feed mostly contains Bulawayo/Victoria Falls/etc
properties. We must never label an out-of-town hotel as in-town:
  - Strong cities (enough genuine in-city stock) -> strict in-city filter.
  - Thin cities -> in-city first, then nearby/regional fill, each card
    keeps its OWN honest area label and the section reads "in and around".

Output structure (data/hotels.json):
  { "<slug>": {"title": str, "scope": "in"|"around", "hotels": [ {name,area,image,url}, ... ]},
    ... ,
    "all": [ balanced mix across cities ] }
"""
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEED_DIR = os.path.join(ROOT, "data", "hotel-feeds")
HARARE_JSON = os.path.join(ROOT, "data", "harare-hotels.json")
OUT = os.path.join(ROOT, "data", "hotels.json")

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# slug -> (display name, feed filename or None for Harare, strict?)
# strict=True  -> in-city only (strong inventory)
# strict=False -> in-city first then regional fill, "in and around"
CITIES = [
    ("harare",         "Harare",         None,                  True),
    ("bulawayo",       "Bulawayo",       "bulawayo.xlsx",       True),
    ("victoria-falls", "Victoria Falls", "victoria-falls.xlsx", True),
    ("mutare",         "Mutare",         "mutare.xlsx",         False),
    ("masvingo",       "Masvingo",       "masvingo.xlsx",       False),
    ("gweru",          "Gweru",          "gweru.xlsx",          False),
]

MAX_PER_CITY = 14   # cap so a carousel stays snappy
MAX_ALL = 18        # national mix size


def _colnum(ref):
    letters = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for c in letters:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def parse_feed(path):
    """Return list of {name, area, image, url} dicts from a Hotels.com xlsx feed."""
    z = zipfile.ZipFile(path)
    shared = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.iter(NS + "si"):
        shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.iter(NS + "row"):
        cells = {}
        for c in row.iter(NS + "c"):
            v = c.find(NS + "v")
            if v is None:
                continue
            val = shared[int(v.text)] if c.get("t") == "s" else v.text
            cells[_colnum(c.get("r"))] = val
        rows.append(cells)
    # Row 0 is a CJ note; row 1 is the header.
    header = rows[1]

    def col(name):
        for k, v in header.items():
            if v and v.strip().lower() == name.lower():
                return k
        return None

    c_title = col("Product Title")
    c_desc = col("Product Description")
    c_img = col("Image URL")
    c_url = col("Copy Link")
    out = []
    for r in rows[2:]:
        name = (r.get(c_title) or "").strip()
        url = (r.get(c_url) or "").strip()
        img = (r.get(c_img) or "").strip()
        desc = r.get(c_desc) or ""
        if not (name and url and img):
            continue
        m = re.search(r"Located in ([A-Za-z .'\-]+?)[,.]", desc)
        area = m.group(1).strip() if m else ""
        out.append({"name": name, "area": area, "image": img, "url": url, "_desc": desc})
    return out


# Known Zimbabwe towns/areas, used only to give regional-fill cards an
# honest place label when the feed's "Located in" phrase didn't parse.
KNOWN_AREAS = [
    "Victoria Falls", "Bulawayo", "Harare", "Mutare", "Masvingo", "Gweru",
    "Kariba", "Hwange", "Nyanga", "Kadoma", "Kwekwe", "Chinhoyi", "Beitbridge",
    "Great Zimbabwe", "Matobo", "Lake Kariba",
]


def in_city(hotel, display):
    hay = (hotel["name"] + " " + hotel.get("_desc", "")).lower()
    return display.lower() in hay


def detect_area(hotel):
    """Honest place label: prefer the feed's 'Located in', else scan the
    name/description for a known Zimbabwe town, else 'Zimbabwe'."""
    if hotel["area"]:
        return hotel["area"]
    hay = hotel["name"] + " " + hotel.get("_desc", "")
    for town in KNOWN_AREAS:
        if town.lower() in hay.lower():
            return town
    return "Zimbabwe"


def clean(hotel, fallback_area):
    return {
        "name": hotel["name"],
        "area": detect_area(hotel) if fallback_area == "Zimbabwe" else (hotel["area"] or fallback_area),
        "image": hotel["image"],
        "url": hotel["url"],
    }


def dedupe(hotels):
    seen, out = set(), []
    for h in hotels:
        if h["name"] in seen:
            continue
        seen.add(h["name"])
        out.append(h)
    return out


def main():
    result = {}
    per_city_incity = {}  # slug -> in-city list (for the national mix)

    for slug, display, feed, strict in CITIES:
        if feed is None:
            # Harare: reuse the hand-curated JSON verbatim.
            data = json.load(open(HARARE_JSON))
            hotels = dedupe(data["hotels"])[:MAX_PER_CITY]
            result[slug] = {
                "title": f"Where to stay in {display}",
                "scope": "in",
                "hotels": hotels,
            }
            per_city_incity[slug] = hotels
            print(f"{display:16} {len(hotels):3} (curated)")
            continue

        raw = dedupe(parse_feed(os.path.join(FEED_DIR, feed)))
        incity = [clean(h, display) for h in raw if in_city(h, display)]
        per_city_incity[slug] = incity

        if strict:
            hotels = incity[:MAX_PER_CITY]
            scope = "in"
            title = f"Where to stay in {display}"
        else:
            # In-city first, then regional fill (honest per-card area labels).
            regional = [clean(h, "Zimbabwe") for h in raw if not in_city(h, display)]
            hotels = (incity + regional)[:MAX_PER_CITY]
            scope = "around"
            title = f"Where to stay in and around {display}"

        result[slug] = {"title": title, "scope": scope, "hotels": hotels}
        print(f"{display:16} {len(hotels):3}  (in-city {len(incity)}, scope={scope})")

    # National mix: round-robin across each city's genuine in-city stock.
    pools = [list(per_city_incity[s]) for s, *_ in CITIES]
    mix, i = [], 0
    seen = set()
    while len(mix) < MAX_ALL and any(pools):
        pool = pools[i % len(pools)]
        if pool:
            h = pool.pop(0)
            if h["name"] not in seen:
                seen.add(h["name"])
                mix.append(h)
        i += 1
        if i > 500:
            break
    result["all"] = mix
    print(f"{'All Zimbabwe':16} {len(mix):3}  (national mix)")

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
