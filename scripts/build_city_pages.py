#!/usr/bin/env python3
"""Generate dedicated city news pages for Zimbabwe's six largest cities.

One page per city — pre-rendered static HTML so Google crawls a fully
populated article list at the canonical URL. JS hydration on top adds
a live weather card and refreshes the article list against the latest
CMS index.

URL pattern:  /<city>-news.html  →  served at /<city>-news (no .html)
              by GitHub Pages' default extension stripping.

SEO surfaces:
  • Hyper-specific <title>, <meta description>, <meta keywords>
  • Schema.org CollectionPage + Place + ItemList JSON-LD
  • Long-form keyword-rich body intro
  • Internal links from related cities + main nav
  • Canonical + hreflang anchors

Run on every fetch-news cron so the article list stays fresh in the
static HTML (separate from the JS hydration layer, which is for
visitors arriving between crons).
"""
import html as html_mod
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from build_feed_cards import card_public_url as _feed_card_url
except ImportError:
    _feed_card_url = None

BASE_URL = "https://www.mutapatimes.com"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INDEX_PATH = os.path.join(ROOT, "content", "articles", "index.json")

CITIES = [
    {
        "slug": "harare",
        "name": "Harare",
        "title_short": "Harare",
        "lat": -17.8252, "lon": 31.0335,
        "headline": "Harare news, today.",
        "context": (
            "Harare is the capital and largest city of Zimbabwe, "
            "headquarters of the Reserve Bank of Zimbabwe, the "
            "Zimbabwe Stock Exchange, every major bank and most "
            "listed industrial groups. The Mutapa Times tracks "
            "Harare daily — economy, business, politics, infrastructure, "
            "culture, sport — aggregating reports from local "
            "Zimbabwean newsrooms and international wire services."
        ),
        "keywords_extra": [
            "Harare news", "Harare news today", "Harare news latest",
            "latest Harare news", "Harare business news", "Harare weather",
            "Harare politics", "Harare Zimbabwe news",
            "news Harare", "Harare today",
        ],
        "matchers": [r"\bharare\b"],
    },
    {
        "slug": "bulawayo",
        "name": "Bulawayo",
        "title_short": "Bulawayo",
        "lat": -20.1539, "lon": 28.5880,
        "headline": "Bulawayo news, today.",
        "context": (
            "Bulawayo is Zimbabwe's second city, the historic capital of "
            "Matabeleland and the country's industrial heartland. The "
            "Mutapa Times covers Bulawayo daily — manufacturing, the "
            "Zimbabwe International Trade Fair, urban infrastructure, "
            "the National Railways of Zimbabwe HQ, Highlanders FC, and "
            "the cultural calendar — pulling from local newsrooms "
            "and international wires."
        ),
        "keywords_extra": [
            "Bulawayo news", "Bulawayo news today", "Bulawayo news latest",
            "latest Bulawayo news", "Bulawayo business news",
            "Bulawayo weather", "Matabeleland news", "Bulawayo Zimbabwe news",
            "news Bulawayo", "Bulawayo today",
        ],
        "matchers": [r"\bbulawayo\b"],
    },
    {
        "slug": "mutare",
        "name": "Mutare",
        "title_short": "Mutare",
        "lat": -18.9707, "lon": 32.6731,
        "headline": "Mutare news, today.",
        "context": (
            "Mutare is the largest city in eastern Zimbabwe, the gateway "
            "to the Eastern Highlands and the headquarters of major "
            "agribusiness and tea-growing operations. The Mutapa Times "
            "tracks Mutare daily — Manicaland politics, border trade with "
            "Mozambique, timber and citrus exports, tourism in Nyanga "
            "and Vumba, and the cultural calendar — aggregating reports "
            "from local Zimbabwean newsrooms and international wires."
        ),
        "keywords_extra": [
            "Mutare news", "Mutare news today", "Mutare news latest",
            "latest Mutare news", "Mutare business news", "Mutare weather",
            "Manicaland news", "Mutare Zimbabwe news",
            "news Mutare", "Mutare today", "Nyanga news", "Vumba news",
        ],
        "matchers": [r"\bmutare\b", r"\bmanicaland\b"],
    },
    {
        "slug": "gweru",
        "name": "Gweru",
        "title_short": "Gweru",
        "lat": -19.4570, "lon": 29.8170,
        "headline": "Gweru news, today.",
        "context": (
            "Gweru is the capital of the Midlands province, a key "
            "industrial, education and military town in central "
            "Zimbabwe. The Mutapa Times covers Gweru daily — Midlands "
            "State University, the ZNA Officers' Academy, ferrochrome "
            "and steel, urban affairs, and the cultural calendar — "
            "pulling from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Gweru news", "Gweru news today", "Gweru news latest",
            "latest Gweru news", "Gweru business news", "Gweru weather",
            "Midlands news", "Gweru Zimbabwe news",
            "news Gweru", "Gweru today",
        ],
        "matchers": [r"\bgweru\b", r"\bmidlands\b"],
    },
    {
        "slug": "masvingo",
        "name": "Masvingo",
        "title_short": "Masvingo",
        "lat": -20.0744, "lon": 30.8328,
        "headline": "Masvingo news, today.",
        "context": (
            "Masvingo is Zimbabwe's oldest colonial-era town and home "
            "to the Great Zimbabwe National Monument — the medieval "
            "stone city that gave the country its name. The Mutapa Times "
            "tracks Masvingo daily — Great Zimbabwe heritage news, "
            "Lake Mutirikwi, agriculture in the Lowveld, Masvingo "
            "Polytechnic, and the cultural calendar — aggregating "
            "reports from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Masvingo news", "Masvingo news today", "Masvingo news latest",
            "latest Masvingo news", "Masvingo business news",
            "Masvingo weather", "Great Zimbabwe news", "Lowveld news",
            "Masvingo Zimbabwe news",
            "news Masvingo", "Masvingo today",
        ],
        "matchers": [r"\bmasvingo\b", r"\bgreat zimbabwe\b"],
    },
    {
        "slug": "victoria-falls",
        "name": "Victoria Falls",
        "title_short": "Vic Falls",
        "lat": -17.9244, "lon": 25.8572,
        "headline": "Victoria Falls news, today.",
        "context": (
            "Victoria Falls is Zimbabwe's premier tourist town and "
            "home to the Victoria Falls Stock Exchange (VFEX). The "
            "Mutapa Times covers Vic Falls daily — Mosi-oa-Tunya "
            "conservation, the VFEX, hospitality and safari operators, "
            "Hwange National Park, and the SADC tourism corridor — "
            "aggregating reports from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Victoria Falls news", "Vic Falls news", "Victoria Falls news today",
            "Victoria Falls news latest", "latest Vic Falls news",
            "Victoria Falls weather", "Mosi-oa-Tunya news",
            "VFEX news", "Hwange news", "tourism news Zimbabwe",
            "news Victoria Falls", "Vic Falls today",
        ],
        "matchers": [r"\bvictoria falls\b", r"\bvic[\s-]?falls\b",
                     r"\bmosi[\s-]?oa[\s-]?tunya\b", r"\bhwange\b", r"\bvfex\b"],
    },
]


