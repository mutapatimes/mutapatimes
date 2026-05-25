#!/usr/bin/env python3
"""Build /mining/ microsite from aggregated Zimbabwean mines roster.
Mirrors the schools/zse build pattern."""
import json, re, html, urllib.request, urllib.parse, time
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT  = ROOT / "mining"
OUT.mkdir(exist_ok=True)
IMG  = ROOT / "img" / "mining"
IMG.mkdir(parents=True, exist_ok=True)

UA = "MutapaTimes/1.0 (https://www.mutapatimes.com; news@mutapatimes.com)"
TODAY = "2026-05-22"

# Load raw roster + dedupe known title variants (Wikipedia sometimes has two
# articles for the same mine, e.g. "Mimosa Mine" + "Mimosa mine" as separate
# redirects/articles).
roster = json.loads(Path("/tmp/mines-roster.json").read_text())

# Canonicalise: lowercase variants of duplicate mines map to the canonical
DUPES = {
    "Bikita mine":      "Bikita Minerals",
    "Mimosa mine":      "Mimosa Mine",
    "Unki mine":        "Unki Mine",
    "Sandawana mines":  "Sandawana Mine",
}
mines = {}
for raw_name, meta in roster.items():
    canon = DUPES.get(raw_name, raw_name)
    if canon not in mines:
        mines[canon] = meta
        mines[canon]["name"] = canon
    # Promote a more specific commodity if we have one
    if meta["commodity"] != "General" and mines[canon]["commodity"] == "General":
        mines[canon]["commodity"] = meta["commodity"]

print(f"After dedupe: {len(mines)} unique mines")

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

# --- Wikipedia helpers ------------------------------------------------------
def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def http_download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read())

def fetch_wikitext(title):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&prop=wikitext&format=json&redirects=1"
    try:
        return http_get_json(url).get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception:
        return ""

def parse_infobox(wt):
    """Two-char lookahead state machine — handles nested templates correctly.
    Previous implementation walked char-by-char checking cur[-1], which
    over-counted consecutive close-braces (}}}}  was treated as 4 separate
    pair-closes instead of 2), causing the 'colours' field of Bernard
    Mizeki College to leak the rest of the infobox into its value."""
    m = re.search(r'\{\{Infobox[^\|]*\|', wt, re.I)
    if not m: return {}
    start = m.start()
    # Walk to the matching closing }} of the outer infobox
    depth = 0; i = start
    while i < len(wt):
        if wt[i:i+2] == '{{': depth += 1; i += 2; continue
        if wt[i:i+2] == '}}':
            depth -= 1; i += 2
            if depth == 0: break
            continue
        i += 1
    inner = wt[start+2:i-2]
    # Split inner on top-level | only (template_depth == 0 and link_depth == 0)
    parts = []; cur = []
    td = ld = 0
    j = 0
    while j < len(inner):
        two = inner[j:j+2]
        if two == '{{': td += 1; cur.append(two); j += 2; continue
        if two == '}}': td -= 1; cur.append(two); j += 2; continue
        if two == '[[': ld += 1; cur.append(two); j += 2; continue
        if two == ']]': ld -= 1; cur.append(two); j += 2; continue
        ch = inner[j]
        if ch == '|' and td == 0 and ld == 0:
            parts.append(''.join(cur)); cur = []
        else:
            cur.append(ch)
        j += 1
    if cur: parts.append(''.join(cur))
    out = {}
    for p in parts[1:]:
        if '=' not in p: continue
        k, v = p.split('=', 1)
        out[k.strip().lower()] = v.strip()
    return out

def clean_val(v):
    if not v: return ""
    v = re.sub(r'<ref[^>]*>.*?</ref>', '', v, flags=re.S)
    v = re.sub(r'<ref[^>]*/>', '', v)
    v = re.sub(r'\[\[File:[^\]]+\]\]', '', v, flags=re.I)
    v = re.sub(r'\{\{cite[^}]*\}\}', '', v, flags=re.I)
    v = re.sub(r'\{\{coord[^}]*\}\}', '', v, flags=re.I)
    v = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', v)
    v = re.sub(r'\[\[([^\]]+)\]\]', r'\1', v)
    v = re.sub(r"'''([^']+)'''", r'\1', v)
    v = re.sub(r"''([^']+)''", r'\1', v)
    # Iteratively strip nested templates: match only innermost first
    prev = None
    while prev != v:
        prev = v
        v = re.sub(r'\{\{[^{}]*\}\}', '', v)
    v = re.sub(r'<br\s*/?>', '; ', v, flags=re.I)
    v = re.sub(r'<[^>]+>', '', v)
    v = re.sub(r'\s+', ' ', v).strip()
    return v.strip(' ;,.')

