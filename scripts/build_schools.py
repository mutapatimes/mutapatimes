#!/usr/bin/env python3
"""Generate /schools/ microsite from data/ats-schools.json."""
import json, os, re, html, math
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT = ROOT / "schools"
OUT.mkdir(exist_ok=True)

# Load ATS roster
data = json.loads((ROOT / "data" / "ats-schools.json").read_text())
schools = data["schools"]

# Load optional Wikipedia enrichment (only schools with verified WP articles)
WP = {}
wp_file = ROOT / "data" / "ats-schools-wp.json"
if wp_file.exists():
    WP = json.loads(wp_file.read_text())

# --- City/region inference from coordinates -------------------------------
# Each entry: (city, (lat_min, lat_max), (lon_min, lon_max), province)
REGIONS = [
    # Harare metro (broad — covers Borrowdale, Avondale, Highlands, Mt Pleasant, Hatfield, Westgate)
    ("Harare",            (-17.95, -17.60), (30.85, 31.25),  "Harare"),
    # Greater Harare commuter belt
    ("Norton / Lilfordia",(-17.78, -17.70), (30.80, 30.90),  "Mashonaland West"),
    # Bulawayo metro
    ("Bulawayo",          (-20.30, -20.05), (28.45, 28.80),  "Bulawayo"),
    # Plumtree corridor
    ("Plumtree area",     (-20.30, -20.15), (28.55, 28.70),  "Matabeleland South"),
    # Mutare
    ("Mutare",            (-19.00, -18.85), (32.55, 32.70),  "Manicaland"),
    # Marondera
    ("Marondera",         (-18.30, -18.10), (31.45, 31.70),  "Mashonaland East"),
    # Macheke (Bernard Mizeki, Ariel)
    ("Macheke / Murewa",  (-18.15, -17.85), (31.25, 31.60),  "Mashonaland East"),
    # Kwekwe / Goldridge
    ("Kwekwe",            (-19.00, -18.90), (29.78, 29.85),  "Midlands"),
    # Gweru / Midlands Christian
    ("Gweru",             (-19.50, -19.40), (29.80, 29.85),  "Midlands"),
    # Kyle / Masvingo
    ("Masvingo",          (-20.10, -20.00), (30.80, 30.90),  "Masvingo"),
    # Chinhoyi / Lomagundi
    ("Chinhoyi",          (-17.40, -17.30), (30.10, 30.20),  "Mashonaland West"),
    # Triangle / Hippo Valley / South Eastern lowveld
    ("Triangle / Hippo Valley", (-21.10, -20.80), (31.40, 31.55),  "Masvingo"),
    # Chiredzi (South Eastern College)
    ("Chiredzi",          (-21.05, -20.95), (31.70, 31.80),  "Masvingo"),
    # Karoi (Rydings)
    ("Karoi",             (-16.85, -16.75), (29.60, 29.70),  "Mashonaland West"),
    # Hwange / Coalfields
    ("Hwange",            (-18.40, -18.30), (26.45, 26.60),  "Matabeleland North"),
    # Victoria Falls
    ("Victoria Falls",    (-17.95, -17.90), (25.80, 25.90),  "Matabeleland North"),
    # Kadoma (Bryden)
    ("Kadoma",            (-18.20, -18.05), (30.15, 30.25),  "Mashonaland West"),
    # Chimanimani / Rusitu (Mvurachena)
    ("Chimanimani / Rusitu", (-20.20, -20.05), (32.65, 32.75),  "Manicaland"),
    # Filabusi / Whitestone area (Bulawayo outskirts)
    ("Bulawayo (Esigodini)", (-20.25, -20.10), (28.60, 28.70),  "Matabeleland South"),
    # Bulawayo / Falcon (Esigodini)
    ("Esigodini",         (-20.25, -20.15), (28.90, 29.00),  "Matabeleland South"),
    # Headlands (Mvurachena alt)
    ("Watershed (Marondera)", (-18.20, -18.10), (31.45, 31.55),  "Mashonaland East"),
    # Selous / Lilfordia broader
    ("Selous / Lilfordia", (-17.75, -17.70), (30.83, 30.84),  "Mashonaland West"),
]

