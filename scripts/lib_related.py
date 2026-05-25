"""Shared cross-site related-content rail.

Used by both:
  * scripts/install_related_rail.py — post-process injection on microsite pages
  * scripts/build_static_pages.py — bake into article template at render time

The rail shows 4 cards picked from a curated cross-site highlight list,
excluding cards from the same microsite the current page is on. This
keeps users moving across the site without seeing 'related' that's
actually just another instance of what they already came for.
"""

# One entry per top-level destination. 'site' is the microsite key used
# to filter out the current page's own bucket so we don't recommend
# what they're already on.
HIGHLIGHTS = [
    {"site": "fx",         "href": "/fx/",                               "tag": "MONEY",   "title": "Send money to Zimbabwe",       "meta": "Compare Wise, WorldRemit, Mukuru &middot; live FX"},
    {"site": "airports",   "href": "/airports/",                         "tag": "TRAVEL",  "title": "Live arrivals + departures",   "meta": "HRE &middot; BUQ &middot; VFA in real time"},
    {"site": "flights",    "href": "/flights/london-to-harare/",         "tag": "FLIGHTS", "title": "London → Harare flights",      "meta": "From £700 &middot; airline comparison + live prices"},
    {"site": "cooking",    "href": "/cooking/",                           "tag": "FOOD",    "title": "Zimbabwean recipes",            "meta": "Sadza, muriwo, kapenta &middot; full method"},
    {"site": "zse",        "href": "/zse/",                              "tag": "MARKETS", "title": "ZSE listed companies",          "meta": "All 54 listings &middot; live ZWG prices"},
    {"site": "schools",    "href": "/schools/",                          "tag": "SCHOOLS", "title": "ATS member schools",            "meta": "All 64 with location + Wikipedia profile"},
    {"site": "mining",     "href": "/mining/",                            "tag": "MINING",  "title": "Zimbabwean mines directory",    "meta": "Gold, lithium, platinum &middot; by commodity"},
    {"site": "moving",     "href": "/moving-to-zimbabwe/",                "tag": "GUIDES",  "title": "Moving to Zimbabwe",            "meta": "Visas, healthcare, banking, schools &middot; UK guide"},
    {"site": "news",       "href": "/articles",                           "tag": "NEWS",    "title": "Latest news",                   "meta": "Zimbabwean stories from 100+ sources"},
]

# Marker so install_related_rail.py is idempotent — pages already
# containing this string are skipped on re-run.
MARKER = "data-related-rail"

# Microsite slug per URL prefix — used both to identify the page's site
# (so we exclude it) and to map back when reading paths.
SITE_FOR_PATH = [
    ("/fx/",                    "fx"),
    ("/airports/",              "airports"),
    ("/flights/",               "flights"),
    ("/cooking/",               "cooking"),
    ("/zse/",                   "zse"),
    ("/schools/",               "schools"),
    ("/mining/",                "mining"),
    ("/moving-to-zimbabwe/",    "moving"),
    ("/articles/",              "news"),
]


def site_for_path(url_or_path):
    """Return the microsite key for a given URL or file path. None if
    the page is outside our microsite system (homepage, etc.)."""
    for prefix, site in SITE_FOR_PATH:
        # Allow either '/schools/' or 'schools/' in the input
        if prefix in url_or_path or prefix.lstrip("/") in url_or_path:
            return site
    return None