def parse_coords(wt):
    """Find {{Coord|lat|lon|...}} or geo template in wikitext, return (lat, lon) or None."""
    m = re.search(r'\{\{[Cc]oord\|([^}]+)\}\}', wt)
    if not m: return None
    parts = [p.strip() for p in m.group(1).split('|')]
    # Try patterns:
    # {{coord|-18.5|29.3|...}}  -> decimal
    # {{coord|18|30|S|29|18|E|...}} -> DMS
    if len(parts) >= 2 and re.match(r'-?\d+\.\d+', parts[0]):
        try: return float(parts[0]), float(parts[1])
        except: return None
    # DMS: deg|min|sec|N/S|deg|min|sec|E/W
    try:
        d1, m1, s1, ns = parts[0], parts[1], parts[2], parts[3]
        d2, m2, s2, ew = parts[4], parts[5], parts[6], parts[7]
        lat = float(d1) + float(m1)/60 + float(s1)/3600
        if ns.upper() == 'S': lat = -lat
        lon = float(d2) + float(m2)/60 + float(s2)/3600
        if ew.upper() == 'W': lon = -lon
        return lat, lon
    except Exception:
        return None

def fetch_summary(title):
    try:
        return http_get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}").get("extract", "")
    except Exception:
        return ""

FREE_RE = re.compile(r"\b(CC[ -]?BY(?:[ -]?SA)?(?:[ -]?\d(?:\.\d)?)?|CC0|Public[ ]?domain|PDM|GFDL|OGL)\b", re.I)
NONFREE_RE = re.compile(r"\bfair[ -]?use\b|\bnon[- ]?free\b", re.I)

def fetch_image(title, slug):
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=pageimages&piprop=name&format=json&redirects=1"
    try: j = http_get_json(url)
    except Exception: return None
    page = next(iter(j.get("query", {}).get("pages", {}).values()), {})
    fname = page.get("pageimage")
    if not fname: return None
    url2 = (f"https://en.wikipedia.org/w/api.php?action=query"
            f"&titles={urllib.parse.quote('File:'+fname)}"
            f"&prop=imageinfo&iiprop=url|extmetadata|mime&format=json&redirects=1")
    try: j2 = http_get_json(url2)
    except Exception: return None
    page = next(iter(j2.get("query", {}).get("pages", {}).values()), {})
    infos = page.get("imageinfo")
    if not infos: return None
    info = infos[0]
    meta = info.get("extmetadata") or {}
    short = (meta.get("LicenseShortName") or {}).get("value", "")
    usage = (meta.get("UsageTerms") or {}).get("value", "")
    artist = re.sub(r'<[^>]+>', '', (meta.get("Artist") or {}).get("value", "")).strip()
    license_text = short + " " + usage
    if not FREE_RE.search(license_text) or NONFREE_RE.search(license_text):
        return None
    mime = info.get("mime","")
    ext = ".jpg"
    if "png" in mime: ext = ".png"
    elif "svg" in mime: ext = ".svg"
    dest = IMG / f"{slug}{ext}"
    try: http_download(info["url"], dest)
    except Exception: return None
    return {
        "filename": fname, "license": short, "artist": artist,
        "commons_page": f"https://commons.wikimedia.org/wiki/File:{fname.replace(' ','_')}",
        "local": f"/img/mining/{dest.name}",
    }

# --- Enrich each mine -------------------------------------------------------
INFOBOX_KEYS = ["products","owner","operator","company","opened","closed",
                "discovered","employees","location","place","subdivision_name",
                "type","greatest_depth","depth","website","active_years",
                "production","financial_year","stateparty","province","district"]

# Cache: skip re-enrichment if data/mines.json already has the same mines
cache_file = ROOT / "data" / "mines.json"
cache = {}
if cache_file.exists():
    try:
        cdata = json.loads(cache_file.read_text())
        for m in cdata.get("mines", []):
            cache[m["name"]] = m
    except Exception: pass

