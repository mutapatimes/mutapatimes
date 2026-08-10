#!/usr/bin/env python3
"""Generate /vfex/ — VFEX listed-companies directory. Mirrors /zse/'s
pattern (scripts/build_zse.py), adapted for what's actually public about
the VFEX:

  * Company roster: the ZSE/VFEX group's own official issuer registry
    (same public API data/vfex-market-activity.json is fetched from),
    NOT a scrape -- this is first-party, verified data (name, symbol,
    status, logo, address, contact, website).
  * Live price: cross-referenced from data/vfex-market-activity.json's
    gainers/losers, by symbol. VFEX only publishes movers/shakers
    publicly (no africa-markets.com-style full price table exists for
    it), so most companies on a given day legitimately have no live
    price to show -- shown honestly as "no live price today", not
    hidden or faked. A full daily pricesheet for every VFEX name is a
    paid ZSE Data Direct product; see the Sources section on each page.
  * Company profile detail (founded, industry, key people, etc.): only
    for the small number of VFEX names with a verified, unambiguous
    English Wikipedia article -- checked by hand, see WP_MAP. Most VFEX
    names are too new/small for Wikipedia coverage, so are left blank
    rather than guessed.
"""
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "vfex"
OUT.mkdir(exist_ok=True)
DATA = ROOT / "data" / "vfex-companies.json"
ACTIVITY = ROOT / "data" / "vfex-market-activity.json"
IMG_DIR = ROOT / "img" / "vfex"
IMG_DIR.mkdir(parents=True, exist_ok=True)

UA = "MutapaTimes/1.0 (https://mutapatimes.com; news@mutapatimes.com)"
API_BASE = "https://ds88jcmqc11je.cloudfront.net"
from datetime import datetime, timezone
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# --- Slugify ------------------------------------------------------------
def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# --- HTTP helpers (retry-hardened) --------------------------------------
def http_get_json(url, retries=3, backoff=2):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(backoff)
    raise last

def http_download(url, dest, retries=3, backoff=2):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                dest.write_bytes(r.read())
                return
        except Exception as e:
            last = e
            if attempt < retries:
                time.sleep(backoff)
    raise last

# --- Wikipedia enrichment (identical to build_zse.py) -------------------
def fetch_wikitext(title):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&prop=wikitext&format=json&redirects=1"
    try:
        j = http_get_json(url)
        return j.get("parse", {}).get("wikitext", {}).get("*", "")
    except Exception:
        return ""

def parse_infobox(wt):
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
    return f"/img/vfex/{local.name}", {
        "filename": fname, "license": short, "artist": artist,
        "commons_page": f"https://commons.wikimedia.org/wiki/{file_title.replace(' ','_')}",
        "local": f"/img/vfex/{local.name}",
    }

INFOBOX_KEYS = ["founded","founder","headquarters","industry","sector",
                "key_people","products","revenue","operating_income","net_income",
                "assets","equity","employees","subsid","parent","website","traded_as",
                "isin","predecessor"]

# Hand-verified only -- most VFEX names are too new/small for English
# Wikipedia coverage. Checked each candidate's summary API response by hand
# before adding; anything ambiguous (name collisions, no direct hit) was
# left out rather than guessed. See module docstring.
WP_MAP = {
    "Bindura Nickel Corporation Limited": "Bindura_Nickel_Corporation",
    "Nedbank Group Limited": "Nedbank_Group",
}

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

# --- News cross-reference (identical pattern to build_zse.py) -----------
WIRES = ROOT / "content" / "wires"
news_index = []
if WIRES.exists():
    for p in WIRES.glob("*.md"):
        try:
            news_index.append((p, p.read_text(errors="ignore").lower()))
        except Exception:
            pass

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

# --- Build --------------------------------------------------------------
print("Fetching VFEX issuer registry (official API)…")
issuers = http_get_json(f"{API_BASE}/api/issuers?exchange=VFEX&market=equity")
print(f"  -> {len(issuers)} issuers")

