#!/usr/bin/env python3
"""Generate the /diaspora/ landing pages.

These are static, SEO-targeted hubs for the four largest diaspora
clusters in our GSC data: UK, South Africa, USA, plus the umbrella hub.
Each page hard-codes country-specific meta tags (title, description,
og:* and twitter:*) so Google can serve country-targeted snippets to
country-targeted queries.

Run: python3 scripts/build_diaspora_pages.py
"""
import os
import textwrap
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
BASE_URL = "https://www.mutapatimes.com"


# ─── Shared HTML scaffolding ─────────────────────────────────────────

HEAD = """<!doctype html>
<html class="no-js" lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="canonical" href="{canonical}">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="apple-touch-icon" href="/icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/normalize.css">
  <link rel="stylesheet" href="/css/main.css?v=102">
  <link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/img/favicon-16x16.png">
  <meta name="theme-color" content="#1a1a1a">
  <meta name="author" content="The Mutapa Times">
  <meta name="description" content="{description}">
  <meta name="robots" content="index, follow">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:site_name" content="The Mutapa Times">
  <meta property="og:image" content="{BASE_URL}/img/harare-palms.jpg">
  <meta name="twitter:site" content="@mutapatimes">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{BASE_URL}/img/harare-palms.jpg">
  {hreflang}
<script type="application/ld+json">{breadcrumb_jsonld}</script>
<script type="application/ld+json">{webpage_jsonld}</script>
<style>
/* Diaspora landing pages — reuses .fl- patterns from /flights/ */
body {{ background: #fbfaf6; }}
.dp-page {{ color: var(--text); }}
.dp-hero {{ padding: 60px 24px 32px; max-width: 1200px; margin: 0 auto; }}
.dp-hero-inner {{ max-width: 1080px; }}
.dp-eyebrow {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 14px; }}
.dp-title {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(2.2em, 5.5vw, 3.6em); line-height: 1.05; color: var(--ink);
  margin: 0 0 18px; letter-spacing: -0.022em; max-width: 22ch; }}
.dp-stand {{ font-family: 'Inter', system-ui, sans-serif; font-size: clamp(1.05em, 1.6vw, 1.25em);
  line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 60ch;
  font-weight: 400; }}
.dp-rule {{ width: 56px; height: 3px; background: var(--accent); border: 0; margin: 22px 0 0; }}
.dp-cards {{ display: grid; gap: 18px; padding: 0 24px 32px;
  max-width: 1080px; margin: 24px auto 0;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }}
.dp-card {{ display: flex; flex-direction: column; gap: 10px;
  padding: 22px; border: 1px solid var(--rule); border-radius: 10px;
  background: #fff; color: var(--text); text-decoration: none;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s; }}
.dp-card:hover {{ border-color: var(--accent); text-decoration: none;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06); transform: translateY(-2px); }}
.dp-card-flag {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.1em; color: var(--text-light); margin: 0;
  text-transform: uppercase; font-weight: 600; }}
.dp-card-name {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; line-height: 1.2; margin: 0; color: var(--ink);
  letter-spacing: -0.01em; }}
.dp-card:hover .dp-card-name {{ color: var(--accent); }}
.dp-card-meta {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.92em;
  color: var(--text-mid); margin: 4px 0 0; line-height: 1.55; }}
.dp-card-soon {{ opacity: 0.55; cursor: default; pointer-events: none; }}
.dp-card-soon::after {{ content: 'coming soon'; display: inline-block;
  font-size: 0.66em; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--text-light); margin-top: 4px; font-family: 'Inter', system-ui, sans-serif; }}
.dp-section {{ max-width: 1080px; margin: 56px auto 0; padding: 0 24px; }}
.dp-section-eyebrow {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; display: flex; align-items: baseline; gap: 12px; }}
.dp-section-num {{ color: var(--text-light); font-weight: 500; }}
.dp-section-h2 {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.55em, 2.6vw, 1.95em); line-height: 1.15; color: var(--ink);
  margin: 0 0 18px; letter-spacing: -0.015em; max-width: 32ch; }}
.dp-prose {{ max-width: 64ch; margin: 0; font-family: 'Inter', system-ui, sans-serif; }}
.dp-prose p {{ font-size: 1.075em; line-height: 1.7; color: var(--text); margin: 0 0 18px; }}
.dp-prose ul {{ font-size: 1.05em; line-height: 1.7; padding-left: 24px;
  margin: 0 0 18px; color: var(--text); }}
.dp-prose li {{ margin-bottom: 8px; }}
.dp-prose li::marker {{ color: var(--accent); }}
.dp-prose a {{ color: var(--accent); text-decoration: none;
  border-bottom: 1px solid currentColor; padding-bottom: 1px; }}
.dp-prose a:hover {{ color: var(--ink); }}
.dp-prose strong {{ color: var(--ink); font-weight: 600; }}
.dp-mod {{ display: grid; gap: 14px; padding: 0 24px;
  max-width: 1080px; margin: 26px auto 0;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }}
.dp-mod-card {{ padding: 18px 20px; background: #fff;
  border: 1px solid var(--rule); border-radius: 10px;
  text-decoration: none; color: var(--text);
  transition: border-color 0.15s, transform 0.15s; }}
.dp-mod-card:hover {{ border-color: var(--accent); transform: translateY(-2px);
  text-decoration: none; }}
.dp-mod-tag {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.66em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 6px; }}
.dp-mod-title {{ font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.08em; line-height: 1.25; color: var(--ink); margin: 0 0 6px;
  letter-spacing: -0.01em; }}
.dp-mod-desc {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.9em;
  color: var(--text-mid); margin: 0; line-height: 1.5; }}
.dp-sources {{ max-width: 1080px; margin: 56px auto 24px;
  padding: 22px 24px; background: #fff; border-top: 1px solid var(--rule); }}
.dp-sources h2 {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--text-light);
  font-weight: 700; margin: 0 0 12px; }}
.dp-sources p {{ font-family: 'Inter', system-ui, sans-serif; font-size: 0.92em;
  color: var(--text-mid); line-height: 1.55; margin: 0; max-width: 70ch; }}
@media (max-width: 640px) {{ .dp-hero {{ padding: 40px 20px 24px; }} }}
</style>
</head>
<body class="dp-page">
"""