print(f"\nEnriching mines from Wikipedia (cache hits skipped)…")
for name, meta in mines.items():
    meta["slug"] = slugify(name)
    meta["name"] = name
    if name in cache and "wp" in cache[name]:
        meta["wp"] = cache[name]["wp"]
        print(f"  {name} ({meta['commodity']}) [cached]")
        continue
    print(f"  {name} ({meta['commodity']})")
    wt = fetch_wikitext(meta["wp_slug"])
    if not wt:
        meta["wp"] = {}
        continue
    ib = parse_infobox(wt)
    wp = {}
    for k in INFOBOX_KEYS:
        if k in ib:
            cv = clean_val(ib[k])
            if cv: wp[k] = cv
    # Normalise: prefer 'company' > 'owner' > 'operator' as a unified field
    for k in ["company","owner","operator"]:
        if wp.get(k):
            wp["operator_label"] = wp[k]; break
    # Location: prefer 'location' > 'place' > 'subdivision_name'
    for k in ["location","place","subdivision_name"]:
        if wp.get(k):
            wp["location_label"] = wp[k]; break
    coords = parse_coords(wt)
    if coords: wp["lat"], wp["lon"] = coords
    wp["summary"] = fetch_summary(meta["wp_slug"])
    wp["wikipedia"] = f"https://en.wikipedia.org/wiki/{meta['wp_slug']}"
    img = fetch_image(meta["wp_slug"], slugify(name))
    if img: wp["image"] = img
    meta["wp"] = wp
    meta["slug"] = slugify(name)
    time.sleep(0.4)

# Save enriched dataset
data_file = ROOT / "data" / "mines.json"
data_file.write_text(json.dumps({
    "fetched_at": TODAY,
    "source": "Wikipedia categories (Mines_in_Zimbabwe and commodity-specific subcategories)",
    "count": len(mines),
    "mines": [mines[k] for k in sorted(mines.keys())],
}, indent=2, ensure_ascii=False))
print(f"\nsaved {data_file}")
print(f"  enriched (any WP data):  {sum(1 for m in mines.values() if m['wp'])}")
print(f"  with hero image:         {sum(1 for m in mines.values() if m['wp'].get('image'))}")
print(f"  with coordinates:        {sum(1 for m in mines.values() if m['wp'].get('lat'))}")

# --- News cross-reference ---------------------------------------------------
WIRES = ROOT / "content" / "wires"
news_index = []
if WIRES.exists():
    for p in WIRES.glob("*.md"):
        try: news_index.append((p, p.read_text(errors="ignore").lower()))
        except Exception: pass

def image_for(slug):
    """Return ../img/mining/<slug>.<ext> if a file exists, else None."""
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".svg"):
        p = ROOT / "img" / "mining" / f"{slug}{ext}"
        if p.exists():
            return f"../img/mining/{p.name}"
    return None

def hub_banner_html():
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "img" / "mining" / f"_hero{ext}"
        if p.exists():
            return f'<figure class="mn-hub-img"><div class="mn-hub-img-inner"><img src="/img/mining/_hero{ext}" alt="" loading="eager"></div></figure>'
    return ""

def latest_news(max_n=6):
    """Return latest N wires for the hub Recent News module."""
    out = []
    for p, _text in news_index:
        m = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
        if not m: continue
        title = None
        try:
            parts = p.read_text(errors="ignore").split("---", 2)
            if len(parts) >= 3:
                tm = re.search(r'^title:\s*"?([^"\n]+)"?', parts[1], re.M)
                if tm: title = tm.group(1).strip().rstrip('"')
        except Exception: pass
        if not title:
            title = m.group(2).replace("-", " ").capitalize()
        out.append({"date": m.group(1), "title": title, "file": p.stem})
    out.sort(key=lambda h: h["date"], reverse=True)
    return out[:max_n]

def matching_articles(name, max_n=4):
    needle = name.lower()
    short = needle.replace(" mine","").replace(" minerals","").replace(" colliery","").strip()
    hits = []; seen = set()
    for p, text in news_index:
        if needle in text or (len(short) > 5 and short in text):
            if p.stem in seen: continue
            seen.add(p.stem)
            title = None
            try:
                parts = p.read_text(errors="ignore").split("---", 2)
                if len(parts) >= 3:
                    mm = re.search(r'^title:\s*"?([^"\n]+)"?', parts[1], re.M)
                    if mm: title = mm.group(1).strip()
                if not title:
                    mm = re.search(r'^#\s+(.+)$', parts[-1], re.M)
                    if mm: title = mm.group(1).strip()
            except Exception: pass
            if not title: title = p.stem
            md = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
            if not md: continue
            hits.append({"date": md.group(1), "title": title, "file": p.stem})
    hits.sort(key=lambda h: h["date"], reverse=True)
    return hits[:max_n]