# Specific landmark overrides (more accurate than band-matching)
LANDMARK_OVERRIDES = {
    # ats_id : (city, province, neighbourhood)
    137:   ("Macheke",      "Mashonaland East",    "Ariel Primary School"),
    170:   ("Marondera",    "Mashonaland East",    "Bernard Mizeki College"),
    168:   ("Selous",       "Mashonaland West",    "Bryden Country School"),
    8505:  ("Esigodini",    "Matabeleland South",  "Falcon College"),
    8509:  ("Kwekwe",       "Midlands",            "Goldridge College"),
    8510:  ("Kwekwe",       "Midlands",            "Goldridge Primary School"),
    8514:  ("Mutare",       "Manicaland",          "Hillcrest College, Cecil Kop"),
    8515:  ("Mutare",       "Manicaland",          "Hillcrest Preparatory School"),
    8516:  ("Chiredzi",     "Masvingo",            "Hippo Valley Estates Primary"),
    8517:  ("Masvingo",     "Masvingo",            "Kyle College"),
    8518:  ("Masvingo",     "Masvingo",            "Kyle Preparatory School"),
    8519:  ("Marondera",    "Mashonaland East",    "Lendy Park Primary School"),
    8520:  ("Norton",       "Mashonaland West",    "Lilfordia School"),
    8521:  ("Chinhoyi",     "Mashonaland West",    "Lomagundi College"),
    8522:  ("Chinhoyi",     "Mashonaland West",    "Lomagundi College Primary"),
    8526:  ("Gweru",        "Midlands",            "Midlands Christian College"),
    317093:("Gweru",        "Midlands",            "Midlands Christian School"),
    8527:  ("Harare",       "Harare",              "Mubeena Ebrahim Primary School"),
    8528:  ("Triangle",     "Masvingo",            "Murray MacDougall School"),
    8529:  ("Chimanimani",  "Manicaland",          "Mvurachena Primary School"),
    8530:  ("Marondera",    "Mashonaland East",    "Peterhouse Boys"),
    8531:  ("Marondera",    "Mashonaland East",    "Peterhouse Girls"),
    8534:  ("Plumtree",     "Matabeleland South",  "Portland Primary School"),
    8536:  ("Marondera",    "Mashonaland East",    "Ruzawi School"),
    8537:  ("Karoi",        "Mashonaland West",    "Rydings School"),
    8539:  ("Chiredzi",     "Masvingo",            "South Eastern College"),
    8540:  ("Marondera",    "Mashonaland East",    "Springvale House"),
    317102:("Marondera",    "Mashonaland East",    "Watershed College"),
    317100:("Victoria Falls","Matabeleland North", "Victoria Falls Primary School"),
    317110:("Bulawayo",     "Bulawayo",            "Whitestone School"),
    8500:  ("Hwange",       "Matabeleland North",  "Coalfields Primary School"),
    8501:  ("Harare",       "Harare",              "Dominican Convent High (Harare)"),
    8502:  ("Bulawayo",     "Bulawayo",            "Dominican Convent Primary (Bulawayo)"),
    8503:  ("Harare",       "Harare",              "Eaglesvale Junior School"),
    8504:  ("Harare",       "Harare",              "Eaglesvale Senior School"),
    8499:  ("Bulawayo",     "Bulawayo",            "Christian Brothers' College"),
    8506:  ("Harare",       "Harare",              "Gateway High School"),
    8507:  ("Harare",       "Harare",              "Gateway Primary School"),
    8508:  ("Bulawayo",     "Bulawayo",            "Girls' College"),
    8511:  ("Harare",       "Harare",              "Hartmann House Preparatory"),
    8512:  ("Harare",       "Harare",              "Hellenic Academy"),
    8513:  ("Harare",       "Harare",              "Hellenic Primary School"),
    8523:  ("Harare",       "Harare",              "Lusitania Primary School"),
    8524:  ("Bulawayo",     "Bulawayo",            "Masiyephambili College"),
    8525:  ("Bulawayo",     "Bulawayo",            "Masiyephambili Junior School"),
    8532:  ("Bulawayo",     "Bulawayo",            "Petra College Junior School"),
    8533:  ("Bulawayo",     "Bulawayo",            "Petra College Senior School"),
    8535:  ("Bulawayo",     "Bulawayo",            "Riverside Stimulation Centre"),
    8538:  ("Harare",       "Harare",              "Sharon School"),
    8541:  ("Harare",       "Harare",              "St John's College"),
    8542:  ("Harare",       "Harare",              "St Michael's Presentation Primary"),
    8544:  ("Harare",       "Harare",              "St George's College"),
    8545:  ("Harare",       "Harare",              "St John's Preparatory School"),
    8546:  ("Bulawayo",     "Bulawayo",            "St Thomas Aquinas"),
    8546:  ("Bulawayo",     "Bulawayo",            "St Thomas Aquinas High"),
    167:   ("Bulawayo",     "Bulawayo",            "Carmel Primary School"),
    166:   ("Bulawayo",     "Bulawayo",            "Centenary Primary School"),
    152:   ("Harare",       "Harare",              "Arundel School"),
    169:   ("Harare",       "Harare",              "Bishopslea Preparatory School"),
    165:   ("Harare",       "Harare",              "Chisipite Senior School"),
    176:   ("Harare",       "Harare",              "Chisipite Junior School"),
    317104:("Harare",       "Harare",              "Westridge High School"),
    317107:("Harare",       "Harare",              "Westridge Primary School"),
    317096:("Harare",       "Harare",              "Twin Rivers Primary School"),
    317098:("Harare",       "Harare",              "Tynwald Primary School"),
}

def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s

def city_for(s):
    o = LANDMARK_OVERRIDES.get(s["ats_id"])
    if o:
        return o[0], o[1]
    lat, lon = s["lat"], s["lon"]
    for city, (la0, la1), (lo0, lo1), prov in REGIONS:
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return city, prov
    return "Zimbabwe", "—"

# Normalise categories. ATS marker tags are inconsistent (some schools tagged
# only "Boarding" — we treat that as a fact about boarding being offered, not
# the only fact about the school).
SECTION_TAGS = {"Primary","Senior"}
LIFESTYLE_TAGS = {"Boarding","Day Scholar","Weekly Boarding"}
GENDER_TAGS = {"Boys","Girls"}
URBAN_TAGS = {"Urban"}

def section_label(cats):
    cs = set(cats)
    out = []
    if "Primary" in cs: out.append("Primary")
    if "Senior" in cs: out.append("Senior")
    return " & ".join(out) if out else ""

def boarding_label(cats):
    cs = set(cats)
    out = []
    if "Boarding" in cs: out.append("Boarding")
    if "Weekly Boarding" in cs: out.append("Weekly boarding")
    if "Day Scholar" in cs: out.append("Day")
    return " · ".join(out) if out else ""

def gender_label(cats):
    cs = set(cats)
    if "Boys" in cs and "Girls" in cs: return "Co-ed"
    if "Boys" in cs: return "Boys"
    if "Girls" in cs: return "Girls"
    return ""