TOPBAR_AND_DRAWER = """<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>
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
    <a href="/fx/">FX</a>
    <a href="/markets">Markets</a>
    <a href="/property">Property</a>
    <a href="/jobs">Jobs</a>
    <a href="/articles">Articles</a>
  </nav>
  <span class="nav-drawer-section">Diaspora</span>
  <nav class="nav-drawer-info" aria-label="Diaspora">
    <a href="/diaspora/">All countries</a>
    <a href="/diaspora/uk/">United Kingdom</a>
    <a href="/diaspora/south-africa/">South Africa</a>
    <a href="/diaspora/usa/">United States</a>
  </nav>
  <span class="nav-drawer-section">Directories</span>
  <nav class="nav-drawer-info" aria-label="Directories">
    <a href="/flights/">Flights</a>
    <a href="/schools/">Schools</a>
    <a href="/zse/">ZSE companies</a>
    <a href="/mining/">Mining</a>
    <a href="/moving-to-zimbabwe/">Moving to Zimbabwe</a>
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
</aside>
<main>
"""

FOOTER = """<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/">News</a><span class="sep">·</span>
      <a href="/diaspora/">Diaspora</a><span class="sep">·</span>
      <a href="/flights/">Flights</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/jobs">Jobs</a><span class="sep">·</span>
      <a href="/articles">Articles</a><span class="sep">·</span>
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
</script>
<script defer src="/js/nav.js"></script>
</body>
</html>
"""

# ─── Per-page content ────────────────────────────────────────────────


def hreflang_block(self_key):
    """Tell Google these are sibling regional pages of one another."""
    rels = {
        "hub": ("https://www.mutapatimes.com/diaspora/", "x-default"),
        "uk":  ("https://www.mutapatimes.com/diaspora/uk/", "en-GB"),
        "sa":  ("https://www.mutapatimes.com/diaspora/south-africa/", "en-ZA"),
        "us":  ("https://www.mutapatimes.com/diaspora/usa/", "en-US"),
    }
    out = []
    for k, (url, lang) in rels.items():
        out.append(f'<link rel="alternate" hreflang="{lang}" href="{url}">')
    return "\n  ".join(out)


def breadcrumb(country=None):
    items = [
        {"@type": "ListItem", "position": 1, "name": "Home",
         "item": "https://www.mutapatimes.com/"},
        {"@type": "ListItem", "position": 2, "name": "Diaspora",
         "item": "https://www.mutapatimes.com/diaspora/"},
    ]
    if country:
        items.append({"@type": "ListItem", "position": 3, "name": country["name"],
                      "item": country["url"]})
    import json as _json
    return _json.dumps({"@context": "https://schema.org",
                        "@type": "BreadcrumbList",
                        "itemListElement": items})