# --- CSS (reuses main-site palette) ----------------------------------------
CSS = """
body { background: #fff !important; }
.mn-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }

/* Hub banner image */
.mn-hub-img { max-width: 1100px; margin: 14px auto 0; padding: 0 20px; }
.mn-hub-img-inner { aspect-ratio: 21/9; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--rule); background: #f0ece4; }
.mn-hub-img-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }
@media (max-width: 640px) { .mn-hub-img-inner { aspect-ratio: 16/9; } }

/* Card hero image */
.mn-card-img { display: block; width: calc(100% + 36px); margin: -18px -18px 14px;
  aspect-ratio: 16/9; object-fit: cover; background: #f0ece4;
  border-bottom: 1px solid var(--rule); }

/* Recent news module (hub footer) */
.mn-news { max-width: 1100px; margin: 32px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.mn-news-h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 16px; letter-spacing: -0.01em; }
.mn-news-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.mn-news-card { display: block; padding: 16px 18px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); transition: border-color 0.15s, transform 0.15s; }
.mn-news-card:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.mn-news-date { font-size: 0.72em; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.mn-news-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1em; line-height: 1.3; color: var(--ink); margin: 0; }
.mn-section-header { padding: 24px 20px 4px; max-width: 1100px; margin: 0 auto; }
.mn-section-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.mn-section-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.mn-section-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1em;
  line-height: 1.55; color: var(--text-mid); margin: 0 0 14px; max-width: 44em; }
.mn-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 8px 0 0; }

.mn-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; max-width: 1100px; margin: 20px auto 8px; padding: 0 20px; }
.mn-stat { padding: 14px 16px; background: var(--paper); border: 1px solid var(--rule); border-radius: 8px; }
.mn-stat-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 4px; font-weight: 600; }
.mn-stat-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.4em;
  line-height: 1.15; color: var(--ink); margin: 0; font-weight: 700; }

.mn-filterbar { max-width: 1100px; margin: 14px auto 0; padding: 0 20px; font-family: 'Inter', system-ui, sans-serif; }
.mn-search { width: 100%; padding: 10px 14px; font-size: 0.95em; font-family: inherit;
  background: #fff; border: 1px solid var(--rule); color: var(--ink); border-radius: 6px; margin: 0 0 10px; }
.mn-search:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
.mn-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.mn-chip { font-size: 0.78em; padding: 5px 12px; background: #f0ece4;
  border: 1px solid var(--rule); color: var(--ink); border-radius: 14px;
  cursor: pointer; user-select: none; font-family: inherit; }
.mn-chip:hover { border-color: var(--ink); }
.mn-chip[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
.mn-clear { font-size: 0.78em; color: var(--text-mid); text-decoration: underline;
  cursor: pointer; background: none; border: 0; padding: 5px 6px; margin-left: 4px; font-family: inherit; }
.mn-clear:hover { color: var(--accent); }
.mn-count { max-width: 1100px; margin: 14px auto 6px; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.82em; color: var(--text-light); }

.mn-grid { display: grid; gap: 14px; padding: 0 20px 24px;
  max-width: 1100px; margin: 8px auto 0;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.mn-card { display: flex; flex-direction: column; gap: 10px;
  padding: 18px; border: 1px solid var(--rule); border-radius: 8px;
  background: #fff; color: var(--text); text-decoration: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.mn-card:hover { border-color: var(--accent); text-decoration: none;
  box-shadow: 0 6px 22px rgba(0,0,0,0.06); transform: translateY(-1px); }
.mn-card-head { display: flex; gap: 12px; align-items: flex-start; }
.mn-card-mark { flex-shrink: 0; width: 44px; height: 44px; border-radius: 8px;
  background: #f0ece4; border: 1px solid var(--rule);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  color: var(--accent); font-size: 1.3em; }
.mn-card-headtext { flex: 1; min-width: 0; }
.mn-card-com { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.06em; color: var(--text-light); margin: 0 0 3px;
  text-transform: uppercase; font-weight: 600; }
.mn-card-name { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.1em; line-height: 1.2; margin: 0; color: var(--ink); }
.mn-card:hover .mn-card-name { color: var(--accent); }
.mn-card-meta { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-mid); margin: 2px 0 0; line-height: 1.45; }
.mn-card-meta strong { color: var(--ink); font-weight: 600; }
.mn-card[hidden] { display: none; }

/* Detail */
.mn-detail-head { max-width: 820px; margin: 0 auto; padding: 28px 20px 12px; }
.mn-detail-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 10px; font-weight: 700; }
.mn-detail-com { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  letter-spacing: 0.08em; color: var(--text-light); text-transform: uppercase;
  margin: 0 0 6px; font-weight: 600; }
.mn-detail-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.9em, 4.4vw, 2.8em); line-height: 1.1; margin: 0 0 12px;
  color: var(--ink); letter-spacing: -0.01em; }
.mn-detail-stand { font-family: 'Inter', system-ui, sans-serif;
  font-size: 1.02em; line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 44em; }
.mn-detail-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 14px 0 0; }

.mn-hero-img { max-width: 1000px; margin: 0 auto 18px; padding: 0 20px; }
.mn-hero-img img { width: 100%; height: auto; max-height: 440px; object-fit: cover;
  border-radius: 8px; border: 1px solid var(--rule); display: block; background: var(--paper); }
.mn-hero-img-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  color: var(--text-light); margin: 6px 0 0; line-height: 1.45; }
.mn-hero-img-cap a { color: var(--text-mid); }

.mn-prose { max-width: 720px; margin: 0 auto; padding: 0 20px; font-family: 'Inter', system-ui, sans-serif; }
.mn-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; line-height: 1.2; margin: 26px 0 10px; color: var(--ink); }
.mn-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.mn-prose ul { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.mn-prose li { margin-bottom: 5px; }
.mn-prose a { color: var(--accent); text-decoration: underline; }
.mn-prose a:hover { color: var(--ink); }
.mn-prose strong { color: var(--ink); }

.mn-profile { display: grid; grid-template-columns: minmax(110px, max-content) 1fr;
  gap: 8px 18px; margin: 10px 0 6px; font-size: 0.95em;
  background: var(--paper); border: 1px solid var(--rule); border-radius: 8px; padding: 14px 18px; }
.mn-profile-row { display: contents; }
.mn-profile dt { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-light);
  font-weight: 700; padding-top: 3px; }
.mn-profile dd { margin: 0; font-family: 'Inter', system-ui, sans-serif; line-height: 1.5; color: var(--ink); }
.mn-profile-credit { font-size: 0.78em; color: var(--text-light); margin: 8px 0 0; }
.mn-profile-credit a { color: var(--text-mid); }
@media (max-width: 540px) {
  .mn-profile { grid-template-columns: 1fr; gap: 2px 0; padding: 12px 14px; }
  .mn-profile dt { padding-top: 10px; }
  .mn-profile-row:first-child dt { padding-top: 0; }
}

.mn-mapwrap { max-width: 1000px; margin: 12px auto 18px; padding: 0 20px; }
.mn-map { width: 100%; aspect-ratio: 16/9; border: 1px solid var(--rule);
  border-radius: 8px; background: var(--paper); display: block; overflow: hidden; }
.mn-map iframe { width: 100%; height: 100%; border: 0; display: block; }
.mn-map-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-light); margin: 6px 0 0; }
.mn-map-cap a { color: var(--text-mid); }

.mn-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.mn-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700; font-family: inherit; }
.mn-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55; color: var(--text); }
.mn-sources a { color: var(--ink); text-decoration: underline; }
.mn-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }

.mn-back { text-align: center; margin: 24px 0 40px; font-family: 'Inter', system-ui, sans-serif; }
.mn-back a { font-size: 0.88em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }
.mn-back a:hover { color: var(--accent); }
"""

