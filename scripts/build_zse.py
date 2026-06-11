#!/usr/bin/env python3
"""Scrape the ZSE listed-companies table from african-markets, enrich with
Wikipedia data, generate /zse/ microsite. Mirrors the /schools/ pattern."""
import json, re, html, urllib.request, time
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT  = ROOT / "zse"
OUT.mkdir(exist_ok=True)
DATA = ROOT / "data" / "zse-companies.json"
IMG_DIR = ROOT / "img" / "zse"
IMG_DIR.mkdir(parents=True, exist_ok=True)

UA = "MutapaTimes/1.0 (https://mutapatimes.com; news@mutapatimes.com)"
TODAY = "2026-05-22"

# --- Scrape -----------------------------------------------------------------

def scrape_african_markets():
    url = "https://www.african-markets.com/en/stock-markets/zse/listed-companies"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, timeout=25) as r:
        h = r.read().decode("utf-8", errors="replace")
    tables = re.findall(r'<table[^>]*>(.*?)</table>', h, re.S)
    target = max(tables, key=lambda t: len(re.findall(r'<tr', t)))
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', target, re.S)
    out = []
    for r in rows[2:]:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)
        cleaned = [re.sub(r'<[^>]+>', '', c).replace('&nbsp;', ' ').strip() for c in cells]
        if len(cleaned) < 7 or not cleaned[0]:
            continue
        # Columns: Company, Sector, Price, 1D, YTD, MCap, Date
        company, sector, price, day, ytd, mcap, date = cleaned[:7]
        out.append({
            "company": company,
            "sector": sector,
            "price": price,
            "day_change": day if day != "-" else "",
            "ytd": ytd if ytd != "-" else "",
            "mcap_b": mcap if mcap != "-" else "",
            "data_date": date,
        })
    return out

# --- Slugify ----------------------------------------------------------------
def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s

# --- Wikipedia mapping ------------------------------------------------------
# Hand-curated to avoid false matches (e.g. "Delta Corporation" → US company)
WP_MAP = {
    "African Distillers":            "African_Distillers",
    "British American Tobacco Zimbabwe": "British_American_Tobacco_Zimbabwe",
    "CBZ Holdings":                  "CBZ_Holdings",
    "Delta Corporation":             "Delta_Corporation",
    "Dairibord Holdings":            "Dairibord_Holdings",
    "FBC Holdings":                  "FBC_Holdings",
    "Hippo Valley Estates":          "Hippo_Valley_Estates",
    "Hwange Colliery Company":       "Hwange_Colliery_Company",
    "Lafarge Cement Zimbabwe":       "Lafarge_Cement_Zimbabwe",
    "Meikles":                       "Meikles_Limited",
    "NMBZ Holdings":                 "NMB_Bank_Zimbabwe",
    "OK Zimbabwe":                   "OK_Zimbabwe",
    "Old Mutual":                    "Old_Mutual",
    "RioZim":                        "RioZim",
    "Rainbow Tourism Group":         "Rainbow_Tourism_Group",
    "Seed Co":                       "Seed_Co",
    "Tanganda Tea Company":          "Tanganda_Tea_Company",
    "Zimbabwe Newspapers (1980)":    "Zimbabwe_Newspapers",
    "Zimre Holdings":                "Zimre_Holdings",
    "Border Timbers":                "Border_Timbers",
    "Cafca":                         "CAFCA",
    "ART Corporation":               "Amalgamated_Regional_Trading",
    "Ariston Holdings":              "Ariston_Holdings",
    "Astra Industries":              "Astra_Industries",
    "Mashonaland Holdings":          "Mashonaland_Holdings",
    "First Mutual Holdings":         "First_Mutual_Holdings",
    "Fidelity Life Assurance":       "Fidelity_Life_Assurance_of_Zimbabwe",
    "Pretoria Portland Cement":      "PPC_Ltd",
    "Proplastics":                   "Proplastics",
    "Masimba Holdings":              "Masimba_Holdings",
    "ZB Financial Holdings":         "ZB_Financial_Holdings",
    "Nampak Zimbabwe":               "Nampak",
    "TSL":                           "TSL_Limited",
    "Tigere Property Fund":          "Tigere_Property_Fund",
    "Willdale":                      "Willdale_Limited",
    "Starafrica Corporation":        "Starafrica_Corporation",
    "COTTCO Holdings":               "Cotton_Company_of_Zimbabwe",
    "CFI Holdings":                  "CFI_Holdings",
    "Unifreight Africa":             "Unifreight",
    "Dawn Properties":               "Dawn_Properties",
}

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def http_download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read())

# infobox parser identical to school enricher
def fetch_wikitext(title):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&prop=wikitext&format=json&redirects=1"
    try:
        j = http_get_json(url)
        return j.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception as e:
        return ""