def webpage(meta):
    import json as _json
    return _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "headline": meta["title"],
        "description": meta["description"],
        "url": meta["canonical"],
        "inLanguage": meta.get("lang", "en"),
        "publisher": {"@type": "Organization", "name": "The Mutapa Times",
                      "logo": {"@type": "ImageObject",
                               "url": "https://www.mutapatimes.com/img/logo.png"}}
    })


def render(meta, hero_html, body_html, country_for_crumb=None, self_key=None):
    head = HEAD.format(
        title=meta["title"],
        description=meta["description"],
        canonical=meta["canonical"],
        BASE_URL=BASE_URL,
        hreflang=hreflang_block(self_key) if self_key else "",
        breadcrumb_jsonld=breadcrumb(country_for_crumb),
        webpage_jsonld=webpage(meta),
    )
    return head + TOPBAR_AND_DRAWER + hero_html + body_html + "</main>\n" + FOOTER


# ─── Hub page (/diaspora/) ───────────────────────────────────────────


def page_hub():
    meta = {
        "title": "Zimbabwe news for the global diaspora | The Mutapa Times",
        "description": "Country-specific Zimbabwean news hubs for the UK, South Africa, USA and beyond. Live FX corridors, flight guides, returning-home resources — built around where Zimbabweans actually live and read.",
        "canonical": "https://www.mutapatimes.com/diaspora/",
    }

    hero = """  <header class="dp-hero">
    <div class="dp-hero-inner">
      <p class="dp-eyebrow">The Mutapa Times &middot; Diaspora</p>
      <h1 class="dp-title">Zimbabwe news for the global diaspora</h1>
      <p class="dp-stand">The Mutapa Times is operated from the United Kingdom and read across more than thirty countries. This is the front door for the four largest Zimbabwean diaspora clusters — pick yours, or start at the top.</p>
      <hr class="dp-rule">
    </div>
  </header>

  <section class="dp-cards" aria-label="Diaspora hubs">
    <a class="dp-card" href="/diaspora/uk/">
      <p class="dp-card-flag">🇬🇧 United Kingdom</p>
      <p class="dp-card-name">Zim diaspora &middot; UK</p>
      <p class="dp-card-meta">London, Luton, Slough, Manchester, Leeds. The site is operated from the UK and our biggest converting readership.</p>
    </a>
    <a class="dp-card" href="/diaspora/south-africa/">
      <p class="dp-card-flag">🇿🇦 South Africa</p>
      <p class="dp-card-name">Zim diaspora &middot; SA</p>
      <p class="dp-card-meta">Johannesburg, Pretoria, Cape Town, Durban. The largest single concentration of Zimbabweans living abroad.</p>
    </a>
    <a class="dp-card" href="/diaspora/usa/">
      <p class="dp-card-flag">🇺🇸 United States</p>
      <p class="dp-card-name">Zim diaspora &middot; USA</p>
      <p class="dp-card-meta">Atlanta, DMV (DC/Maryland/Virginia), Dallas/Fort Worth, Houston. Smaller but a fast-growing professional cluster.</p>
    </a>
    <a class="dp-card dp-card-soon" href="#" aria-disabled="true">
      <p class="dp-card-flag">🇨🇦 Canada</p>
      <p class="dp-card-name">Zim diaspora &middot; Canada</p>
      <p class="dp-card-meta">Toronto, Calgary, Edmonton, Winnipeg.</p>
    </a>
    <a class="dp-card dp-card-soon" href="#" aria-disabled="true">
      <p class="dp-card-flag">🇦🇺 Australia</p>
      <p class="dp-card-name">Zim diaspora &middot; Australia</p>
      <p class="dp-card-meta">Sydney, Perth, Melbourne, Brisbane.</p>
    </a>
    <a class="dp-card dp-card-soon" href="#" aria-disabled="true">
      <p class="dp-card-flag">🇮🇪 Ireland</p>
      <p class="dp-card-name">Zim diaspora &middot; Ireland</p>
      <p class="dp-card-meta">Dublin, Cork, Limerick.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">01</span><span>What you get</span></p>
    <h2 class="dp-section-h2">What each country hub gives you</h2>
    <div class="dp-prose">
      <p>Each country page pulls together the parts of the site most relevant to Zimbabweans living in that country: the news angles, the remittance corridor, the practical guides, the flight routes home, and the contact points for press and partnership work that already operate from that jurisdiction.</p>
      <ul>
        <li><strong>News.</strong> The same editorial briefings the rest of the site runs, framed for the country you read from.</li>
        <li><strong>FX corridor.</strong> Live rates for sending money home in the relevant currency &mdash; pounds, rand, or US dollars &mdash; via Wise, WorldRemit, Mukuru and the bank-to-bank routes.</li>
        <li><strong>Flights.</strong> The realistic options out of your nearest hub: who flies, what fares look like across the year, and the layover patterns the diaspora actually uses.</li>
        <li><strong>Practical resources.</strong> Cooking, returning home, schools for the kids, the airport boards when you land.</li>
      </ul>
    </div>
  </section>

  <section class="dp-mod">
    <a class="dp-mod-card" href="/fx/">
      <p class="dp-mod-tag">Money</p>
      <h3 class="dp-mod-title">Live FX rates</h3>
      <p class="dp-mod-desc">Pound, rand, USD and ZiG &middot; updated continuously.</p>
    </a>
    <a class="dp-mod-card" href="/flights/">
      <p class="dp-mod-tag">Travel</p>
      <h3 class="dp-mod-title">Flights home</h3>
      <p class="dp-mod-desc">All corridors, all seasons, live prices.</p>
    </a>
    <a class="dp-mod-card" href="/articles">
      <p class="dp-mod-tag">News</p>
      <h3 class="dp-mod-title">All articles</h3>
      <p class="dp-mod-desc">Original analysis + 100+ sources, daily.</p>
    </a>
    <a class="dp-mod-card" href="/subscribe">
      <p class="dp-mod-tag">Briefing</p>
      <h3 class="dp-mod-title">Newsletter</h3>
      <p class="dp-mod-desc">Twice-weekly, free, one-click unsubscribe.</p>
    </a>
  </section>

  <section class="dp-sources" aria-label="About this hub">
    <h2>About this hub</h2>
    <p>Pages updated 26 May 2026. We do not collect or geo-target on the searcher's country &mdash; these pages exist so that Google can serve country-specific results to country-specific queries. If you are reading from a country that isn't yet listed, the main <a href="/" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">site front page</a> is the right place to start, and we are interested in hearing where to add next: <a href="mailto:news@mutapatimes.com?subject=Diaspora%20hub%20request" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">news@mutapatimes.com</a>.</p>
  </section>
"""

    return render(meta, hero, "", country_for_crumb=None, self_key="hub")