HEAD_COMMON = """    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="../site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="../icon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="../css/normalize.css">
    <link rel="stylesheet" href="../css/main.css?v=102">
    <link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../img/favicon-16x16.png">
    <meta name="theme-color" content="#1a1a1a">
    <meta name="author" content="The Mutapa Times">
    <meta name="twitter:site" content="@mutapatimes">
    <meta name="twitter:card" content="summary_large_image">"""

TOPBAR = """<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>"""

FOOTER = """<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/">News</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/mining/">Mining</a><span class="sep">·</span>
      <a href="/schools/">Schools</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
      <a href="/moving-to-zimbabwe/">UK guide</a><span class="sep">·</span>
      <a href="/authors/">Masthead</a><span class="sep">·</span>
      <a href="/privacy">Privacy</a><span class="sep">·</span>
      <a href="/terms">Terms</a><span class="sep">·</span>
      <a href="mailto:news@mutapatimes.com">Contact</a>
    </div>
    <p class="atlantic-foot-copy">&copy; 2020&ndash;2026 The Mutapa Times. All rights reserved. Operated from the United Kingdom.</p>
  </div>
</footer>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XQPRFK7JTB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XQPRFK7JTB');
</script>"""

# --- Render -----------------------------------------------------------------
def render_hub(mines_list):
    total = len(mines_list)
    commodities = sorted({m["commodity"] for m in mines_list})
    by_commodity = {}
    for m in mines_list:
        by_commodity.setdefault(m["commodity"], []).append(m)

    stats = [
        ("Mines listed", str(total)),
        ("Commodities", str(len(commodities))),
        ("Gold mines", str(len(by_commodity.get("Gold", [])))),
        ("Lithium &amp; PGM", str(len(by_commodity.get("Lithium", [])) + len(by_commodity.get("Platinum group", [])))),
    ]
    stats_html = "\n".join(
        f'    <div class="mn-stat"><p class="mn-stat-label">{lbl}</p><p class="mn-stat-value">{val}</p></div>'
        for lbl, val in stats)

    chips = [f'<button class="mn-chip" data-filter="{html.escape(c.lower())}" aria-pressed="false">{html.escape(c)} ({len(by_commodity[c])})</button>'
             for c in commodities]
    chips.append('<button class="mn-clear" id="mnClear">Clear</button>')

    cards = []
    for m in mines_list:
        operator = m["wp"].get("operator_label", "")
        location = m["wp"].get("location_label", "")
        meta_bits = []
        if operator: meta_bits.append(f"<strong>{html.escape(operator)}</strong>")
        if location: meta_bits.append(html.escape(location))
        meta_html = (' <p class="mn-card-meta">' + " &middot; ".join(meta_bits) + "</p>") if meta_bits else ''
        initial = next((ch for ch in m["name"] if ch.isalpha()), "?").upper()
        # Hero image: prefer user-uploaded, fall back to WP-fetched
        img_path = image_for(m["slug"])
        if not img_path and m["wp"].get("image", {}).get("local"):
            img_path = ".." + m["wp"]["image"]["local"]
        img_html = f'<img class="mn-card-img" src="{img_path}" alt="{html.escape(m["name"])}" loading="lazy">' if img_path else ""
        cards.append(
f'''    <a class="mn-card" href="./{m["slug"]}.html"
       data-name="{html.escape(m["name"].lower())}"
       data-com="{html.escape(m["commodity"].lower())}">
      {img_html}
      <div class="mn-card-head">
        <div class="mn-card-mark" aria-hidden="true">{html.escape(initial)}</div>
        <div class="mn-card-headtext">
          <p class="mn-card-com">{html.escape(m["commodity"])}</p>
          <h3 class="mn-card-name">{html.escape(m["name"])}</h3>
        </div>
      </div>{meta_html}
    </a>''')
    cards_html = "\n".join(cards)

    # Recent news cards for the hub
    recent = latest_news(6)
    recent_news_html = "\n".join(
        f'      <a class="mn-news-card" href="/articles/{n["file"]}.html"><p class="mn-news-date">{n["date"]}</p><h3 class="mn-news-title">{html.escape(n["title"])}</h3></a>'
        for n in recent
    ) if recent else '      <p style="color:var(--text-light)">No recent stories.</p>'

    title = "Zimbabwe mining directory: gold, platinum, lithium, diamond mines"
    desc = (f"All {total} major mines in Zimbabwe — by commodity (gold, "
            "platinum group, lithium, diamond, nickel, coal, iron), with "
            "operator, location and our latest mining coverage.")

    ld_page = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title, "description": desc,
        "url":"https://www.mutapatimes.com/mining/", "inLanguage":"en",
        "publisher":{"@type":"Organization","name":"The Mutapa Times",
                     "logo":{"@type":"ImageObject","url":"https://www.mutapatimes.com/img/logo.png"}}
    }, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Mining directory","item":"https://www.mutapatimes.com/mining/"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(title)} | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/mining/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://www.mutapatimes.com/mining/">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(title)}">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_page}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="mn-section-header">
    <p class="mn-section-eyebrow">Mutapa Times &middot; Mining</p>
    <h1 class="mn-section-title">Zimbabwe mining directory</h1>
    <p class="mn-section-stand">Zimbabwe is one of Africa's most concentrated
      mining geographies &mdash; significant in gold, platinum group metals,
      lithium and diamond. This directory tracks {total} of its named mines and
      operations, by commodity, with operator and location. Click any entry
      for the full profile.</p>
    <hr class="mn-rule">
  </header>
  {hub_banner_html()}
  <div class="mn-stats" role="list">
{stats_html}
  </div>
  <div class="mn-filterbar">
    <input type="search" class="mn-search" id="mnSearch"
           placeholder="Search by mine or operator…" aria-label="Search mines">
    <div class="mn-chips" role="group" aria-label="Filter by commodity">
      {chr(10).join("      " + c for c in chips)}
    </div>
  </div>
  <p class="mn-count" id="mnCount" aria-live="polite">Showing all {total} mines.</p>
  <div class="mn-grid" id="mnGrid">
{cards_html}
  </div>
  <section class="mn-news" aria-label="Latest from The Mutapa Times">
    <h2 class="mn-news-h2">Latest from The Mutapa Times</h2>
    <div class="mn-news-grid">
{recent_news_html}
    </div>
  </section>
  <section class="mn-sources" aria-label="About this directory">
    <h2>About this directory</h2>
    <ul>
      <li>Mine roster is drawn from Wikipedia categories (<a href="https://en.wikipedia.org/wiki/Category:Mines_in_Zimbabwe" rel="noopener" target="_blank">Mines in Zimbabwe</a> and commodity-specific subcategories) plus a hand-curated list of major commercial operations.</li>
      <li>Operator, location, opened/closed dates and coordinates are taken from each mine's Wikipedia infobox where available.</li>
      <li>This is editorial reference. Production figures and ownership change &mdash; verify directly with the operator before commercial decisions.</li>
    </ul>
    <p class="mn-sources-note">Last reviewed {TODAY}. Spot an error or a missing mine? Email <a href="mailto:news@mutapatimes.com?subject=Mining%20directory%20update">news@mutapatimes.com</a>.</p>
  </section>