# Enrich
for s in schools:
    s["slug"] = slugify(s["name"])
    s["city"], s["province"] = city_for(s)
    s["section"] = section_label(s["categories"])
    s["boarding"] = boarding_label(s["categories"])
    s["gender"]   = gender_label(s["categories"])

schools.sort(key=lambda s: s["name"].lower())

# --- News cross-reference: scan wires for school name mentions -------------
WIRES = ROOT / "content" / "wires"
ARTICLES = ROOT / "articles"
news_index = []
if WIRES.exists():
    for p in WIRES.glob("*.md"):
        try:
            text = p.read_text(errors="ignore").lower()
        except Exception:
            continue
        news_index.append((p, text))

def image_for(slug):
    """Return /img/schools/<slug>.<ext> if a file exists, else None.
    Looks for user-uploaded images first, falling back to WP-fetched."""
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".svg"):
        p = ROOT / "img" / "schools" / f"{slug}{ext}"
        if p.exists():
            return f"../img/schools/{p.name}"
    return None

def latest_news(max_n=6):
    """Return latest N wires (date, title, slug) for the hub Recent News module."""
    out = []
    for p, _text in news_index:
        m = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
        if not m: continue
        # Extract title from frontmatter
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

def matching_articles(school_name, max_n=4):
    """Return up to max_n (date, slug, title) tuples for wires mentioning this school."""
    needle = school_name.lower()
    short = needle.replace(" school","").replace(" college","").strip()
    hits = []
    for p, text in news_index:
        if needle in text or (len(short) > 6 and short in text):
            # Pull title from frontmatter or first heading
            title = None
            try:
                head = p.read_text(errors="ignore").split("---",2)
                if len(head) >= 3:
                    fm = head[1]
                    m = re.search(r'^title:\s*"?([^"\n]+)"?', fm, re.M)
                    if m: title = m.group(1).strip()
                if not title:
                    m = re.search(r'^#\s+(.+)$', head[-1], re.M)
                    if m: title = m.group(1).strip()
            except Exception:
                pass
            if not title:
                title = p.stem
            # Date = filename prefix (YYYY-MM-DD)
            m = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
            if not m: continue
            hits.append({"date": m.group(1), "slug": m.group(2), "title": title, "file": p.stem})
    hits.sort(key=lambda h: h["date"], reverse=True)
    return hits[:max_n]

# --- Templates -------------------------------------------------------------