# ─── United Kingdom (/diaspora/uk/) ──────────────────────────────────


def page_uk():
    meta = {
        "title": "Zimbabwe news for the UK-based diaspora | The Mutapa Times",
        "description": "Britain has one of the largest Zimbabwean diaspora communities. The Mutapa Times is operated from the United Kingdom. London-Harare flights, pound-to-ZiG remittance, returning-home guidance, daily news.",
        "canonical": "https://www.mutapatimes.com/diaspora/uk/",
        "lang": "en-GB",
    }

    hero = """  <header class="dp-hero">
    <div class="dp-hero-inner">
      <p class="dp-eyebrow"><a href="/diaspora/">Diaspora</a> &middot; United Kingdom</p>
      <h1 class="dp-title">Zimbabwe news for the UK-based diaspora</h1>
      <p class="dp-stand">Britain hosts one of the largest Zimbabwean communities outside the country, concentrated in London, Luton, Slough, Manchester, Leeds and Birmingham. The Mutapa Times is operated from the United Kingdom and writes, in large part, for the readers who live in it.</p>
      <hr class="dp-rule">
    </div>
  </header>

  <section class="dp-cards" aria-label="UK-Zim resources">
    <a class="dp-card" href="/fx/">
      <p class="dp-card-flag">🇬🇧 → 🇿🇼 Money</p>
      <p class="dp-card-name">Send pounds to Zimbabwe</p>
      <p class="dp-card-meta">Live GBP &rarr; ZiG and GBP &rarr; USD rates. Compare Wise, WorldRemit, Mukuru, Sasai and the bank-to-bank routes.</p>
    </a>
    <a class="dp-card" href="/flights/london-to-harare/">
      <p class="dp-card-flag">🇬🇧 → 🇿🇼 Travel</p>
      <p class="dp-card-name">London to Harare flights</p>
      <p class="dp-card-meta">Emirates, Qatar, Ethiopian, Kenya Airways, South African. From £700 off-peak. Live fares per origin.</p>
    </a>
    <a class="dp-card" href="/moving-to-zimbabwe/">
      <p class="dp-card-flag">🇬🇧 → 🇿🇼 Return</p>
      <p class="dp-card-name">Moving to Zimbabwe from the UK</p>
      <p class="dp-card-meta">A full guide for British residents and returning Zimbabweans: schools, banking, healthcare, vehicle imports.</p>
    </a>
    <a class="dp-card" href="/articles">
      <p class="dp-card-flag">📰 News</p>
      <p class="dp-card-name">All news, daily</p>
      <p class="dp-card-meta">Original analysis plus 100+ Zimbabwean and international sources, refreshed every three hours.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">01</span><span>What's happening</span></p>
    <h2 class="dp-section-h2">UK-Zim stories worth reading this week</h2>
    <div class="dp-prose">
      <p>The trade relationship between Britain and Zimbabwe is in an unusual moment. The Department for Business and Trade published its latest <a href="/articles/2026-05-14-zimbabwe-tobacco-96-percent-uk-trade-monoculture.html">UK-Zimbabwe trade factsheet on 14 May</a>, and the numbers tell a structural story: 96% of all goods Zimbabwe sells Britain is beverages and tobacco, the bilateral total is down 7.7% on the year, and <a href="/articles/2026-05-14-uk-zimbabwe-services-trade-freefall.html">services trade is in freefall</a>. On the export side, <a href="/articles/2026-05-14-uk-cars-medicines-machinery-zimbabwe-up.html">British cars, medicines and machinery</a> are the lines holding up.</p>
      <p>On the airline side, <a href="/articles/2026-05-15-air-zimbabwe-to-resume-london-flights-by-june.html">Air Zimbabwe is preparing to resume London flights by June</a>, the first time the route has been served by the national carrier in years. The commercial logic is partly diaspora-driven.</p>
    </div>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">02</span><span>Money home</span></p>
    <h2 class="dp-section-h2">The pound-to-ZiG corridor</h2>
    <div class="dp-prose">
      <p>The UK is one of the most established corridors for Zimbabwean remittances by volume. The competitive set is well-defined: <strong>Wise</strong> for transparent bank-to-bank transfers, <strong>WorldRemit</strong> and <strong>Mukuru</strong> for cash collection at OK Zimbabwe, NetOne and EcoCash outlets, <strong>Sasai</strong> for mobile-to-mobile, and the high-street banks for larger transfers.</p>
      <p>The mid-market pound rate against the ZiG is published on our <a href="/fx/">live FX page</a>; each provider's effective rate (after fees and FX margin) is calculated against that midmarket and listed alongside.</p>
    </div>
  </section>

  <section class="dp-mod">
    <a class="dp-mod-card" href="/harare-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Harare news</h3>
      <p class="dp-mod-desc">The capital, daily.</p>
    </a>
    <a class="dp-mod-card" href="/bulawayo-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Bulawayo news</h3>
      <p class="dp-mod-desc">The second city, daily.</p>
    </a>
    <a class="dp-mod-card" href="/economy">
      <p class="dp-mod-tag">Data</p>
      <h3 class="dp-mod-title">Live economy</h3>
      <p class="dp-mod-desc">GDP, inflation, trade.</p>
    </a>
    <a class="dp-mod-card" href="/jobs">
      <p class="dp-mod-tag">Work</p>
      <h3 class="dp-mod-title">Jobs in Zimbabwe</h3>
      <p class="dp-mod-desc">Open roles, weekly.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">03</span><span>Returning home</span></p>
    <h2 class="dp-section-h2">If you are thinking about moving back</h2>
    <div class="dp-prose">
      <p>Our <a href="/moving-to-zimbabwe/">Moving to Zimbabwe guide</a> covers what we are most often asked about by UK-resident readers: schooling for children educated to the British curriculum, opening domestic and offshore-USD accounts, healthcare and medical aid, and the logistics of shipping or importing a vehicle. The guide is editorial and updated quarterly, and we point out where to corroborate with the embassy and the ZIMRA rules at time of move.</p>
    </div>
  </section>

  <section class="dp-sources" aria-label="About this page">
    <h2>About this page</h2>
    <p>The Mutapa Times is registered and operated from the United Kingdom. Editorial questions and press enquiries: <a href="mailto:news@mutapatimes.com" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">news@mutapatimes.com</a>. We do not detect or store the country of the reader; this page exists as a static SEO hub so that Google can connect UK-based searches for Zimbabwean news to the section of the site that already speaks to UK readers. Page last reviewed 26 May 2026.</p>
  </section>
"""

    return render(meta,
                  hero,
                  "",
                  country_for_crumb={"name": "United Kingdom",
                                     "url": "https://www.mutapatimes.com/diaspora/uk/"},
                  self_key="uk")