</main>
{FOOTER}
<script>
(function(){{
  var grid = document.getElementById('mnGrid');
  var cards = Array.from(grid.querySelectorAll('.mn-card'));
  var search = document.getElementById('mnSearch');
  var chips = Array.from(document.querySelectorAll('.mn-chip'));
  var clear = document.getElementById('mnClear');
  var countEl = document.getElementById('mnCount');
  var total = cards.length;
  var active = new Set();
  function apply(){{
    var q = (search.value||'').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){{
      var n = c.dataset.name||'', co = c.dataset.com||'';
      var matchQ = !q || n.indexOf(q) !== -1 || co.indexOf(q) !== -1;
      var matchC = !active.size || active.has(co);
      var ok = matchQ && matchC;
      c.hidden = !ok; if (ok) shown++;
    }});
    countEl.textContent = (q || active.size) ? ('Showing ' + shown + ' of ' + total + ' mines.') : ('Showing all ' + total + ' mines.');
  }}
  search.addEventListener('input', apply);
  chips.forEach(function(c){{
    c.addEventListener('click', function(){{
      var f = c.dataset.filter;
      if (active.has(f)) {{ active.delete(f); c.setAttribute('aria-pressed','false'); }}
      else                {{ active.add(f);    c.setAttribute('aria-pressed','true'); }}
      apply();
    }});
  }});
  clear.addEventListener('click', function(){{
    search.value=''; active.clear();
    chips.forEach(function(c){{ c.setAttribute('aria-pressed','false'); }});
    apply();
  }});
}})();
</script>
</body>
</html>
'''
    return out

def render_detail(m):
    wp = m["wp"]
    name = m["name"]
    commodity = m["commodity"]
    slug = m["slug"]

    # Profile facts
    profile_facts = []
    LBLS = [
        ("operator_label", "Operator"),
        ("location_label", "Location"),
        ("opened",         "Opened"),
        ("closed",         "Closed"),
        ("discovered",     "Discovered"),
        ("active_years",   "Active years"),
        ("products",       "Products"),
        ("type",           "Mine type"),
        ("depth",          "Depth"),
        ("greatest_depth", "Greatest depth"),
        ("employees",      "Employees"),
        ("financial_year", "Financial year"),
        ("production",     "Production"),
        ("province",       "Province"),
        ("district",       "District"),
        ("website",        "Website"),
    ]
    for k, lbl in LBLS:
        v = wp.get(k)
        if v: profile_facts.append((lbl, v))

    summary = (wp.get("summary") or "").strip()
    if len(summary) > 700:
        summary = summary[:700].rsplit(".", 1)[0] + "."
    summary_html = f"<p>{html.escape(summary)}</p>" if summary else ""

    profile_html = ""
    if profile_facts or summary:
        rows = "\n".join(f'        <div class="mn-profile-row"><dt>{html.escape(lbl)}</dt><dd>{html.escape(val)}</dd></div>' for lbl, val in profile_facts)
        credit = f'<p class="mn-profile-credit">Profile data: <a href="{wp.get("wikipedia")}" rel="noopener" target="_blank">Wikipedia</a>. Figures may be out of date &mdash; verify with operator.</p>' if wp.get("wikipedia") else ""
        profile_dl = ('<dl class="mn-profile">\n' + rows + '\n    </dl>') if profile_facts else ""
        profile_html = f'''    <h2>Mine profile</h2>
{summary_html}
    {profile_dl}
    {credit}'''

    # Hero image
    img = wp.get("image") or {}
    hero_html = ""
    if img.get("local"):
        att = []
        if img.get("artist"): att.append(html.escape(img["artist"]))
        if img.get("license"): att.append(html.escape(img["license"]))
        att_html = " &middot; ".join(att) if att else "Wikimedia Commons"
        hero_html = f'''<figure class="mn-hero-img">
  <img src="..{img["local"]}" alt="{html.escape(name)}" loading="eager">
  <figcaption class="mn-hero-img-cap">Photo: <a href="{img["commons_page"]}" rel="noopener" target="_blank">Wikimedia Commons</a> &middot; {att_html}</figcaption>