def esc(s):
    return html_mod.escape(s or "", quote=True)


def format_date(date_str):
    if not date_str:
        return ""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        return f"{months[d.month - 1]} {d.day}, {d.year}"
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else date_str


def load_articles():
    try:
        entries = json.load(open(INDEX_PATH))
    except (IOError, json.JSONDecodeError):
        return []
    fresh = [e for e in entries if isinstance(e, dict) and e.get("slug") and e.get("title")]
    fresh.sort(key=lambda e: e.get("date") or "", reverse=True)
    return fresh


def articles_for_city(all_articles, city):
    """Filter articles whose title OR summary mentions any city matcher."""
    matchers = [re.compile(p, re.IGNORECASE) for p in city["matchers"]]
    out = []
    for a in all_articles:
        text = f"{a.get('title','')} {a.get('summary','')}"
        if any(m.search(text) for m in matchers):
            out.append(a)
    return out


def render_article_row(a, idx):
    slug = a["slug"]
    title = a["title"]
    summary = (a.get("summary") or "")[:240]
    cat = (a.get("category") or "").strip()
    when = format_date(a.get("date", ""))
    href = f"/articles/{slug}.html"
    bg_cls = " city-article--alt" if idx % 2 else ""
    summary_block = f'  <p class="city-article-summary">{esc(summary)}</p>' if summary else ""
    cat_block = f'<span class="city-article-cat">{esc(cat)}</span>' if cat else ""
    time_block = f'<time>{esc(when)}</time>' if when else ""
    return (
        f'<article class="city-article{bg_cls}">'
        f'  <h3 class="city-article-title"><a href="{esc(href)}">{esc(title)}</a></h3>'
        f'{summary_block}'
        f'  <p class="city-article-meta">'
        f'{cat_block}'
        f'{time_block}'
        f'  </p>'
        f'</article>'
    )