SUFFIX_RE = re.compile(r"\b(LIMITED|LTD|PLC|HOLDINGS|CORPORATION|CORP|GROUP)\b")
def _norm_name(s):
    return re.sub(r"\s+", " ", SUFFIX_RE.sub("", (s or "").upper())).strip()

print("Cross-referencing today's live price (movers/shakers)…")
price_by_symbol = {}
price_by_name = {}
as_of = None
if ACTIVITY.exists():
    act = json.loads(ACTIVITY.read_text())
    as_of = act.get("as_of")
    for m in (act.get("gainers") or []) + (act.get("losers") or []):
        sym = (m.get("symbol") or "").strip().upper()
        if sym:
            price_by_symbol[sym] = m
        else:
            # DTR movers occasionally lack a symbol (the DTR's own counter
            # name didn't exactly match the market-cap endpoint's company
            # name, e.g. missing a "LIMITED" suffix) -- fall back to a
            # normalized-name match so we don't drop a real live price.
            nm = _norm_name(m.get("name"))
            if nm:
                price_by_name[nm] = m

print("Enriching with Wikipedia (hand-verified matches only)…")
companies = []
for row in issuers:
    name = (row.get("name") or "").strip()
    if not name:
        continue
    slug = slugify(name)
    price = price_by_symbol.get((row.get("short_name") or "").strip().upper())
    if not price:
        price = price_by_name.get(_norm_name(name))
    wp = {}
    if name in WP_MAP:
        print(f"  - {name}")
        wp = enrich(name)
        time.sleep(0.5)
    companies.append({
        "name": name,
        "symbol": row.get("short_name") or "",
        "status": row.get("status") or "",
        "logo": row.get("logo") or "",
        "address": row.get("address") or "",
        "website": row.get("website_url") or "",
        "email": row.get("email") or "",
        "phone": row.get("phone") or "",
        "slug": slug,
        "price": price,
        "wp": wp,
    })
companies.sort(key=lambda c: c["name"])

DATA.write_text(json.dumps({
    "fetched_at": TODAY, "source": "ZSE/VFEX official issuer registry (public API)",
    "count": len(companies), "companies": companies,
}, indent=2, ensure_ascii=False))
print(f"saved {DATA}")
print(f"  Wikipedia-enriched: {sum(1 for c in companies if c['wp'])}")
print(f"  with live price today: {sum(1 for c in companies if c['price'])}")