</figure>'''

    # Map
    map_html = ""
    if wp.get("lat") and wp.get("lon"):
        lat, lon = wp["lat"], wp["lon"]
        pad = 0.02
        bbox = f"{lon-pad},{lat-pad},{lon+pad},{lat+pad}"
        osm = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&layer=mapnik&marker={lat},{lon}"
        osm_link = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}"
        map_html = f'''<div class="mn-mapwrap">
  <div class="mn-map"><iframe loading="lazy" src="{osm}" title="Map of {html.escape(name)}"></iframe></div>
  <p class="mn-map-cap">Map: OpenStreetMap. <a href="{osm_link}" rel="noopener" target="_blank">Open full map</a>.</p>
</div>'''

    # News
    arts = matching_articles(name, max_n=5)
    rel_html = ""
    if arts:
        items = "\n".join(
            f'        <li><a href="/articles/{a["file"]}.html">{html.escape(a["title"])}</a> <span style="color:var(--text-light)">&mdash; {a["date"]}</span></li>'
            for a in arts)
        rel_html = f'''    <h2>Recent coverage</h2>
    <ul>
{items}
    </ul>'''

    operator_phrase = f" operated by {html.escape(wp['operator_label'])}" if wp.get("operator_label") else ""
    stand = (f"{html.escape(name)} is a {html.escape(commodity.lower())} mine in Zimbabwe"
             f"{operator_phrase}. " + (html.escape(summary[:140]) + "…" if summary and len(summary) > 140 else ""))

    desc = f"{name}: {commodity} mine in Zimbabwe. Operator, location, history and our latest coverage."

    ld = {
        "@context":"https://schema.org","@type":"Place",
        "name": name,
        "url": f"https://www.mutapatimes.com/mining/{slug}.html",
        "description": f"{commodity} mine in Zimbabwe.",
    }
    if wp.get("lat") and wp.get("lon"):
        ld["geo"] = {"@type":"GeoCoordinates","latitude": wp["lat"], "longitude": wp["lon"]}
    if wp.get("location_label"):
        ld["address"] = {"@type":"PostalAddress","addressLocality": wp["location_label"], "addressCountry":"ZW"}
    ld_json = json.dumps(ld, ensure_ascii=False)

    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Mining directory","item":"https://www.mutapatimes.com/mining/"},
            {"@type":"ListItem","position":3,"name": name,"item": f"https://www.mutapatimes.com/mining/{slug}.html"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(name)} — {html.escape(commodity)} mine, Zimbabwe | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/mining/{slug}.html">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(name)} — {html.escape(commodity)} mine">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://www.mutapatimes.com/mining/{slug}.html">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(name)} — {html.escape(commodity)} mine">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_json}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="mn-detail-head">
    <p class="mn-detail-eyebrow"><a href="./" style="color:inherit;text-decoration:none">Mining directory</a> &middot; {html.escape(commodity)}</p>
    <h1 class="mn-detail-title">{html.escape(name)}</h1>
    <p class="mn-detail-stand">{stand}</p>
    <hr class="mn-detail-rule">
  </header>
  {hero_html}
  <div class="mn-prose">
{profile_html}
{rel_html}
    <h2>About this profile</h2>
    <p>Data here is drawn from the Wikipedia article for {html.escape(name)}
      and our own news archive. Ownership, production figures and operational
      status change frequently in the Zimbabwean mining sector;
      <strong>verify directly with the operator before any commercial
      decision</strong>.</p>
  </div>
  {map_html}
  <section class="mn-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      {('<li><a href="' + wp["wikipedia"] + '" rel="noopener" target="_blank">Wikipedia &mdash; ' + html.escape(name) + '</a> (profile, infobox, history)</li>') if wp.get("wikipedia") else ''}
      <li><a href="https://en.wikipedia.org/wiki/Category:Mines_in_Zimbabwe" rel="noopener" target="_blank">Wikipedia &mdash; Mines in Zimbabwe (category)</a></li>
    </ul>
    <p class="mn-sources-note">Last reviewed {TODAY}. Editorial — The Mutapa Times receives no payment from any mine operator.</p>
  </section>
  <p class="mn-back"><a href="./">&larr; Back to mining directory</a></p>
</main>
{FOOTER}
</body>
</html>
'''
    return out

mines_list = sorted(mines.values(), key=lambda m: m["name"].lower())
hub_html = render_hub(mines_list)
(OUT / "index.html").write_text(hub_html)
print(f"wrote {OUT / 'index.html'} ({len(hub_html):,} bytes)")
for m in mines_list:
    (OUT / f"{m['slug']}.html").write_text(render_detail(m))
print(f"wrote {len(mines_list)} detail pages")