def build_schema(city, articles):
    items = []
    for i, a in enumerate(articles[:30], start=1):
        items.append({
            "@type": "ListItem",
            "position": i,
            "url": f"{BASE_URL}/articles/{a['slug']}.html",
            "name": a["title"],
        })
    return [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{city['name']} news",
            "description": (
                f"Latest {city['name']} news, business, politics, weather "
                f"and culture — daily updates from Zimbabwe. The Mutapa Times."
            ),
            "url": f"{BASE_URL}/{city['slug']}-news",
            "inLanguage": "en",
            "isPartOf": {"@type": "WebSite", "name": "The Mutapa Times",
                         "url": BASE_URL},
            "about": {
                "@type": "Place",
                "name": city["name"],
                "address": {"@type": "PostalAddress",
                            "addressLocality": city["name"],
                            "addressCountry": "ZW"},
                "geo": {"@type": "GeoCoordinates",
                        "latitude": city["lat"], "longitude": city["lon"]},
            },
            "publisher": {
                "@type": "NewsMediaOrganization",
                "name": "The Mutapa Times",
                "logo": {"@type": "ImageObject",
                         "url": f"{BASE_URL}/img/brand/mark-512.png"},
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Latest {city['name']} news",
            "itemListElement": items,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home",
                 "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Cities",
                 "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 3,
                 "name": f"{city['name']} news",
                 "item": f"{BASE_URL}/{city['slug']}-news"},
            ],
        },
    ]


def build_page(city, all_articles, other_cities):
    articles = articles_for_city(all_articles, city)
    print(f"  {city['name']:<16s}  {len(articles):>4d} articles")
    rows = "\n".join(render_article_row(a, i) for i, a in enumerate(articles[:60]))
    if not rows:
        rows = '<p class="loading-msg">Fresh coverage will appear here as news comes in.</p>'

    schema_blocks = "\n".join(
        f'<script type="application/ld+json">{json.dumps(s)}</script>'
        for s in build_schema(city, articles)
    )

    related = "\n".join(
        f'<li><a href="/{c["slug"]}-news">{esc(c["name"])} news</a></li>'
        for c in other_cities
    )

    canonical = f"{BASE_URL}/{city['slug']}-news"
    title = (f"{city['name']} news latest — today's headlines from "
             f"{city['title_short']}, Zimbabwe | The Mutapa Times")
    description = (
        f"Latest {city['name']} news today — business, politics, weather, "
        f"sport and culture from {city['name']}, Zimbabwe. Updated daily by "
        f"The Mutapa Times. Includes today's {city['name']} weather forecast."
    )
    keywords = ", ".join(city["keywords_extra"])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="google-site-verification" content="hiG_LERbmJeR4lCj2z4jsSumsaHhPI_wOjRFhT1E4Yw" />
<!-- Google Reader Revenue Manager (open-access) -->
<script async type="application/javascript" src="https://news.google.com/swg/js/v1/swg-basic.js"></script>
<script>
  (self.SWG_BASIC = self.SWG_BASIC || []).push(basicSubscriptions => {{
    basicSubscriptions.init({{
      type: "NewsArticle",
      isPartOfType: ["Product"],
      isPartOfProductId: "CAow56S3DA:openaccess",
      clientOptions: {{ theme: "light", lang: "en-GB" }}
    }});
  }});
</script>
<title>{esc(title)}</title>
<link rel="canonical" href="{esc(canonical)}">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="{esc(description)}">
<meta name="keywords" content="{esc(keywords)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="language" content="English">
<meta name="geo.region" content="ZW">
<meta name="geo.placename" content="{esc(city['name'])}">
<meta name="geo.position" content="{city['lat']};{city['lon']}">
<meta name="ICBM" content="{city['lat']},{city['lon']}">
<meta name="news_keywords" content="{esc(keywords)}">