# --- Templates (mirrors build_zse.py's CSS/TOPBAR/HEAD_COMMON/FOOTER) ---
CSS = """
body { background: #fff !important; }

.vfex-hub-img { max-width: 1100px; margin: 14px auto 0; padding: 0 20px; }
.vfex-hub-img-inner { aspect-ratio: 21/9; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--rule); background: #f0ece4; }
.vfex-hub-img-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }
@media (max-width: 640px) { .vfex-hub-img-inner { aspect-ratio: 16/9; } }

.vfex-section-header { padding: 24px 20px 4px; max-width: 1100px; margin: 0 auto; }
.vfex-section-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.vfex-section-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.vfex-section-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1em;
  line-height: 1.55; color: var(--text-mid); margin: 0 0 14px; max-width: 44em; }
.vfex-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 8px 0 0; }

.vfex-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; max-width: 1100px; margin: 32px auto 8px; padding: 0 20px; }
.vfex-stat { padding: 14px 16px; background: var(--paper); border: 1px solid var(--rule);
  border-radius: 8px; transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.vfex-stat:hover { border-color: var(--accent); box-shadow: 0 6px 22px rgba(0,0,0,0.06);
  transform: translateY(-1px); }
.vfex-stat-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 4px; font-weight: 600; }
.vfex-stat-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.4em;
  line-height: 1.15; color: var(--ink); margin: 0; font-weight: 700; }

.vfex-tablewrap { max-width: 1100px; margin: 20px auto 4px; padding: 0 20px;
  overflow-x: auto; }
.vfex-table { width: 100%; border-collapse: collapse; font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.92em; background: #fff; border: 1px solid var(--rule); border-radius: 8px;
  overflow: hidden; }
.vfex-table thead th { text-align: left; padding: 10px 14px; background: var(--paper);
  border-bottom: 1px solid var(--rule); font-size: 0.72em; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-light); white-space: nowrap; }
.vfex-table tbody td { padding: 10px 14px; border-bottom: 1px solid var(--rule);
  color: var(--text); }
.vfex-table tbody tr:last-child td { border-bottom: 0; }
.vfex-table tbody tr:hover { background: var(--paper); }
.vfex-table a { color: var(--ink); text-decoration: none; font-weight: 600; }
.vfex-table a:hover { color: var(--accent); }
.vfex-table .num { font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }
.vfex-table .pos { color: #1f7a3e; }
.vfex-table .neg { color: var(--accent); }
.vfex-table .muted { color: var(--text-light); }
@media (max-width: 640px) {
  .vfex-table thead th, .vfex-table tbody td { padding: 8px 10px; font-size: 0.85em; }
}

/* Per-company detail */
.vfex-detail-head { max-width: 820px; margin: 0 auto; padding: 28px 20px 12px; }
.vfex-detail-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 10px; font-weight: 700; }
.vfex-detail-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.9em, 4.4vw, 2.8em); line-height: 1.1; margin: 0 0 12px;
  color: var(--ink); letter-spacing: -0.01em; }
.vfex-detail-stand { font-family: 'Inter', system-ui, sans-serif;
  font-size: 1.02em; line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 44em; }
.vfex-detail-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 14px 0 0; }

.vfex-pricerow { max-width: 1000px; margin: 18px auto 24px; padding: 0 20px;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
.vfex-pricecell { background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 14px 16px; transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.vfex-pricecell:hover { border-color: var(--accent); box-shadow: 0 6px 22px rgba(0,0,0,0.06);
  transform: translateY(-1px); }
.vfex-pricecell-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  font-weight: 600; margin: 0 0 4px; }
.vfex-pricecell-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.35em;
  font-weight: 700; color: var(--ink); margin: 0; line-height: 1.15; font-variant-numeric: tabular-nums; }
.vfex-pricecell-value.pos { color: #1f7a3e; }
.vfex-pricecell-value.neg { color: var(--accent); }
.vfex-pricecell-value.muted { font-size: 1em; color: var(--text-light); font-weight: 600; }

.vfex-hero-img { max-width: 1000px; margin: 0 auto 18px; padding: 0 20px; }
.vfex-hero-img img { width: 100%; height: auto; max-height: 440px; object-fit: cover;
  border-radius: 8px; border: 1px solid var(--rule); display: block; background: var(--paper); }
.vfex-hero-img-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  color: var(--text-light); margin: 6px 0 0; line-height: 1.45; }
.vfex-hero-img-cap a { color: var(--text-mid); }
.vfex-logo-img { max-width: 240px; margin: 0 auto 18px; padding: 0 20px; }
.vfex-logo-img img { width: 100%; height: auto; max-height: 140px; object-fit: contain;
  border-radius: 8px; border: 1px solid var(--rule); display: block; background: var(--paper); padding: 12px; }

.vfex-prose { max-width: 720px; margin: 0 auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.vfex-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; line-height: 1.2; margin: 26px 0 10px; color: var(--ink); }
.vfex-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.vfex-prose ul { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.vfex-prose li { margin-bottom: 5px; }
.vfex-prose a { color: var(--accent); text-decoration: underline; }
.vfex-prose a:hover { color: var(--ink); }
.vfex-prose strong { color: var(--ink); }

.vfex-profile { display: grid; grid-template-columns: minmax(110px, max-content) 1fr;
  gap: 8px 18px; margin: 10px 0 6px; font-size: 0.95em;
  background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 14px 18px; }
.vfex-profile-row { display: contents; }
.vfex-profile dt { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-light);
  font-weight: 700; padding-top: 3px; }
.vfex-profile dd { margin: 0; font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.5; color: var(--ink); }
.vfex-profile dd a { color: var(--ink); }
.vfex-profile-credit { font-size: 0.78em; color: var(--text-light); margin: 8px 0 0; }
.vfex-profile-credit a { color: var(--text-mid); }
@media (max-width: 540px) {
  .vfex-profile { grid-template-columns: 1fr; gap: 2px 0; padding: 12px 14px; }
  .vfex-profile dt { padding-top: 10px; }
  .vfex-profile-row:first-child dt { padding-top: 0; }
}

.vfex-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.vfex-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700; font-family: inherit; }
.vfex-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55;
  color: var(--text); }
.vfex-sources a { color: var(--ink); text-decoration: underline; }
.vfex-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }

.vfex-back { text-align: center; margin: 24px 0 40px; font-family: 'Inter', system-ui, sans-serif; }
.vfex-back a { font-size: 0.88em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }
.vfex-back a:hover { color: var(--accent); }
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
      <a href="/vfex/">VFEX companies</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
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

def fmt_price(n):
    try:
        return f"{float(n):,.2f}"
    except Exception:
        return str(n)

SOURCES_NOTE = (
    'Full daily price lists for every VFEX-listed name are a paid ZSE Data '
    'Direct product, not something published free. Live prices shown here '
    '(when present) are today’s movers/shakers, the entire per-company '
    'picture VFEX itself publishes publicly — not a curated subset of a '
    'larger free dataset.'
)

# --- Hub ------------------------------------------------------------------
def render_hub():
    total = len(companies)
    with_price = sum(1 for c in companies if c["price"])

    stats = [
        ("Listed companies", str(total)),
        ("With a live price today", str(with_price)),
        ("Currency", "US$"),
        ("Exchange group", "ZSE / VFEX"),
    ]
    stats_html = "\n".join(
        f'    <div class="vfex-stat"><p class="vfex-stat-label">{lbl}</p><p class="vfex-stat-value">{val}</p></div>'
        for lbl, val in stats)

    rows = []
    for c in companies:
        p = c["price"]
        if p:
            price_cell = f'<span class="num">US${fmt_price(p["price"])}</span>'
            chg = p.get("change_pct")
            chg_cls = "pos" if (chg or 0) > 0 else ("neg" if (chg or 0) < 0 else "")
            chg_cell = f'<span class="num {chg_cls}">{"+" if (chg or 0) > 0 else ""}{chg:.2f}%</span>' if chg is not None else '<span class="num muted">—</span>'
        else:
            price_cell = '<span class="num muted">—</span>'
            chg_cell = '<span class="num muted">—</span>'
        rows.append(
f'''    <tr>
      <td><a href="./{c["slug"]}.html">{html.escape(c["name"])}</a></td>
      <td class="muted">{html.escape(c["symbol"])}</td>
      <td class="num">{price_cell}</td>
      <td class="num">{chg_cell}</td>
    </tr>''')
    rows_html = "\n".join(rows)

    title = "Victoria Falls Stock Exchange (VFEX) listed companies"
    desc = (f"All {total} companies listed on Zimbabwe's VFEX dollar bourse — official "
            "name, symbol, contact and today's live price where VFEX publishes one. "
            "Company profiles and our latest coverage.")

    ld_page = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title, "description": desc, "url":"https://mutapatimes.com/vfex/",
        "inLanguage":"en",
        "publisher":{"@type":"Organization","name":"The Mutapa Times",
                     "logo":{"@type":"ImageObject","url":"https://mutapatimes.com/img/logo.png"}}
    }, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"VFEX listed companies","item":"https://mutapatimes.com/vfex/"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(title)} | The Mutapa Times</title>
    <link rel="canonical" href="https://mutapatimes.com/vfex/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://mutapatimes.com/vfex/">
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
  <header class="vfex-section-header">
    <p class="vfex-section-eyebrow">Mutapa Times &middot; Markets</p>
    <h1 class="vfex-section-title">Victoria Falls Stock Exchange &mdash; listed companies</h1>
    <p class="vfex-section-stand">All {total} companies on Zimbabwe&rsquo;s VFEX dollar
      bourse, official registry data with today&rsquo;s live price where VFEX
      publishes one. Click any company for its full profile and our latest
      coverage.</p>
    <hr class="vfex-rule">
  </header>
  <div class="vfex-stats" role="list">
{stats_html}
  </div>
  <div class="vfex-tablewrap">
    <table class="vfex-table">
      <thead>
        <tr><th>Company</th><th>Symbol</th><th class="num">Price (US$)</th><th class="num">1D</th></tr>
      </thead>
      <tbody>
{rows_html}
      </tbody>
    </table>
  </div>
  <section class="vfex-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://www.zse.co.zw/" rel="noopener" target="_blank">Zimbabwe Stock Exchange / VFEX</a> official issuer registry and public market-data API</li>
      <li><a href="https://www.vfex.exchange" rel="noopener" target="_blank">vfex.exchange</a></li>
    </ul>
    <p class="vfex-sources-note">{SOURCES_NOTE} Last reviewed {TODAY}. The Mutapa Times
      is editorially independent and earns no commission from any listed company.</p>
  </section>
</main>
{FOOTER}
</body>
</html>
'''
    return out

# --- Detail -----------------------------------------------------------------
def render_detail(c):
    wp = c.get("wp") or {}
    name = c["name"]
    symbol = c["symbol"]

    profile_facts = []
    LBL_MAP = [
        ("founded","Founded"), ("headquarters","Headquarters"),
        ("industry","Industry"), ("key_people","Key people"),
        ("products","Products"), ("revenue","Revenue"),
        ("employees","Employees"), ("parent","Parent"),
        ("subsid","Subsidiaries"), ("traded_as","Traded as"),
        ("predecessor","Predecessor"),
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
        rows = "\n".join(f'        <div class="vfex-profile-row"><dt>{html.escape(lbl)}</dt><dd>{html.escape(val)}</dd></div>' for lbl, val in profile_facts)
        credit = f'<p class="vfex-profile-credit">Profile data: <a href="{wp["wikipedia"]}" rel="noopener" target="_blank">Wikipedia</a>. Figures may be out of date.</p>' if wp.get("wikipedia") else ""
        profile_dl = ('<dl class="vfex-profile">\n' + rows + '\n    </dl>') if profile_facts else ""
        profile_html = f'''    <h2>Company profile</h2>
{summary_html}
    {profile_dl}
    {credit}'''
    else:
        profile_html = (
            '    <h2>Company profile</h2>\n'
            f'    <p>No independent profile is available for {html.escape(name)} yet '
            '&mdash; it doesn&rsquo;t have a verified English Wikipedia article we could '
            'source founding date, industry or key people from. The contact and registry '
            'details below are official, direct from the ZSE/VFEX issuer registry.</p>'
        )

    # Hero image: Wikipedia photo if we have one, else the official logo
    img = (wp.get("image") or {})
    hero_html = ""
    if img.get("local"):
        att_bits = []
        if img.get("artist"): att_bits.append(html.escape(img["artist"]))
        if img.get("license"): att_bits.append(html.escape(img["license"]))
        att = " &middot; ".join(att_bits) if att_bits else "Wikimedia Commons"
        hero_html = f'''<figure class="vfex-hero-img">
  <img src="..{img["local"]}" alt="{html.escape(name)}" loading="eager">
  <figcaption class="vfex-hero-img-cap">Photo: <a href="{img["commons_page"]}" rel="noopener" target="_blank">Wikimedia Commons</a> &middot; {att}</figcaption>
</figure>'''
    elif c.get("logo"):
        hero_html = f'''<figure class="vfex-logo-img">
  <img src="{html.escape(c["logo"])}" alt="{html.escape(name)} logo" loading="eager">
</figure>'''

    alt_names = []
    short = name.replace(" Holdings", "").replace(" Corporation", "").replace(" Limited", "")
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

    price_cells = []
    p = c["price"]
    if p:
        price_cells.append(("Last price", f"US${fmt_price(p['price'])}", ""))
        chg = p.get("change_pct")
        if chg is not None:
            cls = "pos" if chg > 0 else ("neg" if chg < 0 else "")
            price_cells.append(("Change today", f"{'+' if chg > 0 else ''}{chg:.2f}%", cls))
    else:
        price_cells.append(("Last price", "No live price today", "muted"))
    price_cells.append(("Status", html.escape((c["status"] or "").title() or "—"), ""))
    if c.get("website"):
        price_cells.append(("Website", f'<a href="{html.escape(c["website"])}" rel="noopener" target="_blank">{html.escape(c["website"].replace("https://","").replace("http://","").rstrip("/"))}</a>', ""))

    price_html = "\n".join(
        f'  <div class="vfex-pricecell"><p class="vfex-pricecell-label">{lbl}</p><p class="vfex-pricecell-value {cls}">{val}</p></div>'
        for lbl, val, cls in price_cells)

    contact_bits = []
    if c.get("address"): contact_bits.append(html.escape(c["address"]))
    if c.get("phone"): contact_bits.append(html.escape(c["phone"]))
    if c.get("email"): contact_bits.append(f'<a href="mailto:{html.escape(c["email"])}">{html.escape(c["email"])}</a>')
    contact_html = ""
    if contact_bits:
        contact_html = "    <h2>Contact</h2>\n    <p>" + "<br>".join(contact_bits) + "</p>"

    desc = f"{name} ({symbol}): VFEX listing details, today's price if published, and company profile. The Mutapa Times' guide to Victoria Falls Stock Exchange listed companies."

    ld_org = {
        "@context":"https://schema.org","@type":"Organization",
        "name": name, "url": f"https://mutapatimes.com/vfex/{c['slug']}.html",
        "address": {"@type":"PostalAddress","addressCountry":"ZW"},
    }
    if c.get("address"): ld_org["address"]["streetAddress"] = c["address"]
    if wp.get("founded"): ld_org["foundingDate"] = wp["founded"]
    if c.get("website"): ld_org["sameAs"] = [c["website"]]
    ld_org_json = json.dumps(ld_org, ensure_ascii=False)

    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"VFEX listed companies","item":"https://mutapatimes.com/vfex/"},
            {"@type":"ListItem","position":3,"name": name,"item": f"https://mutapatimes.com/vfex/{c['slug']}.html"}
        ]
    }, ensure_ascii=False)

    stand = (
        f"{html.escape(name)} is listed on Zimbabwe&rsquo;s VFEX dollar bourse under {html.escape(symbol)}. "
        + (f"Last price US${fmt_price(p['price'])} as of {html.escape(as_of or TODAY)}." if p
           else "VFEX has not published a live price for this counter today.")
    )

    wp_source_li = ""
    if wp.get("wikipedia"):
        wp_source_li = f'<li><a href="{wp["wikipedia"]}" rel="noopener" target="_blank">Wikipedia &mdash; {html.escape(name)}</a> (company profile{", hero photo" if img.get("local") else ""})</li>'

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(name)} ({html.escape(symbol)}) — VFEX listing, profile | The Mutapa Times</title>
    <link rel="canonical" href="https://mutapatimes.com/vfex/{c["slug"]}.html">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(name)} — VFEX listing, profile">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://mutapatimes.com/vfex/{c["slug"]}.html">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(name)} — VFEX listing">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_org_json}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="vfex-detail-head">
    <p class="vfex-detail-eyebrow"><a href="./" style="color:inherit;text-decoration:none">VFEX listed companies</a> &middot; {html.escape(symbol)}</p>
    <h1 class="vfex-detail-title">{html.escape(name)}</h1>
    <p class="vfex-detail-stand">{stand}</p>
    <hr class="vfex-detail-rule">
  </header>
  {hero_html}
  <div class="vfex-pricerow">
{price_html}
  </div>
  <div class="vfex-prose">
{profile_html}
{contact_html}
{rel_html}
  </div>
  <section class="vfex-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://www.zse.co.zw/" rel="noopener" target="_blank">Zimbabwe Stock Exchange / VFEX</a> official issuer registry and public market-data API</li>
      {wp_source_li}
    </ul>
    <p class="vfex-sources-note">{SOURCES_NOTE} Last reviewed {TODAY}. The Mutapa Times
      is editorially independent and earns no commission from any listed company.</p>
  </section>
  <p class="vfex-back"><a href="./">&larr; Back to all VFEX listings</a></p>
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