def parse_infobox(wt):
    """Two-char lookahead. Old per-char tracker over-counted }}}}."""
    m = re.search(r'\{\{Infobox[^\|]*\|', wt, re.I)
    if not m: return {}
    start = m.start(); depth = 0; i = start
    while i < len(wt):
        if wt[i:i+2] == '{{': depth += 1; i += 2; continue
        if wt[i:i+2] == '}}':
            depth -= 1; i += 2
            if depth == 0: break
            continue
        i += 1
    inner = wt[start+2:i-2]
    parts = []; cur = []
    td = ld = 0; j = 0
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
    v = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', v)
    v = re.sub(r'\[\[([^\]]+)\]\]', r'\1', v)
    v = re.sub(r"'''([^']+)'''", r'\1', v)
    v = re.sub(r"''([^']+)''", r'\1', v)
    prev = None
    while prev != v:
        prev = v
        v = re.sub(r'\{\{[^{}]*\}\}', '', v)
    v = re.sub(r'<br\s*/?>', '; ', v, flags=re.I)
    v = re.sub(r'<[^>]+>', '', v)
    v = re.sub(r'\s+', ' ', v).strip()
    return v.strip(' ;,.')

def fetch_summary(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    try:
        return http_get_json(url).get("extract", "")
    except Exception:
        return ""

FREE_LICENSE_RE = re.compile(
    r"\b(CC[ -]?BY(?:[ -]?SA)?(?:[ -]?\d(?:\.\d)?)?|CC0|Public[ ]?domain|PDM|GFDL|OGL)\b", re.I)
NONFREE_RE = re.compile(r"\bfair[ -]?use\b|\bnon[- ]?free\b", re.I)

def fetch_image_meta(title, slug):
    """Return (local_path, meta) for free-licensed lead image, or (None, None)."""
    url = (f"https://en.wikipedia.org/w/api.php?action=query"
           f"&titles={title}&prop=pageimages&piprop=name&format=json&redirects=1")
    try:
        j = http_get_json(url)
    except Exception:
        return None, None
    page = next(iter(j.get("query", {}).get("pages", {}).values()), {})
    fname = page.get("pageimage")
    if not fname: return None, None
    file_title = "File:" + fname
    url2 = (f"https://en.wikipedia.org/w/api.php?action=query"
            f"&titles={urllib.parse.quote(file_title)}"
            f"&prop=imageinfo&iiprop=url|extmetadata|mime&format=json&redirects=1")
    try:
        j2 = http_get_json(url2)
    except Exception:
        return None, None
    info_page = next(iter(j2.get("query", {}).get("pages", {}).values()), {})
    infos = info_page.get("imageinfo")
    if not infos: return None, None
    info = infos[0]
    meta = info.get("extmetadata") or {}
    short = (meta.get("LicenseShortName") or {}).get("value", "")
    usage = (meta.get("UsageTerms") or {}).get("value", "")
    artist = re.sub(r'<[^>]+>', '', (meta.get("Artist") or {}).get("value", "")).strip()
    license_text = short + " " + usage
    if not FREE_LICENSE_RE.search(license_text): return None, None
    if NONFREE_RE.search(license_text): return None, None
    src = info.get("url", "")
    mime = info.get("mime", "")
    ext = ".jpg"
    if "png" in mime: ext = ".png"
    elif "svg" in mime: ext = ".svg"
    elif "webp" in mime: ext = ".webp"
    local = IMG_DIR / f"{slug}{ext}"
    try:
        http_download(src, local)
    except Exception:
        return None, None
    return f"/img/zse/{local.name}", {
        "filename": fname, "license": short, "artist": artist,
        "commons_page": f"https://commons.wikimedia.org/wiki/{file_title.replace(' ','_')}",
        "local": f"/img/zse/{local.name}",
    }

import urllib.parse

INFOBOX_KEYS = ["founded","founder","headquarters","industry","sector",
                "key_people","products","revenue","operating_income","net_income",
                "assets","equity","employees","subsid","parent","website","traded_as",
                "isin","predecessor"]

def enrich(name):
    title = WP_MAP.get(name)
    if not title: return {}
    wt = fetch_wikitext(title)
    if not wt: return {}
    ib = parse_infobox(wt)
    out = {}
    for k in INFOBOX_KEYS:
        if k in ib:
            cv = clean_val(ib[k])
            if cv: out[k] = cv
    out["summary"] = fetch_summary(title)
    out["wikipedia"] = f"https://en.wikipedia.org/wiki/{title}"
    slug = slugify(name)
    local, meta = fetch_image_meta(title, slug)
    if meta: out["image"] = meta
    return out

# --- News cross-reference ---------------------------------------------------
WIRES = ROOT / "content" / "wires"
news_index = []
if WIRES.exists():
    for p in WIRES.glob("*.md"):
        try:
            news_index.append((p, p.read_text(errors="ignore").lower()))
        except Exception: pass

def hub_banner_html():
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "img" / "zse" / f"_hero{ext}"
        if p.exists():
            return f'<figure class="zse-hub-img"><div class="zse-hub-img-inner"><img src="/img/zse/_hero{ext}" alt="" loading="eager"></div></figure>'
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

def matching_articles(name, alt_names, max_n=4):
    needles = [name.lower()]
    needles.extend(a.lower() for a in alt_names if a)
    hits = []
    seen_files = set()
    for p, text in news_index:
        if any(n in text for n in needles):
            if p.stem in seen_files: continue
            seen_files.add(p.stem)
            title = None
            try:
                parts = p.read_text(errors="ignore").split("---", 2)
                if len(parts) >= 3:
                    m = re.search(r'^title:\s*"?([^"\n]+)"?', parts[1], re.M)
                    if m: title = m.group(1).strip()
                if not title:
                    m = re.search(r'^#\s+(.+)$', parts[-1], re.M)
                    if m: title = m.group(1).strip()
            except Exception: pass
            if not title: title = p.stem
            md = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
            if not md: continue
            hits.append({"date": md.group(1), "title": title, "file": p.stem})
    hits.sort(key=lambda h: h["date"], reverse=True)
    return hits[:max_n]

# --- Build ------------------------------------------------------------------

print("Scraping african-markets ZSE listed-companies…")
companies = scrape_african_markets()
print(f"  -> {len(companies)} entries scraped")

for c in companies:
    c["slug"] = slugify(c["company"])

print("Enriching with Wikipedia (mapped entries only)…")
for c in companies:
    if c["company"] in WP_MAP:
        print(f"  - {c['company']}")
        c["wp"] = enrich(c["company"])
        time.sleep(0.5)
    else:
        c["wp"] = {}

dataset = {
    "fetched_at": TODAY,
    "source": "https://www.african-markets.com/en/stock-markets/zse/listed-companies",
    "exchange": "Zimbabwe Stock Exchange",
    "currency": "ZWG",
    "count": len(companies),
    "companies": companies,
}
DATA.write_text(json.dumps(dataset, indent=2, ensure_ascii=False))
print(f"saved {DATA}")
print(f"  Wikipedia-enriched: {sum(1 for c in companies if c['wp'])}")
print(f"  with hero image:    {sum(1 for c in companies if c['wp'].get('image'))}")

# --- CSS (reuses main-site palette, matches /schools/) ---------------------
CSS = """
body { background: #fff !important; }
.zse-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }

/* Hub banner image */
.zse-hub-img { max-width: 1100px; margin: 14px auto 0; padding: 0 20px; }
.zse-hub-img-inner { aspect-ratio: 21/9; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--rule); background: #f0ece4; }
.zse-hub-img-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }
@media (max-width: 640px) { .zse-hub-img-inner { aspect-ratio: 16/9; } }

/* Recent news module (hub footer) */
.zse-news { max-width: 1100px; margin: 32px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.zse-news-h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 16px; letter-spacing: -0.01em; }
.zse-news-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.zse-news-card { display: block; padding: 16px 18px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); transition: border-color 0.15s, transform 0.15s; }
.zse-news-card:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.zse-news-date { font-size: 0.72em; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.zse-news-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1em; line-height: 1.3; color: var(--ink); margin: 0; }
.zse-section-header { padding: 24px 20px 4px; max-width: 1100px; margin: 0 auto; }
.zse-section-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.zse-section-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.zse-section-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1em;
  line-height: 1.55; color: var(--text-mid); margin: 0 0 14px; max-width: 44em; }
.zse-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 8px 0 0; }

.zse-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; max-width: 1100px; margin: 20px auto 8px; padding: 0 20px; }
.zse-stat { padding: 14px 16px; background: var(--paper); border: 1px solid var(--rule);
  border-radius: 8px; }
.zse-stat-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 4px; font-weight: 600; }
.zse-stat-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.4em;
  line-height: 1.15; color: var(--ink); margin: 0; font-weight: 700; }

.zse-filterbar { max-width: 1100px; margin: 14px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.zse-search { width: 100%; padding: 10px 14px; font-size: 0.95em;
  font-family: inherit; background: #fff; border: 1px solid var(--rule);
  color: var(--ink); border-radius: 6px; margin: 0 0 10px; }
.zse-search:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
.zse-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.zse-chip { font-size: 0.78em; padding: 5px 12px; background: #f0ece4;
  border: 1px solid var(--rule); color: var(--ink); border-radius: 14px;
  cursor: pointer; user-select: none; font-family: inherit; }
.zse-chip:hover { border-color: var(--ink); }
.zse-chip[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
.zse-clear { font-size: 0.78em; color: var(--text-mid); text-decoration: underline;
  cursor: pointer; background: none; border: 0; padding: 5px 6px; margin-left: 4px;
  font-family: inherit; }
.zse-clear:hover { color: var(--accent); }
.zse-count { max-width: 1100px; margin: 14px auto 6px; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.82em; color: var(--text-light); }

/* Table view */
.zse-tablewrap { max-width: 1100px; margin: 8px auto 4px; padding: 0 20px;
  overflow-x: auto; }
.zse-table { width: 100%; border-collapse: collapse; font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.92em; background: #fff; border: 1px solid var(--rule); border-radius: 8px;
  overflow: hidden; }
.zse-table thead th { text-align: left; padding: 10px 14px; background: var(--paper);
  border-bottom: 1px solid var(--rule); font-size: 0.72em; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-light); cursor: pointer; user-select: none;
  white-space: nowrap; }
.zse-table thead th[aria-sort]::after { content: ' ⇅'; opacity: 0.4; font-size: 0.85em; }
.zse-table thead th[aria-sort="ascending"]::after  { content: ' ↑'; opacity: 1; color: var(--accent); }
.zse-table thead th[aria-sort="descending"]::after { content: ' ↓'; opacity: 1; color: var(--accent); }
.zse-table tbody td { padding: 10px 14px; border-bottom: 1px solid var(--rule);
  color: var(--text); }
.zse-table tbody tr:last-child td { border-bottom: 0; }
.zse-table tbody tr:hover { background: var(--paper); }
.zse-table a { color: var(--ink); text-decoration: none; font-weight: 600; }
.zse-table a:hover { color: var(--accent); }
.zse-table .num { font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.zse-table .pos { color: #1f7a3e; }
.zse-table .neg { color: var(--accent); }
.zse-table .sect { font-size: 0.75em; padding: 2px 8px; background: #f0ece4;
  color: var(--ink); border-radius: 10px; white-space: nowrap; }
.zse-table tr[hidden] { display: none; }
@media (max-width: 640px) {
  .zse-table thead th, .zse-table tbody td { padding: 8px 10px; font-size: 0.85em; }
  .zse-table .sect { display: none; }
}

/* Per-company detail */
.zse-detail-head { max-width: 820px; margin: 0 auto; padding: 28px 20px 12px; }
.zse-detail-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 10px; font-weight: 700; }
.zse-detail-sect { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  letter-spacing: 0.08em; color: var(--text-light); text-transform: uppercase;
  margin: 0 0 6px; font-weight: 600; }
.zse-detail-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.9em, 4.4vw, 2.8em); line-height: 1.1; margin: 0 0 12px;
  color: var(--ink); letter-spacing: -0.01em; }
.zse-detail-stand { font-family: 'Inter', system-ui, sans-serif;
  font-size: 1.02em; line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 44em; }
.zse-detail-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 14px 0 0; }

.zse-pricerow { max-width: 1000px; margin: 18px auto 24px; padding: 0 20px;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
.zse-pricecell { background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 14px 16px; }
.zse-pricecell-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  font-weight: 600; margin: 0 0 4px; }
.zse-pricecell-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.35em;
  font-weight: 700; color: var(--ink); margin: 0; line-height: 1.15; font-variant-numeric: tabular-nums; }
.zse-pricecell-value.pos { color: #1f7a3e; }
.zse-pricecell-value.neg { color: var(--accent); }

.zse-hero-img { max-width: 1000px; margin: 0 auto 18px; padding: 0 20px; }
.zse-hero-img img { width: 100%; height: auto; max-height: 440px; object-fit: cover;
  border-radius: 8px; border: 1px solid var(--rule); display: block; background: var(--paper); }
.zse-hero-img-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  color: var(--text-light); margin: 6px 0 0; line-height: 1.45; }
.zse-hero-img-cap a { color: var(--text-mid); }

.zse-prose { max-width: 720px; margin: 0 auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.zse-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; line-height: 1.2; margin: 26px 0 10px; color: var(--ink); }
.zse-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.zse-prose ul { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.zse-prose li { margin-bottom: 5px; }
.zse-prose a { color: var(--accent); text-decoration: underline; }
.zse-prose a:hover { color: var(--ink); }
.zse-prose strong { color: var(--ink); }

.zse-profile { display: grid; grid-template-columns: minmax(110px, max-content) 1fr;
  gap: 8px 18px; margin: 10px 0 6px; font-size: 0.95em;
  background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 14px 18px; }
.zse-profile-row { display: contents; }
.zse-profile dt { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-light);
  font-weight: 700; padding-top: 3px; }
.zse-profile dd { margin: 0; font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.5; color: var(--ink); }
.zse-profile-credit { font-size: 0.78em; color: var(--text-light); margin: 8px 0 0; }
.zse-profile-credit a { color: var(--text-mid); }
@media (max-width: 540px) {
  .zse-profile { grid-template-columns: 1fr; gap: 2px 0; padding: 12px 14px; }
  .zse-profile dt { padding-top: 10px; }
  .zse-profile-row:first-child dt { padding-top: 0; }
}

.zse-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.zse-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700; font-family: inherit; }
.zse-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55;
  color: var(--text); }
.zse-sources a { color: var(--ink); text-decoration: underline; }
.zse-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }

.zse-back { text-align: center; margin: 24px 0 40px; font-family: 'Inter', system-ui, sans-serif; }
.zse-back a { font-size: 0.88em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }
.zse-back a:hover { color: var(--accent); }
"""

HEAD_COMMON = """    <meta charset="utf-8">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4428529474445353" crossorigin="anonymous"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="../site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="../icon.png?v=2">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="../css/normalize.css">
    <link rel="stylesheet" href="../css/main.css?v=102">
    <link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32x32.png?v=2">
    <link rel="icon" type="image/png" sizes="16x16" href="../img/favicon-16x16.png?v=2">
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
      <a href="/schools/">Schools directory</a><span class="sep">·</span>
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

def fmt_num(s):
    if not s: return ""
    try:
        f = float(s)
        if f >= 100: return f"{f:,.2f}"
        if f >= 1: return f"{f:.4f}".rstrip("0").rstrip(".")
        return f"{f:.6f}".rstrip("0").rstrip(".")
    except Exception:
        return s

def sign_class(s):
    if not s: return ""
    if s.startswith("+"): return "pos"
    if s.startswith("-"): return "neg"
    return ""

# --- Hub --------------------------------------------------------------------
def render_hub():
    sectors = sorted({c["sector"] for c in companies if c["sector"]})
    total = len(companies)
    listed = sum(1 for c in companies if c["sector"] != "ETF")
    etfs = sum(1 for c in companies if c["sector"] == "ETF")
    finals = [c for c in companies if c["mcap_b"]]
    total_mcap = 0.0
    for c in finals:
        try: total_mcap += float(c["mcap_b"])
        except Exception: pass

    # Stats
    stats = [
        ("Listed equities", str(listed)),
        ("ETFs &amp; REITs", str(total - listed)),
        ("Sectors", str(len(sectors))),
        ("Combined market cap", f"ZWG {total_mcap:,.1f}B"),
    ]
    stats_html = "\n".join(
        f'    <div class="zse-stat"><p class="zse-stat-label">{lbl}</p><p class="zse-stat-value">{val}</p></div>'
        for lbl, val in stats)

    # Chips
    chips = []
    for s in sectors:
        chips.append(f'<button class="zse-chip" data-filter="{html.escape(s.lower())}" aria-pressed="false">{html.escape(s)}</button>')
    chips.append('<button class="zse-clear" id="zseClear">Clear</button>')

    # Rows
    rows = []
    for c in companies:
        ytd_cls = sign_class(c["ytd"])
        day_cls = sign_class(c["day_change"])
        mcap = f"{float(c['mcap_b']):,.2f}" if c["mcap_b"] else ""
        try: mcap_sort = float(c["mcap_b"]) if c["mcap_b"] else 0
        except Exception: mcap_sort = 0
        try: ytd_sort = float(c["ytd"].rstrip("%").replace("+","")) if c["ytd"] else 0
        except Exception: ytd_sort = 0
        try: price_sort = float(c["price"]) if c["price"] else 0
        except Exception: price_sort = 0
        rows.append(
f'''    <tr data-name="{html.escape(c["company"].lower())}"
        data-sector="{html.escape(c["sector"].lower())}"
        data-mcap="{mcap_sort}" data-ytd="{ytd_sort}" data-price="{price_sort}">
      <td><a href="./{c["slug"]}.html">{html.escape(c["company"])}</a></td>
      <td><span class="sect">{html.escape(c["sector"])}</span></td>
      <td class="num">{fmt_num(c["price"])}</td>
      <td class="num {day_cls}">{html.escape(c["day_change"] or "—")}</td>
      <td class="num {ytd_cls}">{html.escape(c["ytd"] or "—")}</td>
      <td class="num">{mcap or "—"}</td>
    </tr>''')
    rows_html = "\n".join(rows)

    recent = latest_news(6)
    recent_news_html = "\n".join(
        f'      <a class="zse-news-card" href="/articles/{n["file"]}.html"><p class="zse-news-date">{n["date"]}</p><h3 class="zse-news-title">{html.escape(n["title"])}</h3></a>'
        for n in recent
    ) if recent else '      <p style="color:var(--text-light)">No recent stories.</p>'

    title = "Zimbabwe Stock Exchange (ZSE) listed companies — live prices"
    desc = (f"All {total} companies and funds listed on the Zimbabwe Stock "
            "Exchange — latest ZWG price, daily change, YTD performance and "
            "market cap. Searchable, sortable, with full company profiles.")

    ld_page = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title,
        "description": desc,
        "url":"https://mutapatimes.com/zse/",
        "inLanguage":"en",
        "publisher":{"@type":"Organization","name":"The Mutapa Times",
                     "logo":{"@type":"ImageObject","url":"https://mutapatimes.com/img/logo.png"}}
    }, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"ZSE listed companies","item":"https://mutapatimes.com/zse/"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(title)} | The Mutapa Times</title>
    <link rel="canonical" href="https://mutapatimes.com/zse/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://mutapatimes.com/zse/">
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
  <header class="zse-section-header">
    <p class="zse-section-eyebrow">Mutapa Times &middot; Markets</p>
    <h1 class="zse-section-title">Zimbabwe Stock Exchange &mdash; listed companies</h1>
    <p class="zse-section-stand">All {total} companies and funds on the Zimbabwe Stock
      Exchange (ZSE), with latest closing price in ZWG, daily change, year-to-date
      performance, and market capitalisation. Click any company for its full
      profile, history, and our latest coverage.</p>
    <hr class="zse-rule">
  </header>
  {hub_banner_html()}
  <div class="zse-stats" role="list">
{stats_html}
  </div>
  <div class="zse-filterbar">
    <input type="search" class="zse-search" id="zseSearch"
           placeholder="Search by company name…" aria-label="Search ZSE companies">
    <div class="zse-chips" role="group" aria-label="Filter by sector">
      {chr(10).join("      " + c for c in chips)}
    </div>
  </div>
  <p class="zse-count" id="zseCount" aria-live="polite">Showing all {total} listings.</p>
  <div class="zse-tablewrap">
    <table class="zse-table" id="zseTable">
      <thead>
        <tr>
          <th data-sort="name" aria-sort="ascending">Company</th>
          <th data-sort="sector">Sector</th>
          <th data-sort="price" class="num">Price (ZWG)</th>
          <th data-sort="day" class="num">1D</th>
          <th data-sort="ytd" class="num">YTD</th>
          <th data-sort="mcap" class="num">Mkt cap (B)</th>
        </tr>
      </thead>
      <tbody id="zseBody">
{rows_html}
      </tbody>
    </table>
  </div>
  <section class="zse-news" aria-label="Latest from The Mutapa Times">
    <h2 class="zse-news-h2">Latest from The Mutapa Times</h2>
    <div class="zse-news-grid">
{recent_news_html}
    </div>
  </section>
  <section class="zse-sources" aria-label="About this directory">
    <h2>About this directory</h2>
    <ul>
      <li>Price, daily change, YTD and market cap from <a href="https://www.african-markets.com/en/stock-markets/zse/listed-companies" rel="noopener" target="_blank">African Markets</a>, refreshed daily.</li>
      <li>Company profile detail (founded, headquarters, key people, industry) is drawn from Wikipedia where a verified article exists.</li>
      <li>This is editorial reference, not investment advice. ZSE quotes are not real-time and have at least one trading day's delay.</li>
    </ul>
    <p class="zse-sources-note">Last data refresh: {TODAY}. Spot an error? Email <a href="mailto:news@mutapatimes.com?subject=ZSE%20directory%20update">news@mutapatimes.com</a>.</p>
  </section>
</main>
{FOOTER}
<script>
(function(){{
  var body = document.getElementById('zseBody');
  var rows = Array.from(body.querySelectorAll('tr'));
  var search = document.getElementById('zseSearch');
  var chips = Array.from(document.querySelectorAll('.zse-chip'));
  var clear = document.getElementById('zseClear');
  var countEl = document.getElementById('zseCount');
  var headers = Array.from(document.querySelectorAll('.zse-table th[data-sort]'));
  var total = rows.length;
  var active = new Set();

  function apply(){{
    var q = (search.value || '').trim().toLowerCase();
    var shown = 0;
    rows.forEach(function(r){{
      var n = r.dataset.name || '';
      var s = r.dataset.sector || '';
      var matchQ = !q || n.indexOf(q) !== -1 || s.indexOf(q) !== -1;
      var matchS = !active.size || active.has(s);
      var ok = matchQ && matchS;
      r.hidden = !ok;
      if (ok) shown++;
    }});
    countEl.textContent = (q || active.size)
      ? 'Showing ' + shown + ' of ' + total + ' listings.'
      : 'Showing all ' + total + ' listings.';
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
    search.value = ''; active.clear();
    chips.forEach(function(c){{ c.setAttribute('aria-pressed','false'); }});
    apply();
  }});

  // Sorting
  var sortKey = 'name', sortDir = 1;
  function sort(key){{
    if (sortKey === key) sortDir = -sortDir;
    else {{ sortKey = key; sortDir = 1; }}
    headers.forEach(function(h){{
      h.setAttribute('aria-sort', h.dataset.sort === sortKey ? (sortDir > 0 ? 'ascending' : 'descending') : 'none');
    }});
    rows.sort(function(a, b){{
      var va, vb;
      if (key === 'name')   {{ va = a.dataset.name;   vb = b.dataset.name;   return sortDir * va.localeCompare(vb); }}
      if (key === 'sector') {{ va = a.dataset.sector; vb = b.dataset.sector; return sortDir * va.localeCompare(vb); }}
      if (key === 'price')  {{ va = +a.dataset.price; vb = +b.dataset.price; return sortDir * (va - vb); }}
      if (key === 'ytd')    {{ va = +a.dataset.ytd;   vb = +b.dataset.ytd;   return sortDir * (va - vb); }}
      if (key === 'mcap')   {{ va = +a.dataset.mcap;  vb = +b.dataset.mcap;  return sortDir * (va - vb); }}
      return 0;
    }});
    rows.forEach(function(r){{ body.appendChild(r); }});
  }}
  headers.forEach(function(h){{ h.addEventListener('click', function(){{ sort(h.dataset.sort); }}); }});
}})();
</script>
</body>
</html>
'''
    return out

# --- Detail -----------------------------------------------------------------
def render_detail(c):
    wp = c.get("wp") or {}
    name = c["company"]
    sector = c["sector"]

    profile_facts = []
    LBL_MAP = [
        ("founded","Founded"), ("headquarters","Headquarters"),
        ("industry","Industry"), ("key_people","Key people"),
        ("products","Products"), ("revenue","Revenue"),
        ("employees","Employees"), ("parent","Parent"),
        ("subsid","Subsidiaries"), ("website","Website"),
        ("traded_as","Traded as"), ("predecessor","Predecessor"),
    ]
    for k, lbl in LBL_MAP:
        v = wp.get(k)
        if v: profile_facts.append((lbl, v))

    summary = (wp.get("summary") or "").strip()
    if len(summary) > 700:
        summary = summary[:700].rsplit(".", 1)[0] + "."
    summary_html = f"<p>{html.escape(summary)}</p>" if summary else ""

    profile_html = ""
    if profile_facts or summary:
        rows = "\n".join(f'        <div class="zse-profile-row"><dt>{html.escape(lbl)}</dt><dd>{html.escape(val)}</dd></div>' for lbl, val in profile_facts)
        credit = ""
        if wp.get("wikipedia"):
            credit = f'<p class="zse-profile-credit">Profile data: <a href="{wp["wikipedia"]}" rel="noopener" target="_blank">Wikipedia</a>. Figures may be out of date.</p>'
        profile_dl = ('<dl class="zse-profile">\n' + rows + '\n    </dl>') if profile_facts else ""
        profile_html = f'''    <h2>Company profile</h2>
{summary_html}
    {profile_dl}
    {credit}'''

    # Hero image
    img = (wp.get("image") or {})
    hero_html = ""
    if img.get("local"):
        att_bits = []
        if img.get("artist"): att_bits.append(html.escape(img["artist"]))
        if img.get("license"): att_bits.append(html.escape(img["license"]))
        att = " &middot; ".join(att_bits) if att_bits else "Wikimedia Commons"
        hero_html = f'''<figure class="zse-hero-img">
  <img src="..{img["local"]}" alt="{html.escape(name)}" loading="eager">
  <figcaption class="zse-hero-img-cap">Photo: <a href="{img["commons_page"]}" rel="noopener" target="_blank">Wikimedia Commons</a> &middot; {att}</figcaption>
</figure>'''

    # Related news
    alt_names = []
    short = name.replace(" Holdings", "").replace(" Corporation", "").replace(" Limited", "").replace(" Zimbabwe", "")
    if short != name: alt_names.append(short)
    arts = matching_articles(name, alt_names, max_n=5)
    rel_html = ""
    if arts:
        items = "\n".join(
            f'        <li><a href="/articles/{a["file"]}.html">{html.escape(a["title"])}</a> <span style="color:var(--text-light)">&mdash; {a["date"]}</span></li>'
            for a in arts)
        rel_html = f'''    <h2>Recent coverage</h2>
    <ul>
{items}
    </ul>'''

    # Price cells
    price_cells = []
    if c["price"]:
        price_cells.append(("Last price", f"ZWG {fmt_num(c['price'])}", ""))
    if c["day_change"]:
        price_cells.append(("1-day change", html.escape(c['day_change']), sign_class(c['day_change'])))
    if c["ytd"]:
        price_cells.append(("YTD", html.escape(c['ytd']), sign_class(c['ytd'])))
    if c["mcap_b"]:
        try:
            price_cells.append(("Market cap", f"ZWG {float(c['mcap_b']):,.2f}B", ""))
        except Exception: pass
    price_cells.append(("Sector", html.escape(sector), ""))
    if c.get("data_date"):
        price_cells.append(("Data as of", html.escape(c["data_date"]) + "/2026", ""))

    price_html = "\n".join(
        f'  <div class="zse-pricecell"><p class="zse-pricecell-label">{lbl}</p><p class="zse-pricecell-value {cls}">{val}</p></div>'
        for lbl, val, cls in price_cells)

    desc = f"{name}: latest ZSE price, performance, sector and company profile. The Mutapa Times' guide to Zimbabwe Stock Exchange listed companies."

    ld_org = {
        "@context":"https://schema.org","@type":"Organization",
        "name": name,
        "url": f"https://mutapatimes.com/zse/{c['slug']}.html",
        "industry": sector,
        "address": {"@type":"PostalAddress","addressCountry":"ZW"},
    }
    if wp.get("headquarters"):
        ld_org["address"]["streetAddress"] = wp["headquarters"]
    if wp.get("founded"):
        ld_org["foundingDate"] = wp["founded"]
    if wp.get("website"):
        ld_org["sameAs"] = [wp["website"]]
    ld_org_json = json.dumps(ld_org, ensure_ascii=False)

    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"ZSE listed companies","item":"https://mutapatimes.com/zse/"},
            {"@type":"ListItem","position":3,"name": name,"item": f"https://mutapatimes.com/zse/{c['slug']}.html"}
        ]
    }, ensure_ascii=False)

    stand = (
        f"{html.escape(name)} is a Zimbabwe Stock Exchange-listed {html.escape(sector.lower())} company. "
        f"Latest closing price{(' is ZWG ' + fmt_num(c['price']) + ', ') if c['price'] else ' '}"
        f"{('with YTD performance ' + html.escape(c['ytd']) + '. ') if c['ytd'] else ''}"
        f"Data as of {html.escape(c.get('data_date','')) }/2026."
    )

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(name)} — ZSE share price, profile | The Mutapa Times</title>
    <link rel="canonical" href="https://mutapatimes.com/zse/{c["slug"]}.html">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(name)} — ZSE share price, profile">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://mutapatimes.com/zse/{c["slug"]}.html">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(name)} — ZSE share price">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_org_json}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="zse-detail-head">
    <p class="zse-detail-eyebrow"><a href="./" style="color:inherit;text-decoration:none">ZSE listed companies</a> &middot; {html.escape(sector)}</p>
    <h1 class="zse-detail-title">{html.escape(name)}</h1>
    <p class="zse-detail-stand">{stand}</p>
    <hr class="zse-detail-rule">
  </header>
  {hero_html}
  <div class="zse-pricerow">
{price_html}
  </div>
  <div class="zse-prose">
{profile_html}
{rel_html}
    <h2>Where this data comes from</h2>
    <p>Closing prices, daily change, year-to-date returns and market
      capitalisation are drawn from <a href="https://www.african-markets.com/en/stock-markets/zse/listed-companies" rel="noopener" target="_blank">African Markets</a>,
      with a one trading-day delay. Company profile data is drawn from
      Wikipedia where a verified article exists. This page is editorial
      reference, not investment advice.</p>
  </div>
  <section class="zse-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://www.african-markets.com/en/stock-markets/zse/listed-companies" rel="noopener" target="_blank">African Markets &mdash; ZSE listings</a> (price, market cap, sector)</li>
      <li><a href="https://www.zse.co.zw/" rel="noopener" target="_blank">Zimbabwe Stock Exchange</a> (official source)</li>
      {('<li><a href="' + wp["wikipedia"] + '" rel="noopener" target="_blank">Wikipedia &mdash; ' + html.escape(name) + '</a> (company profile' + (', hero photo' if img.get('local') else '') + ')</li>') if wp.get("wikipedia") else ''}
    </ul>
    <p class="zse-sources-note">Last reviewed {TODAY}. The Mutapa Times is
      editorially independent and earns no commission from any listed company.</p>
  </section>
  <p class="zse-back"><a href="./">&larr; Back to all ZSE listings</a></p>
</main>
{FOOTER}
</body>
</html>
'''
    return out

# Write everything
hub = render_hub()
(OUT / "index.html").write_text(hub)
print(f"\nwrote {OUT / 'index.html'} ({len(hub):,} bytes)")

for c in companies:
    p = render_detail(c)
    (OUT / f"{c['slug']}.html").write_text(p)
print(f"wrote {len(companies)} detail pages")