def related_rail_html(exclude_site=None, count=4):
    """Render the related-rail HTML block. exclude_site removes cards
    from that microsite so the rail recommends DIFFERENT verticals."""
    picks = [h for h in HIGHLIGHTS if h["site"] != exclude_site][:count]
    cards = "\n".join(
        f'''      <a class="rr-card" href="{h["href"]}">
        <p class="rr-card-tag">{h["tag"]}</p>
        <h3 class="rr-card-title">{h["title"]}</h3>
        <p class="rr-card-meta">{h["meta"]}</p>
      </a>'''
        for h in picks
    )
    css = """<style>
.rr-rail { max-width: 1100px; margin: 40px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.rr-rail-label { font-size: 0.72em; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--text-light); font-weight: 700; margin: 0 0 16px; }
.rr-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.rr-card { display: flex; flex-direction: column; padding: 18px 20px;
  background: #fff; border: 1px solid var(--rule, #d4d4d4); border-radius: 10px;
  text-decoration: none; color: var(--text, #1a1a1a);
  transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s; }
.rr-card:hover { border-color: var(--accent, #c41e1e); transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(0,0,0,0.06); text-decoration: none; color: inherit; }
.rr-card-tag { font-size: 0.66em; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--accent, #c41e1e); font-weight: 700; margin: 0 0 6px; }
.rr-card-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.08em; line-height: 1.2; color: var(--ink, #121212); margin: 0 0 6px;
  letter-spacing: -0.01em; }
.rr-card-meta { font-size: 0.85em; line-height: 1.45; color: var(--text-mid, #333);
  margin: 0; }
</style>"""
    return f'''{css}
<section class="rr-rail" {MARKER} aria-label="Related across The Mutapa Times">
  <p class="rr-rail-label">Read next across the site</p>
  <div class="rr-grid">
{cards}
  </div>
</section>'''


# ---------------------------------------------------------------------------
# AUTOLINKING — for use by build_static_pages.py on wire/article body HTML
# ---------------------------------------------------------------------------

# (pattern, target_url) tuples. First occurrence outside <a>/<h*> tags in
# each article gets linked. One link per pattern per article.
AUTOLINK_RULES = [
    # Cities
    (r'\bHarare\b',          '/harare-news'),
    (r'\bBulawayo\b',        '/bulawayo-news'),
    (r'\bMutare\b',          '/mutare-news'),
    (r'\bGweru\b',           '/gweru-news'),
    (r'\bMasvingo\b',        '/masvingo-news'),
    (r'\bVictoria Falls\b',  '/victoria-falls-news'),
    # Markets
    (r'\bZimbabwe Stock Exchange\b', '/zse/'),
    (r'\b(?<!/)ZSE\b',       '/zse/'),
    # Currency
    (r'\b(?:ZiG|Zim Gold)\b','/fx/'),
    (r'\bZWG\b',             '/fx/'),
    # Airports
    (r'\bRobert Gabriel Mugabe International\b', '/airports/harare/'),
    (r'\bHRE\b',             '/airports/harare/'),
    (r'\bJoshua Mqabuko Nkomo International\b', '/airports/bulawayo/'),
    (r'\bBUQ\b',             '/airports/bulawayo/'),
    (r'\bVFA\b',             '/airports/victoria-falls/'),
    # Generic concepts
    (r'\b(?:remittance|remittances)\b', '/fx/'),
    (r'\bmedical aid\b',     '/moving-to-zimbabwe/healthcare-and-medical-aid.html'),
    (r'\b(?:Cambridge|IGCSE|A[- ]Level) (?:school|exam|curriculum)\b', '/schools/'),
]

import re

_TAG_SPLIT_RE = re.compile(r'(<a [^>]*>.*?</a>|<h[1-6][^>]*>.*?</h[1-6]>|<[^>]+>)', re.DOTALL)


def autolink_body(html):
    """Insert cross-site links on first plain-text occurrence of each pattern.
    Skips text inside existing <a> tags, headings, and attribute values."""
    if not html:
        return html
    parts = _TAG_SPLIT_RE.split(html)
    linked = set()  # patterns already used in this article

    # Even indices are plain text between tags; odd are the captured tag/anchor/heading
    for i in range(0, len(parts), 2):
        chunk = parts[i]
        if not chunk:
            continue
        for pat_idx, (pattern, url) in enumerate(AUTOLINK_RULES):
            if pat_idx in linked:
                continue
            m = re.search(pattern, chunk)
            if m:
                chunk = (
                    chunk[:m.start()]
                    + f'<a href="{url}" class="autolink">{m.group(0)}</a>'
                    + chunk[m.end():]
                )
                linked.add(pat_idx)
        parts[i] = chunk

    return "".join(parts)