# ─── South Africa (/diaspora/south-africa/) ──────────────────────────


def page_sa():
    meta = {
        "title": "Zimbabwe news for the South Africa-based diaspora | The Mutapa Times",
        "description": "South Africa hosts the largest single concentration of Zimbabweans abroad — Johannesburg, Pretoria, Cape Town, Durban. Rand-to-ZiG remittance, JNB/CPT-Harare flights, daily news.",
        "canonical": "https://www.mutapatimes.com/diaspora/south-africa/",
        "lang": "en-ZA",
    }

    hero = """  <header class="dp-hero">
    <div class="dp-hero-inner">
      <p class="dp-eyebrow"><a href="/diaspora/">Diaspora</a> &middot; South Africa</p>
      <h1 class="dp-title">Zimbabwe news for the South Africa-based diaspora</h1>
      <p class="dp-stand">South Africa hosts the largest single concentration of Zimbabweans living outside Zimbabwe, with deep communities in Johannesburg, Pretoria, Cape Town and Durban. This is the front door to The Mutapa Times for SA-based readers.</p>
      <hr class="dp-rule">
    </div>
  </header>

  <section class="dp-cards" aria-label="SA-Zim resources">
    <a class="dp-card" href="/fx/">
      <p class="dp-card-flag">🇿🇦 → 🇿🇼 Money</p>
      <p class="dp-card-name">Send rand to Zimbabwe</p>
      <p class="dp-card-meta">Live ZAR &rarr; ZiG and ZAR &rarr; USD rates. Mukuru, Hello Paisa, Shoprite Money, Sasai, EcoCash and the cross-border bank routes.</p>
    </a>
    <a class="dp-card" href="/flights/johannesburg-to-harare/">
      <p class="dp-card-flag">🇿🇦 → 🇿🇼 Travel</p>
      <p class="dp-card-name">Joburg to Harare flights</p>
      <p class="dp-card-meta">1h 50m direct. SAA, Airlink, FastJet. The busiest regional corridor. From R3,500.</p>
    </a>
    <a class="dp-card" href="/flights/cape-town-to-harare/">
      <p class="dp-card-flag">🇿🇦 → 🇿🇼 Travel</p>
      <p class="dp-card-name">Cape Town to Harare flights</p>
      <p class="dp-card-meta">3h direct on Airlink, or via JNB. From R5,500.</p>
    </a>
    <a class="dp-card" href="/articles">
      <p class="dp-card-flag">📰 News</p>
      <p class="dp-card-name">All news, daily</p>
      <p class="dp-card-meta">Original analysis plus 100+ Zimbabwean and international sources, refreshed every three hours.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">01</span><span>What's happening</span></p>
    <h2 class="dp-section-h2">SA-Zim stories worth reading this week</h2>
    <div class="dp-prose">
      <p>The Zimbabwe-South Africa border at Beitbridge handles the largest volume of legal and informal movement of any African land border. The trade and people corridor is its own beat on the site: <a href="/articles/2026-05-25-zimbabwe-deports-29-undocumented-mozambicans.html">deportation and cross-border policing</a> is one strand, the <a href="/articles">commercial side of the corridor</a> — fuel, vehicles, retail goods, agricultural produce — is another.</p>
      <p>SADC-level moves matter here too. Zimbabwe hosted the <a href="/articles/2024-08-21-sadc-holds-44th-annual-summit-in-zimbabwe-as-regional-impera.html">44th SADC summit</a> in 2024, and the regional fisheries, infrastructure and free-trade-area integration files run through both capitals.</p>
    </div>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">02</span><span>Money home</span></p>
    <h2 class="dp-section-h2">The rand-to-ZiG corridor</h2>
    <div class="dp-prose">
      <p>South Africa is the highest-volume remittance corridor into Zimbabwe by some distance. The competitive set is dominated by <strong>Mukuru</strong> &mdash; founded for this exact corridor &mdash; alongside <strong>Hello Paisa</strong>, <strong>Shoprite Money Market</strong> (in-store), <strong>Sasai</strong> for mobile, and the major banks for bank-to-bank.</p>
      <p>The mid-market ZAR rate against the ZiG and against USD is published on our <a href="/fx/">live FX page</a>; effective rates (after fees and FX margin) for each named provider are calculated against that midmarket.</p>
    </div>
  </section>

  <section class="dp-mod">
    <a class="dp-mod-card" href="/harare-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Harare news</h3>
      <p class="dp-mod-desc">The capital, daily.</p>
    </a>
    <a class="dp-mod-card" href="/bulawayo-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Bulawayo news</h3>
      <p class="dp-mod-desc">Closest large city to the SA border.</p>
    </a>
    <a class="dp-mod-card" href="/economy">
      <p class="dp-mod-tag">Data</p>
      <h3 class="dp-mod-title">Live economy</h3>
      <p class="dp-mod-desc">GDP, inflation, trade.</p>
    </a>
    <a class="dp-mod-card" href="/airports/">
      <p class="dp-mod-tag">Travel</p>
      <h3 class="dp-mod-title">Live arrivals/departures</h3>
      <p class="dp-mod-desc">HRE, BUQ, VFA &middot; real time.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">03</span><span>Returning home</span></p>
    <h2 class="dp-section-h2">Practical resources for SA-based Zimbabweans</h2>
    <div class="dp-prose">
      <p>For SA-resident Zimbabweans, the practical reading on the site clusters around the corridor: <a href="/articles">trade and customs coverage</a> for cross-border importers, the <a href="/economy">live economy page</a> for ZWG-rand FX management, and our <a href="/jobs">jobs board</a> for opportunities in Zimbabwean firms, including those with cross-border operations.</p>
      <p>Documentation and permits sit outside our editorial scope &mdash; for Zimbabwe Exemption Permit (ZEP) updates and consular notices, refer to the Zimbabwean Embassy in Pretoria or the Department of Home Affairs directly.</p>
    </div>
  </section>

  <section class="dp-sources" aria-label="About this page">
    <h2>About this page</h2>
    <p>The Mutapa Times is operated from the United Kingdom. For SA-based readers and partners: editorial enquiries to <a href="mailto:news@mutapatimes.com" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">news@mutapatimes.com</a>; advertising and partnerships to <a href="/advertising" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">/advertising</a>. We do not detect or store the country of the reader; this page exists so Google can connect SA-based searches for Zimbabwean news to the section of the site that already serves them. Page last reviewed 26 May 2026.</p>
  </section>
"""

    return render(meta,
                  hero,
                  "",
                  country_for_crumb={"name": "South Africa",
                                     "url": "https://www.mutapatimes.com/diaspora/south-africa/"},
                  self_key="sa")