CSS = """
/* Schools directory — uses main site palette from css/main.css */
body { background: #fff !important; }
.sd-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }

/* Card hero image */
.sd-card-img { display: block; width: calc(100% + 36px); margin: -18px -18px 14px;
  aspect-ratio: 16/9; object-fit: cover; background: #f0ece4;
  border-bottom: 1px solid var(--rule); }

/* Recent news module (hub footer) */
.sd-news { max-width: 1100px; margin: 32px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.sd-news-h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 16px; letter-spacing: -0.01em; }
.sd-news-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.sd-news-card { display: block; padding: 16px 18px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); transition: border-color 0.15s, transform 0.15s; }
.sd-news-card:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.sd-news-date { font-size: 0.72em; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.sd-news-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1em; line-height: 1.3; color: var(--ink); margin: 0; }

/* Section header */
.sd-section-header { padding: 24px 20px 4px; max-width: 1100px; margin: 0 auto; }
.sd-section-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.sd-section-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.sd-section-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1em;
  line-height: 1.55; color: var(--text-mid); margin: 0 0 14px; max-width: 44em; }
.sd-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 8px 0 0; }

/* Quickfacts strip — mirrors prop-highlights style */
.sd-quickfacts { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; max-width: 1100px; margin: 20px auto 8px; padding: 0 20px; }
.sd-fact { padding: 14px 16px; background: var(--paper); border: 1px solid var(--rule);
  border-radius: 8px; }
.sd-fact-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 4px; font-weight: 600; }
.sd-fact-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.4em;
  line-height: 1.15; color: var(--ink); margin: 0; font-weight: 700; }

/* Filter bar */
.sd-filterbar { max-width: 1100px; margin: 14px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.sd-search { width: 100%; padding: 10px 14px; font-size: 0.95em;
  font-family: inherit; background: #fff; border: 1px solid var(--rule);
  color: var(--ink); border-radius: 6px; margin: 0 0 10px; }
.sd-search:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
.sd-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.sd-chip { font-size: 0.78em; letter-spacing: 0.02em; padding: 5px 12px;
  background: #f0ece4; border: 1px solid var(--rule); color: var(--ink);
  border-radius: 14px; cursor: pointer; user-select: none;
  font-family: inherit; }
.sd-chip:hover { border-color: var(--ink); }
.sd-chip[aria-pressed="true"] { background: var(--accent); border-color: var(--accent);
  color: #fff; }
.sd-clear { font-size: 0.78em; color: var(--text-mid); text-decoration: underline;
  cursor: pointer; background: none; border: 0; padding: 5px 6px;
  margin-left: 4px; font-family: inherit; }
.sd-clear:hover { color: var(--accent); }
.sd-count { max-width: 1100px; margin: 14px auto 6px; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.82em;
  color: var(--text-light); }

/* Card grid — mirrors .jobs-grid / .job-card */
.sd-grid { display: grid; gap: 14px; padding: 0 20px 24px;
  max-width: 1100px; margin: 8px auto 0;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.sd-card { display: flex; flex-direction: column; gap: 10px;
  padding: 18px; border: 1px solid var(--rule); border-radius: 8px;
  background: #fff; color: var(--text); text-decoration: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.sd-card:hover { border-color: var(--accent); text-decoration: none;
  box-shadow: 0 6px 22px rgba(0,0,0,0.06); transform: translateY(-1px); }
.sd-card-head { display: flex; gap: 12px; align-items: flex-start; }
.sd-card-mark { flex-shrink: 0; width: 44px; height: 44px; border-radius: 8px;
  background: #f0ece4; border: 1px solid var(--rule);
  display: flex; align-items: center; justify-content: center;
  font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  color: var(--accent); font-size: 1.3em; }
.sd-card-headtext { flex: 1; min-width: 0; }
.sd-card-loc { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.06em; color: var(--text-light); margin: 0 0 3px;
  text-transform: uppercase; font-weight: 600; }
.sd-card-name { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.1em; line-height: 1.2; margin: 0; color: var(--ink); }
.sd-card:hover .sd-card-name { color: var(--accent); }
.sd-card-pills { display: flex; flex-wrap: wrap; gap: 5px; margin: 2px 0 0; }
.sd-pill { display: inline-block; padding: 3px 9px; font-size: 0.7em; font-weight: 500;
  border-radius: 12px; background: #f0ece4; color: var(--ink);
  font-family: 'Inter', system-ui, sans-serif; letter-spacing: 0.02em; }
.sd-pill--section { background: #e8f1ec; }
.sd-pill--boarding { background: #f5ecd9; }
.sd-pill--gender { background: #efe6f5; }
.sd-card-meta { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  color: var(--text-light); margin: 2px 0 0; padding-top: 8px;
  border-top: 1px solid var(--rule); letter-spacing: 0.02em; }
.sd-card[hidden] { display: none; }

/* Per-school detail page */
.sd-detail-head { max-width: 820px; margin: 0 auto; padding: 28px 20px 12px; }
.sd-detail-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 10px; font-weight: 700; }
.sd-detail-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.9em, 4.4vw, 2.8em); line-height: 1.1; margin: 0 0 12px;
  color: var(--ink); letter-spacing: -0.01em; }
.sd-detail-stand { font-family: 'Inter', system-ui, sans-serif;
  font-weight: 400; font-size: 1.02em; line-height: 1.55; color: var(--text-mid);
  margin: 0 0 4px; max-width: 44em; }
.sd-detail-rule { width: 48px; height: 3px; background: var(--accent); border: 0;
  margin: 14px 0 0; }
.sd-detail-loc { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  letter-spacing: 0.08em; color: var(--text-light); text-transform: uppercase;
  margin: 0 0 6px; font-weight: 600; }

.sd-detail-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px; max-width: 1000px; margin: 18px auto 24px; padding: 0 20px; }
.sd-detail-facts .sd-fact-value { font-size: 1.05em; line-height: 1.3; }

.sd-hero-img { max-width: 1000px; margin: 0 auto 18px; padding: 0 20px; }
.sd-hero-img img { width: 100%; height: auto; max-height: 460px; object-fit: cover;
  border-radius: 8px; border: 1px solid var(--rule); display: block; background: var(--paper); }
.sd-hero-img-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  color: var(--text-light); margin: 6px 0 0; line-height: 1.45; }
.sd-hero-img-cap a { color: var(--text-mid); }

.sd-prose { max-width: 720px; margin: 0 auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.sd-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; line-height: 1.2; margin: 26px 0 10px; color: var(--ink); }
.sd-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.sd-prose ul { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.sd-prose li { margin-bottom: 5px; }
.sd-prose a { color: var(--accent); text-decoration: underline; }
.sd-prose a:hover { color: var(--ink); }
.sd-prose strong { color: var(--ink); }

.sd-profile { display: grid; grid-template-columns: minmax(110px, max-content) 1fr;
  gap: 8px 18px; margin: 10px 0 6px; font-size: 0.95em;
  background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 14px 18px; }
.sd-profile-row { display: contents; }
.sd-profile dt { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-light);
  font-weight: 700; padding-top: 3px; align-self: start; }
.sd-profile dd { margin: 0; font-family: 'Inter', system-ui, sans-serif;
  line-height: 1.5; color: var(--ink); }
@media (max-width: 540px) {
  .sd-profile { grid-template-columns: 1fr; gap: 2px 0; padding: 12px 14px; }
  .sd-profile dt { padding-top: 10px; }
  .sd-profile-row:first-child dt { padding-top: 0; }
}
.sd-profile-credit { font-size: 0.78em; color: var(--text-light); margin: 8px 0 0; }
.sd-profile-credit a { color: var(--text-mid); }

.sd-mapwrap { max-width: 1000px; margin: 12px auto 18px; padding: 0 20px; }
.sd-map { width: 100%; aspect-ratio: 16/9; border: 1px solid var(--rule);
  border-radius: 8px; background: var(--paper); display: block; overflow: hidden; }
.sd-map iframe { width: 100%; height: 100%; border: 0; display: block; }
.sd-map-cap { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-light); margin: 6px 0 0; }
.sd-map-cap a { color: var(--text-mid); }

.sd-cta { max-width: 720px; margin: 22px auto; padding: 18px 22px;
  background: var(--paper); border: 1px solid var(--rule); border-left: 3px solid var(--accent);
  border-radius: 6px; font-family: 'Inter', system-ui, sans-serif; }
.sd-cta-label { font-size: 0.7em; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 8px; }
.sd-cta p { margin: 0 0 8px; font-size: 0.95em; line-height: 1.55; color: var(--text); }
.sd-cta p:last-child { margin-bottom: 0; }
.sd-cta a { color: var(--accent); text-decoration: underline; }

.sd-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.sd-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700;
  font-family: 'Inter', system-ui, sans-serif; }
.sd-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55;
  color: var(--text); }
.sd-sources a { color: var(--ink); text-decoration: underline; }
.sd-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }

.sd-back { text-align: center; margin: 24px 0 40px;
  font-family: 'Inter', system-ui, sans-serif; }
.sd-back a { font-size: 0.88em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }
.sd-back a:hover { color: var(--accent); }
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
      <a href="/schools/">Schools directory</a><span class="sep">·</span>
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

# --- Build hub -------------------------------------------------------------

def render_hub(schools):
    # Stats
    n_total = len(schools)
    cities = sorted({s["city"] for s in schools})
    boarding_n = sum(1 for s in schools if "Boarding" in s["categories"])
    primary_n  = sum(1 for s in schools if "Primary" in s["categories"])
    senior_n   = sum(1 for s in schools if "Senior" in s["categories"])

    # Card markup
    cards = []
    for s in schools:
        tags = []
        if s["section"]: tags.append(s["section"])
        if s["boarding"]: tags.append(s["boarding"])
        if s["gender"]: tags.append(s["gender"])
        tag_html = " · ".join(html.escape(t) for t in tags) or "Independent school"
        # Data attributes for client-side filtering
        cats = " ".join(c.lower().replace(" ","-") for c in s["categories"])
        wp_data = WP.get(s["name"], {})
        founded = wp_data.get("established") or ""
        # Lift just the year out of "1955" or "July 1953"
        m = re.search(r'(\d{4})', founded)
        founded_year = m.group(1) if m else ""
        meta_bits = []
        if founded_year: meta_bits.append(f"Founded {founded_year}")
        if wp_data.get("denomination"): meta_bits.append(html.escape(wp_data["denomination"].split(",")[0].strip()))
        extra = ('<p class="sd-card-meta">' + " · ".join(meta_bits) + '</p>') if meta_bits else ''
        # Build pills (replaces .sd-card-tags with coloured pills)
        pills = []
        if s["section"]: pills.append(f'<span class="sd-pill sd-pill--section">{html.escape(s["section"])}</span>')
        if s["boarding"]:
            for b in s["boarding"].split(" · "):
                pills.append(f'<span class="sd-pill sd-pill--boarding">{html.escape(b)}</span>')
        if s["gender"]: pills.append(f'<span class="sd-pill sd-pill--gender">{html.escape(s["gender"])}</span>')
        pills_html = " ".join(pills) if pills else '<span class="sd-pill">Independent</span>'
        # Initial letter for monogram
        initial = next((ch for ch in s["name"] if ch.isalpha()), "?").upper()
        # Hero image if available (user-uploaded or WP-fetched)
        img_path = image_for(s["slug"])
        if not img_path and wp_data.get("image", {}).get("local"):
            img_path = ".." + wp_data["image"]["local"]
        img_html = f'<img class="sd-card-img" src="{img_path}" alt="{html.escape(s["name"])}" loading="lazy">' if img_path else ""
        cards.append(
f'''    <a class="sd-card" href="./{s["slug"]}.html"
       data-name="{html.escape(s["name"].lower())}"
       data-city="{html.escape(s["city"].lower())}"
       data-cats="{cats}">
      {img_html}
      <div class="sd-card-head">
        <div class="sd-card-mark" aria-hidden="true">{html.escape(initial)}</div>
        <div class="sd-card-headtext">
          <p class="sd-card-loc">{html.escape(s["city"])}</p>
          <h3 class="sd-card-name">{html.escape(s["name"])}</h3>
        </div>
      </div>
      <div class="sd-card-pills">{pills_html}</div>
      {extra}
    </a>''')
    cards_html = "\n".join(cards)

    # Recent news cards for the hub
    recent = latest_news(6)
    recent_news_html = "\n".join(
        f'      <a class="sd-news-card" href="/articles/{n["file"]}.html"><p class="sd-news-date">{n["date"]}</p><h3 class="sd-news-title">{html.escape(n["title"])}</h3></a>'
        for n in recent
    ) if recent else '      <p style="color:var(--text-light)">No recent stories.</p>'

    quickfacts = f'''<div class="sd-quickfacts" role="list">
        <div class="sd-fact"><p class="sd-fact-label">ATS members listed</p><p class="sd-fact-value">{n_total}</p></div>
        <div class="sd-fact"><p class="sd-fact-label">Towns &amp; cities</p><p class="sd-fact-value">{len(cities)}</p></div>
        <div class="sd-fact"><p class="sd-fact-label">Boarding schools</p><p class="sd-fact-value">{boarding_n}</p></div>
        <div class="sd-fact"><p class="sd-fact-label">Primary &middot; Senior</p><p class="sd-fact-value">{primary_n} &middot; {senior_n}</p></div>
    </div>'''

    chips = ['<button class="sd-chip" data-filter="primary" aria-pressed="false">Primary</button>',
             '<button class="sd-chip" data-filter="senior" aria-pressed="false">Senior</button>',
             '<button class="sd-chip" data-filter="boarding" aria-pressed="false">Boarding</button>',
             '<button class="sd-chip" data-filter="weekly-boarding" aria-pressed="false">Weekly boarding</button>',
             '<button class="sd-chip" data-filter="day-scholar" aria-pressed="false">Day</button>',
             '<button class="sd-chip" data-filter="boys" aria-pressed="false">Boys</button>',
             '<button class="sd-chip" data-filter="girls" aria-pressed="false">Girls</button>',
             '<button class="sd-clear" id="sdClear">Clear filters</button>']

    title = "Zimbabwe schools directory: ATS member schools"
    desc  = "A searchable directory of all 64 Association of Trust Schools (ATS) member schools in Zimbabwe, with location, type, and links. Data sourced from atszim.org and verified by The Mutapa Times."

    ld_page = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title,
        "description": desc,
        "url":"https://www.mutapatimes.com/schools/",
        "inLanguage":"en",
        "publisher":{"@type":"Organization","name":"The Mutapa Times","logo":{"@type":"ImageObject","url":"https://www.mutapatimes.com/img/logo.png"}}
    }, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Schools directory","item":"https://www.mutapatimes.com/schools/"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(title)} | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/schools/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://www.mutapatimes.com/schools/">
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
  <header class="sd-section-header">
    <p class="sd-section-eyebrow">Mutapa Times · Directory</p>
    <h1 class="sd-section-title">Zimbabwe schools directory</h1>
    <p class="sd-section-stand">The 64 member schools of the Association of Trust
      Schools &mdash; Zimbabwe's independent school federation &mdash; with their
      location, schooling section, and boarding status. Search and filter to
      narrow down, then open any school for full detail.</p>
    <hr class="sd-rule">
  </header>
  {quickfacts}
  <div class="sd-filterbar">
    <input type="search" class="sd-search" id="sdSearch"
           placeholder="Search by school name or town…"
           aria-label="Search schools">
    <div class="sd-chips" role="group" aria-label="Filter by category">
      {chr(10).join("      " + c for c in chips)}
    </div>
  </div>
  <p class="sd-count" id="sdCount" aria-live="polite">Showing all {n_total} schools.</p>
  <div class="sd-grid" id="sdGrid">
{cards_html}
  </div>
  <section class="sd-news" aria-label="Latest from The Mutapa Times">
    <h2 class="sd-news-h2">Latest from The Mutapa Times</h2>
    <div class="sd-news-grid">
{recent_news_html}
    </div>
  </section>
  <section class="sd-sources" aria-label="About this directory">
    <h2>About this directory</h2>
    <ul>
      <li>School roster and coordinates are sourced from the <a href="https://atszim.org/school-directory/" rel="noopener" target="_blank">ATS school directory</a>.</li>
      <li>City and province labels are assigned by The Mutapa Times based on the published coordinates.</li>
      <li>School profile detail (founded date, head, denomination, motto, enrolment) comes from Wikipedia where a verified article exists.</li>
      <li>We do not publish fees, pass rates or admission criteria here &mdash; these change every term and must be verified directly with the school.</li>
    </ul>
    <p class="sd-sources-note">Are you affiliated with one of these schools and have an update? Email <a href="mailto:news@mutapatimes.com?subject=ATS%20directory%20update">news@mutapatimes.com</a>.</p>
  </section>
</main>
{FOOTER}
<script>
(function(){{
  var grid = document.getElementById('sdGrid');
  var cards = Array.from(grid.querySelectorAll('.sd-card'));
  var search = document.getElementById('sdSearch');
  var chips = Array.from(document.querySelectorAll('.sd-chip'));
  var clear = document.getElementById('sdClear');
  var countEl = document.getElementById('sdCount');
  var total = cards.length;
  var active = new Set();

  function apply() {{
    var q = (search.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){{
      var name = c.dataset.name || '';
      var city = c.dataset.city || '';
      var cats = (c.dataset.cats || '').split(/\\s+/);
      var matchQ = !q || name.indexOf(q) !== -1 || city.indexOf(q) !== -1;
      var matchC = true;
      active.forEach(function(f){{ if (cats.indexOf(f) === -1) matchC = false; }});
      var ok = matchQ && matchC;
      c.hidden = !ok;
      if (ok) shown++;
    }});
    if (q || active.size) {{
      countEl.textContent = 'Showing ' + shown + ' of ' + total + ' schools.';
    }} else {{
      countEl.textContent = 'Showing all ' + total + ' schools.';
    }}
  }}

  search.addEventListener('input', apply);
  chips.forEach(function(chip){{
    chip.addEventListener('click', function(){{
      var f = chip.dataset.filter;
      if (active.has(f)) {{ active.delete(f); chip.setAttribute('aria-pressed','false'); }}
      else                {{ active.add(f);    chip.setAttribute('aria-pressed','true'); }}
      apply();
    }});
  }});
  clear.addEventListener('click', function(){{
    search.value = '';
    active.clear();
    chips.forEach(function(c){{ c.setAttribute('aria-pressed','false'); }});
    apply();
  }});
}})();
</script>
</body>
</html>
'''
    return out

# --- Build detail pages ----------------------------------------------------

def render_detail(s):
    cats = s["categories"]
    section = s["section"] or "Independent"
    gender = s["gender"] or "—"
    boarding = s["boarding"] or "—"

    title_full = s["name"]
    short = title_full.replace(" School","").replace(" Preparatory","").strip()

    # Standfirst — generic, factual
    desc_parts = []
    if section and section != "Independent":
        desc_parts.append(section.lower())
    if boarding and boarding != "—":
        desc_parts.append(boarding.lower())
    if gender and gender != "—":
        desc_parts.append(gender.lower())
    type_phrase = " · ".join(desc_parts) if desc_parts else "independent"
    stand = f"{html.escape(s['name'])} is a member of the Association of Trust Schools, Zimbabwe's independent school federation. Located in {html.escape(s['city'])}, {html.escape(s['province'])}."

    # Quick facts grid
    qf = [("Location", f"{html.escape(s['city'])}, {html.escape(s['province'])}")]
    if section and section != "Independent":
        qf.append(("Section", html.escape(section)))
    if boarding and boarding != "—":
        qf.append(("Status", html.escape(boarding)))
    if gender and gender != "—":
        qf.append(("Intake", html.escape(gender)))
    qf.append(("ATS member", "Yes"))

    qf_html = '\n'.join(
        f'        <div class="sd-fact"><p class="sd-fact-label">{lbl}</p><p class="sd-fact-value">{val}</p></div>'
        for lbl, val in qf
    )

    # Coordinates / map
    bbox_pad = 0.01
    bbox = f"{s['lon']-bbox_pad},{s['lat']-bbox_pad},{s['lon']+bbox_pad},{s['lat']+bbox_pad}"
    osm_url = f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&layer=mapnik&marker={s['lat']},{s['lon']}"
    osm_link = f"https://www.openstreetmap.org/?mlat={s['lat']}&mlon={s['lon']}#map=16/{s['lat']}/{s['lon']}"

    # Related coverage
    arts = matching_articles(s["name"], max_n=4)
    if arts:
        rel_items = '\n'.join(
            f'        <li><a href="/articles/{a["file"]}.html">{html.escape(a["title"])}</a> <span style="color:var(--text-light)">&mdash; {a["date"]}</span></li>'
            for a in arts)
        rel_html = f'''      <h2>Recent coverage</h2>
      <ul>
{rel_items}
      </ul>'''
    else:
        rel_html = ''

    # Boarding / section narrative
    narrative_parts = []
    if "Boarding" in cats:
        narrative_parts.append("<p>This school offers boarding. Boarding schools in Zimbabwe vary considerably in pastoral care infrastructure, distance from medical care, and the day-to-day routine — these are questions to ask on a site visit rather than to assume from a brochure.</p>")
    elif "Weekly Boarding" in cats:
        narrative_parts.append("<p>This school offers weekly boarding (typically Sunday evening to Friday afternoon), with pupils returning home at weekends.</p>")
    if "Primary" in cats and "Senior" not in cats:
        narrative_parts.append("<p>This is a primary school. Pupils typically continue to a separate senior school for IGCSE and A-Level.</p>")
    if "Senior" in cats and "Primary" not in cats:
        narrative_parts.append("<p>This is a senior school covering IGCSE and A-Level. Many ATS senior schools follow the Cambridge curriculum; some sit ZIMSEC. Confirm directly with the school.</p>")

    narrative = "\n".join(narrative_parts) if narrative_parts else ""

    # --- Wikipedia-enriched profile ---
    wp = WP.get(s["name"], {})
    profile_facts = []
    if wp:
        # Pull fields we want to surface, in display order
        ORDER = [
            ("established", "Founded"),
            ("denomination", "Affiliation"),
            ("type", "Type"),
            ("gender", "Intake"),
            ("motto", "Motto"),
            ("head", "Head"),
            ("enrollment", "Enrolment"),
            ("enrolment", "Enrolment"),
            ("houses", "Houses"),
            ("colours", "Colours"),
            ("colors", "Colours"),
            ("grades", "Grades"),
        ]
        seen_labels = set()
        for key, label in ORDER:
            if label in seen_labels: continue
            val = wp.get(key)
            if not val: continue
            # Drop labels we already have from ATS data (Intake)
            if label == "Intake" and gender_label(cats):
                continue
            # If we have a head_title that differs from "Head", relabel
            if label == "Head" and wp.get("head_title"):
                label = wp["head_title"]
            profile_facts.append((label, val))
            seen_labels.add(label)

    profile_html = ""
    if wp:
        rows = ""
        for lbl, val in profile_facts:
            rows += f'        <div class="sd-profile-row"><dt>{html.escape(lbl)}</dt><dd>{html.escape(val)}</dd></div>\n'
        summary = wp.get("summary", "").strip()
        summary_html = ""
        if summary:
            # Truncate at sentence boundary
            if len(summary) > 600:
                cut = summary[:600].rsplit(".", 1)[0] + "."
                summary = cut
            summary_html = f'<p>{html.escape(summary)}</p>'
        profile_html = f'''      <h2>School profile</h2>
{summary_html}
      <dl class="sd-profile">
{rows}      </dl>
      <p class="sd-profile-credit">Profile data: <a href="{wp.get("wikipedia")}" rel="noopener" target="_blank">Wikipedia</a>. Figures with dates (e.g. enrolment) are from the year shown and have not been re-verified.</p>'''

    # Wikipedia hero image (only if free-licensed and downloaded)
    img_data = wp.get("image") if wp else None
    hero_img_html = ""
    if img_data and img_data.get("local"):
        attribution_bits = []
        if img_data.get("artist"): attribution_bits.append(html.escape(img_data["artist"]))
        if img_data.get("license"): attribution_bits.append(html.escape(img_data["license"]))
        attribution = " &middot; ".join(attribution_bits) if attribution_bits else "Wikimedia Commons"
        hero_img_html = f'''<figure class="sd-hero-img">
    <img src="..{img_data["local"]}" alt="{html.escape(s["name"])}" loading="eager">
    <figcaption class="sd-hero-img-cap">Photo: <a href="{img_data["commons_page"]}" rel="noopener" target="_blank">Wikimedia Commons</a> &middot; {attribution}</figcaption>
  </figure>'''

    desc_meta = f"{html.escape(s['name'])}: an ATS member school in {html.escape(s['city'])}, Zimbabwe. Location, type, and a direct line to verify fees and admissions with the school."

    ld_school = json.dumps({
        "@context":"https://schema.org","@type":"School",
        "name": s["name"],
        "url": f"https://www.mutapatimes.com/schools/{s['slug']}.html",
        "address": {"@type":"PostalAddress","addressLocality": s["city"], "addressRegion": s["province"], "addressCountry":"ZW"},
        "geo": {"@type":"GeoCoordinates","latitude": s["lat"], "longitude": s["lon"]},
        "memberOf": {"@type":"Organization","name":"Association of Trust Schools (Zimbabwe)","url":"https://atszim.org/"}
    }, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Schools directory","item":"https://www.mutapatimes.com/schools/"},
            {"@type":"ListItem","position":3,"name": s["name"],"item": f"https://www.mutapatimes.com/schools/{s['slug']}.html"}
        ]
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{html.escape(s["name"])} — {html.escape(s["city"])} | Schools directory | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/schools/{s["slug"]}.html">
{HEAD_COMMON}
    <meta name="description" content="{desc_meta}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(s["name"])} — Zimbabwe schools directory">
    <meta property="og:description" content="{desc_meta}">
    <meta property="og:url" content="https://www.mutapatimes.com/schools/{s["slug"]}.html">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(s["name"])} — Zimbabwe schools directory">
    <meta name="twitter:description" content="{desc_meta}">
<script type="application/ld+json">{ld_school}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="sd-detail-head">
    <p class="sd-detail-eyebrow"><a href="./" style="color:inherit;text-decoration:none">Schools directory</a> &middot; ATS member school</p>
    <p class="sd-detail-loc">{html.escape(s["city"])}, {html.escape(s["province"])}</p>
    <h1 class="sd-detail-title">{html.escape(s["name"])}</h1>
    <p class="sd-detail-stand">{stand}</p>
    <hr class="sd-detail-rule">
  </header>
  {hero_img_html}
  <div class="sd-detail-facts">
{qf_html}
  </div>
  <div class="sd-prose">
{profile_html}
    <h2>What we know</h2>
    <p>{html.escape(s["name"])} is listed as a member of the
      <a href="https://atszim.org/school-directory/" rel="noopener" target="_blank">Association
      of Trust Schools</a>, the body that federates Zimbabwe's independent
      schools. ATS membership requires schools to meet a set of governance
      and operational standards.</p>
{narrative}
    <h2>Location</h2>
    <p>The school sits at coordinates
      <a href="{osm_link}" rel="noopener" target="_blank">{s["lat"]:.4f}°, {s["lon"]:.4f}°</a>
      in {html.escape(s["city"])}, {html.escape(s["province"])}.</p>
  </div>
  <div class="sd-mapwrap">
    <div class="sd-map">
      <iframe loading="lazy" src="{osm_url}" title="Map of {html.escape(s['name'])}"></iframe>
    </div>
    <p class="sd-map-cap">Map: OpenStreetMap. <a href="{osm_link}" rel="noopener" target="_blank">Open full map</a>.</p>
  </div>
  <div class="sd-prose">
{rel_html}
    <h2>Verifying fees and admissions</h2>
    <p>School fees in Zimbabwe change every term, and the currency mix
      (USD, ZiG, both) is school-specific. We do not publish fee, pass-rate
      or boarding capacity numbers in this directory because they go stale
      fast and we cannot keep them honest. <strong>Contact the school
      directly</strong> for the current quoted fee, the currency of
      payment, and any boarding, uniform and capital levies.</p>
  </div>
  <aside class="sd-cta" aria-label="For school administrators">
    <p class="sd-cta-label">For the school</p>
    <p>If you are affiliated with {html.escape(s["name"])} and want to add
      a description, website, contact details, or a logo to this listing &mdash;
      or correct anything above &mdash; email
      <a href="mailto:news@mutapatimes.com?subject=Schools%20directory%3A%20{html.escape(s['name'])}">news@mutapatimes.com</a>.</p>
    <p>The Mutapa Times does not charge for directory listings or
      editorial updates.</p>
  </aside>
  <section class="sd-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://atszim.org/school-directory/" rel="noopener" target="_blank">Association of Trust Schools &mdash; school directory</a> (member roster, location)</li>
      <li><a href="{osm_link}" rel="noopener" target="_blank">OpenStreetMap</a> (location verification)</li>
      {('<li><a href="' + wp["wikipedia"] + '" rel="noopener" target="_blank">Wikipedia &mdash; ' + html.escape(s["name"]) + '</a> (school profile, infobox figures' + (', hero photo' if img_data and img_data.get('local') else '') + ')</li>') if wp else ''}
    </ul>
    <p class="sd-sources-note">Last reviewed {data["fetched"]}. This page
      is editorial &mdash; The Mutapa Times receives no payment from listed
      schools.</p>
  </section>
  <p class="sd-back"><a href="./">&larr; Back to schools directory</a></p>
</main>
{FOOTER}
</body>
</html>
'''
    return out

# --- Run -------------------------------------------------------------------
hub = render_hub(schools)
(OUT / "index.html").write_text(hub)
print(f"wrote {OUT / 'index.html'} ({len(hub):,} bytes)")

for s in schools:
    page = render_detail(s)
    (OUT / f"{s['slug']}.html").write_text(page)
print(f"wrote {len(schools)} detail pages to {OUT}")

# Persist enriched roster back to data/ for future use
data_enriched = dict(data)
data_enriched["schools"] = schools
(ROOT / "data" / "ats-schools.json").write_text(json.dumps(data_enriched, indent=2, ensure_ascii=False))
print(f"updated data/ats-schools.json with enrichments (city, province, slug, section, boarding, gender)")