<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="The Mutapa Times">
<meta property="og:image" content="{BASE_URL}/img/brand/og-share.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_GB">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@mutapatimes">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{BASE_URL}/img/brand/og-share.png">
<link rel="alternate" type="application/rss+xml" title="The Mutapa Times" href="{BASE_URL}/feed.xml">
<link rel="alternate" hreflang="en" href="{esc(canonical)}">
<link rel="alternate" hreflang="x-default" href="{esc(canonical)}">

<link rel="manifest" href="/site.webmanifest">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-icon-180x180.png">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="96x96" href="/img/favicon-96x96.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/css/normalize.css">
<link rel="stylesheet" href="/css/main.css?v=67">

{schema_blocks}
</head>
<body>
<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <a href="/" class="topbar-brand">The Mutapa Times</a>
  <nav class="topbar-nav" aria-label="Quick nav">
    <a href="/">News</a>
    <a href="/economy">Economy</a>
    <a href="/articles">Articles</a>
  </nav>
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
</div>
<div class="paper">
  <a href="/" class="title-link">
    <div class="titleDiv">
      <h1 class="title notranslate">THE MUTAPA TIMES</h1>
    </div>
    <h4 class="sub notranslate">Zimbabwe outside-in</h4>
  </a>
  <nav id="mainNav">
      <p><a target="_self" class="notranslate" href="/">News</a></p>
      <p><a target="_self" class="economy-btn" href="/economy">Economy</a></p>
      <p><a target="_self" class="notranslate" href="/fx">FX</a></p>
      <p><a target="_self" class="notranslate" href="/property">Property</a></p>
      <p><a target="_self" class="notranslate" href="/jobs">Jobs</a></p>
      <p><a target="_self" class="notranslate" href="/articles">Articles</a></p>
      <span class="nav-cities-item">
        <button type="button" class="cities-nav-toggle notranslate active" aria-haspopup="true" aria-expanded="false">Cities &#9662;</button>
        <ul class="cities-dropdown" aria-label="Zimbabwe cities">
          <li><a href="/harare-news">Harare</a></li>
          <li><a href="/bulawayo-news">Bulawayo</a></li>
          <li><a href="/mutare-news">Mutare</a></li>
          <li><a href="/gweru-news">Gweru</a></li>
          <li><a href="/masvingo-news">Masvingo</a></li>
          <li><a href="/victoria-falls-news">Victoria Falls</a></li>
        </ul>
      </span>
  </nav>
  <button class="nav-hamburger" type="button" aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <div class="nav-drawer-backdrop" data-close-drawer aria-hidden="true"></div>
  <aside class="nav-drawer" id="navDrawer" aria-hidden="true" aria-label="Site navigation">
    <button class="nav-drawer-close" type="button" data-close-drawer aria-label="Close menu">
      <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
    </button>
    <form class="nav-drawer-search" action="/articles" method="get" role="search">
      <input type="search" name="q" placeholder="Search The Mutapa Times" aria-label="Search The Mutapa Times">
    </form>
    <nav class="nav-drawer-main" aria-label="Sections">
      <a href="/">News</a>
      <a href="/economy">Economy</a>
      <a href="/fx">FX</a>
      <a href="/property">Property</a>
      <a href="/jobs">Jobs</a>
      <a href="/articles">Articles</a>
    </nav>
    <span class="nav-drawer-section">Cities</span>
    <nav class="nav-drawer-cities" aria-label="Cities">
      <a href="/harare-news">Harare</a>
      <a href="/bulawayo-news">Bulawayo</a>
      <a href="/mutare-news">Mutare</a>
      <a href="/gweru-news">Gweru</a>
      <a href="/masvingo-news">Masvingo</a>
      <a href="/victoria-falls-news">Victoria Falls</a>
    </nav>
    <span class="nav-drawer-section">Information</span>
    <nav class="nav-drawer-info" aria-label="Information">
      <a href="/about">About</a>
      <a href="/advertising">Advertising</a>
      <a href="/terms">Terms</a>
      <a href="/privacy">Privacy</a>
    </nav>
    <a href="/subscribe" class="nav-drawer-cta">Subscribe to the briefing &rarr;</a>
  </aside>
  <hr class="topHr">
  <hr class="bottomHr">
  <div class="aboutTitle">
    <div class="date"></div>
    <div class="vol"></div>
    <div class="price"></div>
  </div>
  <hr class="dateHr">

  <div id="stories-rail" aria-label="Story highlights"></div>

  <main class="city-page"
        data-city-slug="{esc(city['slug'])}"
        data-city-name="{esc(city['name'])}"
        data-city-lat="{city['lat']}"
        data-city-lon="{city['lon']}">

    <header class="page-hero">
      <h1 class="page-hero-headline">{esc(city['name'])} news, <em>today.</em></h1>
      <p class="page-hero-deck">Latest {esc(city['name'])} headlines from across Zimbabwe — business, politics, sport, weather and culture. Updated continuously from local newsrooms and international wires.</p>
    </header>

    <!-- Weather card — populated by /js/city.js on load -->
    <section class="city-weather" id="cityWeather" aria-label="{esc(city['name'])} weather">
      <div class="city-weather-inner">
        <div class="city-weather-label">{esc(city['name'].upper())} WEATHER</div>
        <div class="city-weather-temp" id="cityWxTemp">—°</div>
        <div class="city-weather-desc" id="cityWxDesc">Loading current conditions…</div>
        <div class="city-weather-extra" id="cityWxExtra"></div>
      </div>
    </section>

    <!-- SEO-anchor copy -->
    <section class="city-context">
      <p>{esc(city['context'])}</p>
    </section>

    <h2 class="city-section-heading">Latest {esc(city['name'])} headlines</h2>

    <!-- Search across this city's coverage — wired in js/city.js -->
    <div class="articles-search-wrap">
      <input type="search" id="citySearch" class="articles-search"
             placeholder="Search {esc(city['name'])} news…"
             aria-label="Search {esc(city['name'])} news">
    </div>

    <!-- Category filter — narrows the city's article list by topic.
         Wired in js/city.js; "All" is the default selection. -->
    <div class="articles-category-chips city-filter-chips" id="cityFilterChips" role="navigation" aria-label="Filter by category">
      <button class="articles-chip active" data-cat="all">All</button>
      <button class="articles-chip" data-cat="Business">Business</button>
      <button class="articles-chip" data-cat="Tech">Tech</button>
      <button class="articles-chip" data-cat="Health">Health</button>
      <button class="articles-chip" data-cat="Sport">Sport</button>
      <button class="articles-chip" data-cat="Culture">Culture</button>
      <button class="articles-chip" data-cat="Policy">Policy</button>
      <button class="articles-chip" data-cat="Opinion">Opinion</button>
      <button class="articles-chip" data-cat="Environment">Environment</button>
    </div>

    <div class="city-articles" id="cityArticles">
{rows}
    </div>

    <aside class="city-related" aria-label="Other Zimbabwe cities">
      <h2 class="city-section-heading">Other Zimbabwe cities</h2>
      <ul class="city-related-list">
{related}
      </ul>
    </aside>

    <section class="city-context city-context--foot">
      <h2>About {esc(city['name'])} news on The Mutapa Times</h2>
      <p>The Mutapa Times is an independent business and intelligence newspaper for Zimbabweans at home and in the diaspora. Our {esc(city['name'])} desk aggregates coverage from local Zimbabwean newsrooms — Bulawayo24, NewZimbabwe.com, The Herald, The Standard, NewsDay, ZimLive, 263Chat — alongside international wires from Reuters, Bloomberg, BBC, AP, Al Jazeera and The Guardian. Pages refresh several times a day. Coordinates: {city['lat']:.4f}, {city['lon']:.4f}.</p>
    </section>
  </main>

  <hr class="dateHr">
  <div class="back-to-top-wrap">
    <button class="back-to-top-btn" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">Back to top</button>
  </div>
</div>

<script defer src="/js/vendor/modernizr-3.8.0.min.js"></script>
<script defer src="/js/quote-share.js"></script>
<script defer src="/js/stories.js"></script>
<script defer src="/js/nav.js"></script>
<script defer src="/js/city.js"></script>
<script>
if ('serviceWorker' in navigator) {{
  window.addEventListener('load', function() {{ navigator.serviceWorker.register('/sw.js'); }});
}}
</script>
</body>
</html>
"""


def main():
    print("=== BUILD CITY PAGES ===")
    all_articles = load_articles()
    print(f"  Loaded {len(all_articles)} CMS articles")
    for city in CITIES:
        others = [c for c in CITIES if c["slug"] != city["slug"]]
        page = build_page(city, all_articles, others)
        out = os.path.join(ROOT, f"{city['slug']}-news.html")
        with open(out, "w") as f:
            f.write(page)
    print(f"\n  Wrote {len(CITIES)} city pages.")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