# ─── USA (/diaspora/usa/) ────────────────────────────────────────────


def page_us():
    meta = {
        "title": "Zimbabwe news for the US-based diaspora | The Mutapa Times",
        "description": "A small but growing Zimbabwean community across Atlanta, the DMV, Dallas, Houston and the Northeast. USD-to-ZiG remittance, New York-Harare flights, daily news.",
        "canonical": "https://www.mutapatimes.com/diaspora/usa/",
        "lang": "en-US",
    }

    hero = """  <header class="dp-hero">
    <div class="dp-hero-inner">
      <p class="dp-eyebrow"><a href="/diaspora/">Diaspora</a> &middot; United States</p>
      <h1 class="dp-title">Zimbabwe news for the US-based diaspora</h1>
      <p class="dp-stand">The American Zimbabwean community is smaller than its UK or SA counterparts but is growing fast and is concentrated in a handful of metros &mdash; Atlanta, the DMV (DC / Maryland / Virginia), Dallas-Fort Worth, Houston, and the Northeast corridor from Philadelphia to Boston.</p>
      <hr class="dp-rule">
    </div>
  </header>

  <section class="dp-cards" aria-label="US-Zim resources">
    <a class="dp-card" href="/fx/">
      <p class="dp-card-flag">🇺🇸 → 🇿🇼 Money</p>
      <p class="dp-card-name">Send US dollars to Zimbabwe</p>
      <p class="dp-card-meta">Live USD &rarr; ZiG and live USD &rarr; cash-pickup rates. Wise, Remitly, Western Union, MoneyGram, Mukuru, Sasai.</p>
    </a>
    <a class="dp-card" href="/flights/new-york-to-harare/">
      <p class="dp-card-flag">🇺🇸 → 🇿🇼 Travel</p>
      <p class="dp-card-name">New York to Harare flights</p>
      <p class="dp-card-meta">One-stop on Ethiopian via Addis is the standard route. From $1,100. Doha and Dubai are the alternative hubs.</p>
    </a>
    <a class="dp-card" href="/moving-to-zimbabwe/">
      <p class="dp-card-flag">🇺🇸 → 🇿🇼 Return</p>
      <p class="dp-card-name">Moving back from the US</p>
      <p class="dp-card-meta">Banking, schooling, healthcare, vehicle imports &mdash; the version of the guide most relevant for returning American Zimbabweans.</p>
    </a>
    <a class="dp-card" href="/articles">
      <p class="dp-card-flag">📰 News</p>
      <p class="dp-card-name">All news, daily</p>
      <p class="dp-card-meta">Original analysis plus 100+ Zimbabwean and international sources, refreshed every three hours.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">01</span><span>What's happening</span></p>
    <h2 class="dp-section-h2">US-Zim stories worth reading this week</h2>
    <div class="dp-prose">
      <p>US policy on Zimbabwe runs primarily through OFAC's sanctions list, the State Department, and the dollar-denominated remittance corridor &mdash; all three of which touch the diaspora directly. Our coverage tracks the named individuals and entities on the SDN list, the response from Harare, and the practical knock-on effects in US-based banking relationships for Zimbabwean-controlled accounts.</p>
      <p>Healthcare, education and academic-link stories form another strand: the <a href="/articles/2024-07-17-in-zimbabwe-free-cancer-screenings-are-widely-available-trea.html">cancer-screening expansion in 2024</a>, the <a href="/articles">research-partnership coverage</a> with US universities, and the steady flow of Zimbabwean clinicians training in American teaching hospitals.</p>
    </div>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">02</span><span>Money home</span></p>
    <h2 class="dp-section-h2">The dollar-to-ZiG corridor</h2>
    <div class="dp-prose">
      <p>For US-based senders, the practical question is whether to send USD into a Zimbabwean USD-denominated nostro account, or to send to a ZiG endpoint via mobile money. Both have their place. The corridor is served by <strong>Wise</strong>, <strong>Remitly</strong>, <strong>Western Union</strong>, <strong>MoneyGram</strong>, <strong>Mukuru</strong>, and <strong>Sasai</strong>, with materially different fee structures depending on the amount sent and the receiving rail.</p>
      <p>The mid-market USD rate against the ZiG, and the prevailing parallel-market rate, are both published on our <a href="/fx/">live FX page</a> alongside each provider's effective rate.</p>
    </div>
  </section>

  <section class="dp-mod">
    <a class="dp-mod-card" href="/harare-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Harare news</h3>
      <p class="dp-mod-desc">The capital, daily.</p>
    </a>
    <a class="dp-mod-card" href="/bulawayo-news">
      <p class="dp-mod-tag">City</p>
      <h3 class="dp-mod-title">Bulawayo news</h3>
      <p class="dp-mod-desc">The second city, daily.</p>
    </a>
    <a class="dp-mod-card" href="/economy">
      <p class="dp-mod-tag">Data</p>
      <h3 class="dp-mod-title">Live economy</h3>
      <p class="dp-mod-desc">GDP, inflation, trade.</p>
    </a>
    <a class="dp-mod-card" href="/zse/">
      <p class="dp-mod-tag">Markets</p>
      <h3 class="dp-mod-title">ZSE listings</h3>
      <p class="dp-mod-desc">Live ZWG prices.</p>
    </a>
  </section>

  <section class="dp-section">
    <p class="dp-section-eyebrow"><span class="dp-section-num">03</span><span>Practical</span></p>
    <h2 class="dp-section-h2">Practical resources for US-based Zimbabweans</h2>
    <div class="dp-prose">
      <p>For voting and consular matters, refer to the Zimbabwean Embassy in Washington DC and its consulates &mdash; these are outside our editorial scope. For everything else &mdash; flights to <a href="/airports/">HRE / BUQ / VFA</a>, the <a href="/economy">economy snapshot</a>, the <a href="/fx/">parallel-market FX page</a>, the <a href="/jobs">Zimbabwe jobs board</a> for returnee opportunities &mdash; the site is structured to be useful from any time zone.</p>
    </div>
  </section>

  <section class="dp-sources" aria-label="About this page">
    <h2>About this page</h2>
    <p>The Mutapa Times is operated from the United Kingdom. For US-based readers and partners: editorial enquiries to <a href="mailto:news@mutapatimes.com" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">news@mutapatimes.com</a>; advertising and partnerships to <a href="/advertising" style="color:#c41e1e;border-bottom:1px solid currentColor;text-decoration:none;">/advertising</a>. We do not detect or store the country of the reader; this page exists so Google can connect US-based searches for Zimbabwean news to the section of the site already structured for an American audience. Page last reviewed 26 May 2026.</p>
  </section>
"""

    return render(meta,
                  hero,
                  "",
                  country_for_crumb={"name": "United States",
                                     "url": "https://www.mutapatimes.com/diaspora/usa/"},
                  self_key="us")


# ─── Main ────────────────────────────────────────────────────────────


def main():
    pages = [
        ("diaspora/index.html", page_hub()),
        ("diaspora/uk/index.html", page_uk()),
        ("diaspora/south-africa/index.html", page_sa()),
        ("diaspora/usa/index.html", page_us()),
    ]
    for rel, html in pages:
        path = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(html)
        print(f"wrote {rel} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
