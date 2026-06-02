#!/usr/bin/env python3
"""Flight microsite builder v2.

Differences from v1:
  - New readability CSS: bigger body type, wider hero, narrower prose,
    asymmetric layout (prose ~64ch, tables/widgets ~1080px), more vertical
    rhythm, stronger heading hierarchy with section eyebrows.
  - SEO-hardened: title tags include current month/year ("May 2026 fares
    from £X"), AggregateOffer schema with price range, FAQs expanded to
    8-10 questions per page including urgent-intent variants
    ("last minute", "this week", "tomorrow", "weekend"), Place schema
    on airport pages, hreflang/canonical pass.
  - Builds 6 corridor pages + hub + 2 airport pages in one run.
  - Idempotent: writing pages with the same content is fine.

Run:
  python3 scripts/build_flight_pages_v2.py
"""
import json, html, datetime
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT  = ROOT / "flights"
AIRPORTS_OUT = ROOT / "airports"   # airports moved out of /flights/ in May 2026
AIRPORTS_OUT.mkdir(exist_ok=True)

# Use real today (script reads system clock; safe for cron monthly refresh)
TODAY = datetime.date.today()
MONTH_NAME = TODAY.strftime("%B")
MONTH_YEAR = TODAY.strftime("%B %Y")
DATE_ISO = TODAY.isoformat()

widgets = json.loads((ROOT / "data" / "travelpayouts-widgets.json").read_text())["widgets"]

# Optional live-price data from scripts/fetch_flight_prices.py.
# When the file is missing/empty the build still completes — the price
# callouts simply don't render. Updated twice daily by the
# fetch-flight-prices GitHub Action.
_prices_path = ROOT / "data" / "flight-prices.json"
prices_by_slug = {}
prices_fetched_at = ""
if _prices_path.exists():
    try:
        _pp = json.loads(_prices_path.read_text())
        prices_by_slug = _pp.get("corridors", {}) or {}
        prices_fetched_at = _pp.get("fetched_at", "")
    except Exception:
        prices_by_slug = {}

# ---------------------------------------------------------------------------
# SHARED CHROME
# ---------------------------------------------------------------------------

TOPBAR = """<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>"""

DRAWER = """<div class="nav-drawer-backdrop" data-close-drawer aria-hidden="true"></div>
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
  <span class="nav-drawer-section">Information</span>
  <nav class="nav-drawer-info" aria-label="Information">
    <a href="/about">About</a>
    <a href="/advertising">Advertising</a>
    <a href="/terms">Terms</a>
    <a href="/privacy">Privacy</a>
  </nav>
</aside>"""

FOOTER = """<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/">News</a><span class="sep">·</span>
      <a href="/flights/">Flights</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/mining/">Mining</a><span class="sep">·</span>
      <a href="/schools/">Schools</a><span class="sep">·</span>
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
</script>
<script defer src="/js/nav.js"></script>"""

# Sponsored Harare hotels carousel — injected only on Harare-relevant pages
# (Harare corridors + the HRE airport page). Rendered by js/harare-hotels.js.
HOTELS_RAIL = (
    '\n  <!-- Sponsored stays — Harare hotels carousel (js/harare-hotels.js) -->\n'
    '  <section data-hotels-city="harare" data-hotels-variant="feature" data-count="10" '
    'aria-label="Sponsored hotel stays in Harare"></section>\n'
)
HOTELS_SCRIPT = '\n<script defer src="/js/harare-hotels.js?v=2"></script>'

TRACKING = """<!-- impact.com Universal Tracking Tag (UTT) -->
<script type="text/javascript">(function(i,m,p,a,c,t){c.ire_o=p;c[p]=c[p]||function(){(c[p].a=c[p].a||[]).push(arguments)};t=a.createElement(m);var z=a.getElementsByTagName(m)[0];t.async=1;t.src=i;z.parentNode.insertBefore(t,z)})('https://utt.impactcdn.com/P-A7333443-d775-4dfb-addf-0aa89ab29f151.js','script','impactStat',document,window);impactStat('transformLinks');impactStat('trackImpression');</script>
<!-- Travelpayouts Drive tracking -->
<script nowprocket data-noptimize="1" data-cfasync="false" data-wpfc-render="false" seraph-accel-crit="1" data-no-defer="1">
  (function () {
      var script = document.createElement("script");
      script.async = 1;
      script.src = 'https://emrldtp.cc/NTMyMTA3.js?t=532107';
      document.head.appendChild(script);
  })();
</script>"""

# ---------------------------------------------------------------------------
# READABILITY CSS — bigger type, asymmetric layout, generous whitespace
# ---------------------------------------------------------------------------

CSS = """
/* Flight pages v2 — readability-first */
body { background: #fbfaf6; }
.fl-page { color: var(--text); }

/* HERO — full-bleed feeling, generous padding */
.fl-hero { padding: 60px 24px 32px; max-width: 1200px; margin: 0 auto; }
.fl-hero-inner { max-width: 1080px; }
.fl-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 14px; }
.fl-eyebrow a { color: inherit; text-decoration: none; border-bottom: 1px solid transparent; }
.fl-eyebrow a:hover { border-bottom-color: var(--accent); }
.fl-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(2.2em, 5.5vw, 3.6em); line-height: 1.05; color: var(--ink);
  margin: 0 0 18px; letter-spacing: -0.022em; max-width: 18ch; }
.fl-stand { font-family: 'Inter', system-ui, sans-serif; font-size: clamp(1.05em, 1.6vw, 1.25em);
  line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 56ch;
  font-weight: 400; }
.fl-rule { width: 56px; height: 3px; background: var(--accent); border: 0; margin: 22px 0 0; }

/* QUICKFACTS strip — large numbers, scan-friendly */
.fl-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px; max-width: 1080px; margin: 32px auto 12px; padding: 0 24px; }
.fl-fact { padding: 18px 20px; background: #fff; border: 1px solid var(--rule);
  border-radius: 10px; }
.fl-fact-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.66em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 6px; font-weight: 600; }
.fl-fact-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.5em;
  line-height: 1.1; color: var(--ink); margin: 0; font-weight: 700;
  letter-spacing: -0.01em; }

/* WIDGET — wider than prose, gets its own breathing room */
.fl-widget-wrap { max-width: 1080px; margin: 26px auto 36px; padding: 0 24px; }
.fl-widget-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 10px; font-weight: 700; }
.fl-widget { background: #fff; border: 1px solid var(--rule); border-radius: 10px;
  padding: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.03); }

/* SECTION SHELL — numbered eyebrow + big serif h2 + tight rule */
.fl-section { max-width: 1080px; margin: 56px auto 0; padding: 0 24px; }
.fl-section-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.68em;
  letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; display: flex; align-items: baseline; gap: 12px; }
.fl-section-num { color: var(--text-light); font-weight: 500; }
.fl-section-h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.55em, 2.6vw, 1.95em); line-height: 1.15; color: var(--ink);
  margin: 0 0 18px; letter-spacing: -0.015em; max-width: 28ch; }

/* PROSE — narrower for readability, larger type, generous leading */
.fl-prose { max-width: 64ch; margin: 0; font-family: 'Inter', system-ui, sans-serif; }
.fl-prose p { font-size: 1.1em; line-height: 1.7; color: var(--text); margin: 0 0 18px; }
.fl-prose p:first-child::first-letter {
  font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 3.2em; float: left; line-height: 0.9; margin: 4px 8px 0 0;
  color: var(--ink);
}
.fl-prose ul, .fl-prose ol { font-size: 1.075em; line-height: 1.7;
  padding-left: 24px; margin: 0 0 18px; color: var(--text); }
.fl-prose li { margin-bottom: 8px; }
.fl-prose li::marker { color: var(--accent); }
.fl-prose a { color: var(--accent); text-decoration: none;
  border-bottom: 1px solid currentColor; padding-bottom: 1px; }
.fl-prose a:hover { color: var(--ink); }
.fl-prose strong { color: var(--ink); font-weight: 600; }

/* TABLE — uses full section width */
.fl-table-wrap { max-width: 1080px; overflow-x: auto; }
.fl-table { width: 100%; border-collapse: collapse;
  font-family: 'Inter', system-ui, sans-serif; font-size: 1em;
  background: #fff; border: 1px solid var(--rule); border-radius: 10px; overflow: hidden;
  margin: 4px 0 22px; }
.fl-table thead th { text-align: left; padding: 14px 18px; background: #fbfaf6;
  border-bottom: 1px solid var(--rule); font-size: 0.7em; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--text-light); font-weight: 700; white-space: nowrap; }
.fl-table tbody td { padding: 14px 18px; border-bottom: 1px solid var(--rule);
  color: var(--text); line-height: 1.55; }
.fl-table tbody tr:last-child td { border-bottom: 0; }
.fl-table tbody tr:hover { background: #fbfaf6; }
.fl-table strong { color: var(--ink); }
.fl-table .fl-mon-price { text-align: right; font-variant-numeric: tabular-nums;
  font-family: 'Playfair Display', Georgia, serif; font-weight: 700; color: var(--ink); }

/* Live-fare callout: cheapest fare observed for this route today */
.fl-fare { max-width: 1080px; margin: 22px auto 0; padding: 0 24px; }
.fl-fare-inner { background: linear-gradient(135deg, #fbfaf6 0%, #f3eedf 100%);
  border: 1px solid var(--rule); border-left: 4px solid #1f7a3e;
  border-radius: 10px; padding: 18px 22px;
  display: grid; grid-template-columns: 1fr auto; gap: 14px 24px;
  align-items: center; font-family: 'Inter', system-ui, sans-serif; }
.fl-fare-label { font-size: 0.7em; letter-spacing: 0.18em; text-transform: uppercase;
  color: #1f7a3e; font-weight: 700; margin: 0 0 4px;
  display: inline-flex; align-items: center; gap: 8px; }
.fl-fare-pulse { width: 7px; height: 7px; background: #1f7a3e; border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(31,122,62,0.6); animation: flFarePulse 2s infinite; }
@keyframes flFarePulse {
  0%   { box-shadow: 0 0 0 0 rgba(31,122,62,0.6); }
  70%  { box-shadow: 0 0 0 7px rgba(31,122,62,0); }
  100% { box-shadow: 0 0 0 0 rgba(31,122,62,0); }
}
.fl-fare-price { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.6em, 3vw, 2.1em); color: var(--ink); margin: 0;
  line-height: 1.1; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; }
.fl-fare-meta { font-size: 0.9em; color: var(--text-mid); margin: 4px 0 0;
  line-height: 1.5; }
.fl-fare-meta strong { color: var(--ink); }
.fl-fare-asof { font-size: 0.72em; color: var(--text-light); margin: 6px 0 0;
  letter-spacing: 0.04em; }
.fl-fare-cta { font-family: 'Inter', system-ui, sans-serif; font-weight: 600;
  font-size: 0.92em; padding: 10px 18px; background: var(--ink); color: #fff;
  text-decoration: none; border-radius: 6px; white-space: nowrap;
  align-self: center; }
.fl-fare-cta:hover { background: var(--accent); color: #fff; text-decoration: none; }
@media (max-width: 640px) {
  .fl-fare-inner { grid-template-columns: 1fr; }
  .fl-fare-cta { justify-self: start; }
}

/* PULLOUT callout — for key insights */
.fl-pullout { max-width: 720px; margin: 24px 0;
  padding: 22px 26px; background: #fff; border: 1px solid var(--rule);
  border-left: 4px solid var(--accent); border-radius: 8px;
  font-family: 'Playfair Display', Georgia, serif; font-style: normal;
  font-size: 1.2em; line-height: 1.45; color: var(--ink); font-weight: 700;
  letter-spacing: -0.005em; }

/* FAQ — accordion, generous padding */
.fl-faq { max-width: 800px; margin: 0; }
.fl-faq details { background: #fff; border: 1px solid var(--rule); border-radius: 10px;
  padding: 0; margin: 0 0 10px; transition: border-color 0.15s; }
.fl-faq details[open] { border-color: var(--accent); }
.fl-faq summary { padding: 18px 22px; font-weight: 600; cursor: pointer;
  color: var(--ink); font-size: 1.075em; list-style: none;
  font-family: 'Inter', system-ui, sans-serif; }
.fl-faq summary::-webkit-details-marker { display: none; }
.fl-faq summary::after { content: '＋'; float: right; color: var(--accent);
  font-weight: 400; font-size: 1.3em; line-height: 1; }
.fl-faq details[open] summary::after { content: '−'; }
.fl-faq details > p { padding: 0 22px 20px; margin: 0; line-height: 1.7;
  color: var(--text); font-size: 1.025em;
  font-family: 'Inter', system-ui, sans-serif; }

/* CTA banner (eSIM cross-sell) */
.fl-cta { max-width: 1080px; margin: 32px auto; padding: 0 24px; }
.fl-cta-inner { background: linear-gradient(135deg, #fbfaf6 0%, #f5f0e0 100%);
  border: 1px solid var(--rule); border-left: 4px solid var(--accent);
  border-radius: 10px; padding: 22px 28px;
  font-family: 'Inter', system-ui, sans-serif; }
.fl-cta h3 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; margin: 0 0 6px; color: var(--ink); letter-spacing: -0.01em; }
.fl-cta p { font-size: 1em; line-height: 1.6; color: var(--text-mid); margin: 0 0 12px; }
.fl-cta a.fl-cta-btn { display: inline-block; padding: 10px 18px;
  background: var(--ink); color: #fff; text-decoration: none;
  font-weight: 600; border-radius: 6px; font-size: 0.95em;
  transition: background 0.15s; }
.fl-cta a.fl-cta-btn:hover { background: var(--accent); color: #fff; }

/* RELATED grid */
.fl-related { max-width: 1080px; margin: 32px auto; padding: 0 24px; }
.fl-related-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
.fl-related-link { display: block; padding: 18px 20px; background: #fff;
  border: 1px solid var(--rule); border-radius: 10px; text-decoration: none;
  color: var(--text); font-family: 'Inter', system-ui, sans-serif;
  transition: border-color 0.15s, transform 0.15s; }
.fl-related-link:hover { border-color: var(--accent); transform: translateY(-2px);
  text-decoration: none; color: var(--text); }
.fl-related-link strong { color: var(--ink); display: block; margin-bottom: 4px;
  font-size: 1.02em; font-weight: 600; }
.fl-related-link span { font-size: 0.86em; color: var(--text-light); }

/* SOURCES */
.fl-sources { max-width: 1080px; margin: 40px auto 0; padding: 24px 24px 18px;
  border-top: 2px solid var(--ink);
  font-family: 'Inter', system-ui, sans-serif; }
.fl-sources h2 { font-size: 0.74em; letter-spacing: 0.2em; text-transform: uppercase;
  margin: 0 0 14px; color: var(--text-light); font-weight: 700;
  font-family: 'Inter', system-ui, sans-serif; }
.fl-sources ul { font-size: 0.95em; margin: 0 0 12px; padding-left: 24px;
  line-height: 1.65; color: var(--text); }
.fl-sources a { color: var(--ink); text-decoration: underline; }
.fl-sources-note { font-size: 0.82em; color: var(--text-light); margin: 0;
  line-height: 1.6; max-width: 64ch; }

.fl-back { text-align: center; margin: 40px 0 56px;
  font-family: 'Inter', system-ui, sans-serif; }
.fl-back a { font-size: 0.92em; color: var(--ink);
  border-bottom: 1px solid var(--accent); text-decoration: none; padding-bottom: 2px; }

/* HUB-specific: corridor cards */
.fl-corridors { display: grid; gap: 18px; padding: 0 24px 32px;
  max-width: 1080px; margin: 24px auto 0;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
.fl-corridor { display: flex; flex-direction: column; gap: 10px;
  padding: 22px; border: 1px solid var(--rule); border-radius: 10px;
  background: #fff; color: var(--text); text-decoration: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.fl-corridor:hover { border-color: var(--accent); text-decoration: none;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06); transform: translateY(-2px); }
.fl-corridor-route { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.1em; color: var(--text-light); margin: 0;
  text-transform: uppercase; font-weight: 600; }
.fl-corridor-name { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; line-height: 1.2; margin: 0; color: var(--ink);
  letter-spacing: -0.01em; }
.fl-corridor:hover .fl-corridor-name { color: var(--accent); }
.fl-corridor-meta { font-family: 'Inter', system-ui, sans-serif; font-size: 0.92em;
  color: var(--text-mid); margin: 4px 0 0; line-height: 1.55; }
.fl-corridor[data-status="planned"] { opacity: 0.55; cursor: default; pointer-events: none; }
.fl-corridor[data-status="planned"]::after { content: 'coming soon';
  display: inline-block; font-size: 0.66em; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-light); margin-top: 4px;
  font-family: 'Inter', system-ui, sans-serif; }

/* Hero banner image (full-width) */
.fl-hero-img { max-width: 1080px; margin: 4px auto 0; padding: 0 24px; }
.fl-hero-img-inner { position: relative; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--rule); aspect-ratio: 21/9; background: #f0ece4; }
.fl-hero-img-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }
@media (max-width: 640px) {
  .fl-hero-img-inner { aspect-ratio: 16/9; }
}

/* Live arrivals/departures board (Avionio) */
.avionio-board { max-width: 1080px; margin: 26px auto 36px; padding: 0 24px; }
.avionio-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 10px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
.avionio-live-dot { display: inline-block; width: 8px; height: 8px;
  background: #28a745; border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(40,167,69,0.6);
  animation: avionioPulse 2s infinite; }
@keyframes avionioPulse {
  0%   { box-shadow: 0 0 0 0 rgba(40,167,69,0.6); }
  70%  { box-shadow: 0 0 0 8px rgba(40,167,69,0); }
  100% { box-shadow: 0 0 0 0 rgba(40,167,69,0); }
}
.avionio-tabs { display: flex; gap: 4px; border-bottom: 2px solid var(--rule); margin: 0; }
.avionio-tab { background: none; border: 0; padding: 12px 22px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.95em; font-weight: 600;
  color: var(--text-light); cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: color 0.15s, border-color 0.15s; letter-spacing: 0.01em; }
.avionio-tab:hover { color: var(--ink); }
.avionio-tab.is-active { color: var(--accent); border-bottom-color: var(--accent); }
.avionio-pane { display: none; background: #fff; border: 1px solid var(--rule);
  border-top: 0; border-radius: 0 0 10px 10px; overflow: hidden; }
.avionio-pane.is-active { display: block; }
.avionio-frame { width: 100%; min-height: 500px; display: block; border: 0; }
.avionio-credit { font-size: 0.78em; color: var(--text-light); text-align: right;
  margin: 8px 0 0; font-family: 'Inter', system-ui, sans-serif; }
.avionio-credit a { color: var(--text-mid); text-decoration: none;
  border-bottom: 1px solid var(--rule); }

@media (max-width: 640px) {
  .fl-hero { padding: 40px 20px 24px; }
  .fl-prose p:first-child::first-letter { font-size: 2.6em; }
  .avionio-tab { padding: 10px 14px; font-size: 0.88em; }
}
"""

# ---------------------------------------------------------------------------
# COMMON HEAD
# ---------------------------------------------------------------------------

def page_head(title, canonical, desc, og_desc, schemas_inline, depth=2):
    """depth: 2 = /flights/<slug>/, 1 = /flights/"""
    rel = "../" * depth
    schemas_html = "\n".join(f'<script type="application/ld+json">{s}</script>' for s in schemas_inline)
    return f"""<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link rel="canonical" href="{canonical}">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="{rel}site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="{rel}icon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="{rel}css/normalize.css">
    <link rel="stylesheet" href="{rel}css/main.css?v=102">
    <link rel="icon" type="image/png" sizes="32x32" href="{rel}img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="{rel}img/favicon-16x16.png">
    <meta name="theme-color" content="#1a1a1a">
    <meta name="author" content="The Mutapa Times">
    <meta name="twitter:site" content="@mutapatimes">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(og_desc)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(title)}">
    <meta name="twitter:description" content="{html.escape(og_desc)}">
{schemas_html}
{TRACKING}
<style>{CSS}</style>
</head>"""

# ---------------------------------------------------------------------------
# CORRIDOR CONFIG
# ---------------------------------------------------------------------------

CORRIDORS = {
    "london-to-harare": {
        "title":  f"Cheap flights London to Harare — {MONTH_YEAR} fares from £700",
        "h1":     "Cheap flights London to Harare",
        "stand":  ("There are no direct flights between London and Harare; every routing is one-stop via the Gulf or Africa. "
                   "Live prices in GBP below, and the practical guide to who flies the route, when fares move, and what to budget."),
        "flag_from": "🇬🇧", "flag_to": "🇿🇼",
        "origin_short": "London", "origin_full": "London (LON)",
        "dest_short": "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "GBP", "currency_sym": "£",
        "widget_key": "london-harare",
        "distance": "8,200 km", "flight_time": "13–15 hrs", "stops": "1 (no direct)",
        "low_fare": 700, "high_fare": 2200,
        "fare_range_label": "£700–£2,200",
        "lead": (f"London to Harare is the diaspora's busiest corridor, but it has not had a direct flight for years. Every itinerary involves "
                 f"one stop — Dubai, Doha, Addis Ababa, Nairobi or Johannesburg — and your choice of hub matters more than your choice of airline. "
                 f"In {MONTH_YEAR}, Qatar via Doha and Ethiopian via Addis Ababa are the cheapest reliable options at the £700–£900 mark for typical "
                 f"low-season weeks. Emirates via Dubai costs more but offers the most consistent schedule."),
        "airlines": [
            ("Qatar Airways",      "Doha (DOH)",          "£720–£950",  "Often the cheapest reliable option from the UK. Good lounge access in Doha."),
            ("Ethiopian Airlines", "Addis Ababa (ADD)",   "£700–£900",  "Cheapest of the five. Busier hub at ADD; allow 3+ hours."),
            ("Emirates",           "Dubai (DXB)",         "£850–£1,150","Most reliable schedule. Premium product. Skywards lounge access from Silver tier."),
            ("Kenya Airways",      "Nairobi (NBO)",       "£780–£1,000","Decent African network. Occasionally competitive on price."),
            ("BA + Airlink",       "Johannesburg (JNB)",  "£900–£1,300","Watch the through-checking: the JNB–HRE leg can be on a separate ticket."),
        ],
        "season":  (f"In {MONTH_YEAR}, low-season pricing applies — book within the next 8–12 weeks for the cheaper end of the range. "
                    "The expensive windows on this corridor are mid-December to mid-January (Zimbabwean Christmas), July (UK school holidays aligned "
                    "with Zim school holidays), and Easter week. Last-minute fares in those windows routinely exceed £2,000."),
        "layovers": [
            ("Dubai (Emirates)",  "The most comfortable layover. Massive airport, easy connections, lounges accessible on Skywards Silver and above."),
            ("Doha (Qatar)",      "Similar comfort to Dubai. Often the cheapest of the Gulf options."),
            ("Addis Ababa (Ethiopian)", "The cheapest but the airport is busier. Connections can be tight — allow 3 hours minimum."),
            ("Nairobi (Kenya Airways)", "Reasonable, African hub feel. Connections are generally on schedule."),
            ("Johannesburg (BA + Airlink)", "The JNB–HRE onward leg is operated by Airlink and is on a separate ticket in some bookings. Check this carefully or you'll re-clear immigration with no through-checked luggage."),
        ],
        "baggage":  ("Emirates, Qatar and Ethiopian all permit 2 × 23 kg checked in economy on the UK–Africa long-haul. Kenya Airways and BA-Airlink "
                     "itineraries often include only 1 × 23 kg — check before booking, and budget £40–80 per extra bag if you need it. Excess-baggage "
                     "fees at the check-in counter are 3–5× what you'd pay if added at booking."),
        "visa":     ("UK passport holders need a Zimbabwe visa but it's issued on arrival at Harare International. US$55 cash for single-entry, US$70 "
                     "for double, US$50 for the KAZA UniVisa (Zimbabwe + Zambia). Bring USD cash; the visa desk does not accept card. See our "
                     "<a href=\"/moving-to-zimbabwe/visa-on-arrival.html\">visa on arrival guide</a> for the full process."),
        "pullout":  "The single-biggest driver of price on London–Harare is how far ahead you book — not which airline you choose.",
        "faqs": [
            ("How much is a flight from London to Harare today?",
             "Typical return fares are £700–£1,200 in low season (February to May, September to early November) and £1,400–£2,200 in high season (mid-December to mid-January, July, Easter week). Live prices for your specific dates are in the search widget above."),
            ("Are there any direct flights from London to Harare?",
             "No. There are currently no non-stop services between London and Harare. Every itinerary involves one stop at the carrier's hub (Dubai, Doha, Addis Ababa, Nairobi or Johannesburg)."),
            ("How long is the flight from London to Harare?",
             "13 to 15 hours including the stop, depending on routing. Emirates via Dubai is about 13.5 hours door to door; Ethiopian via Addis is around 14 hours; Kenya Airways via Nairobi is 14–15 hours. The pure flight time across both legs is about 10–11 hours; the rest is the layover."),
            ("When should I book?",
             "Eight to twelve weeks ahead for the cheaper end of the range. For Christmas travel, book by August at the latest. Last-minute fares in December and July regularly exceed £2,000 return."),
            ("What is the cheapest month to fly from London to Harare?",
             "February, March, May, September and October are typically the cheapest months on this corridor. These months fall between the major Zimbabwean diaspora travel windows."),
            ("Can I fly from London to Harare tomorrow?",
             "Yes — there are daily departures via Dubai, Doha, Addis Ababa and Nairobi, so a next-day booking is always possible. Expect to pay a premium of £400–£900 versus an 8-week advance booking, more in peak weeks."),
            ("What are the cheapest last-minute flights from London to Harare this week?",
             "Last-minute on this corridor is usually Qatar via Doha or Ethiopian via Addis — both have daily availability and aggressive yield management. Run the live widget above for your exact dates; same-week bookings in low season can still come in under £1,200 return."),
            ("Which airline is best from London to Harare?",
             "Emirates for reliability and schedule comfort, Qatar for the cheapest of the premium options, Ethiopian for the lowest fare overall. Avoid BA + Airlink unless the through-baggage policy is explicit on your specific booking."),
            ("Do I need a visa to fly from London to Zimbabwe?",
             "British passport holders need a visa, but it's issued on arrival at Harare International for US$55 cash (single entry) or US$50 for the KAZA UniVisa (Zimbabwe + Zambia). No advance application is required."),
            ("Is it safe to fly to Harare?",
             "Yes. All five carriers (Emirates, Qatar, Ethiopian, Kenya Airways, SAA/BA) maintain standard international safety records on the route. Harare's airport (HRE) was extensively renovated in 2017–2022 and meets ICAO standards."),
        ],
        "related": [
            ("Flights from Harare",         "/flights/from-harare/",                       "Returning to London"),
            ("Send GBP to Zimbabwe",        "/fx/send-money-from-uk-to-zimbabwe/",         "Cheapest providers"),
            ("Zimbabwe visa on arrival",    "/moving-to-zimbabwe/visa-on-arrival.html",   "The US$55 visa desk"),
            ("Harare airport (HRE)",        "/airports/harare/",                    "Arrivals, taxis, schedule"),
        ],
    },

    "sydney-to-harare": {
        "title": f"Cheap flights Sydney to Harare — {MONTH_YEAR} fares from A$1,800",
        "h1": "Cheap flights Sydney to Harare",
        "stand": ("Sydney to Harare is one of the longer diaspora routes in the world: 22–28 hours, one or two stops, via the Gulf or via "
                  "Perth then Joburg. Live prices in AUD below."),
        "flag_from": "🇦🇺", "flag_to": "🇿🇼",
        "origin_short": "Sydney", "origin_full": "Sydney (SYD)",
        "dest_short": "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "AUD", "currency_sym": "A$",
        "widget_key": "sydney-harare",
        "distance": "11,500 km", "flight_time": "22–28 hrs", "stops": "1–2",
        "low_fare": 1800, "high_fare": 3500,
        "fare_range_label": "A$1,800–A$3,500",
        "lead": (f"The Sydney–Harare corridor is one of the world's longer diaspora routes: 11,500 km of great-circle distance and 22–28 hours door-to-door. "
                 f"In {MONTH_YEAR}, the cheapest options route through Perth then Johannesburg on Qantas + SAA, with one-stop Gulf options on Qatar (via Doha) "
                 f"or Emirates (via Dubai) costing 10–20% more in exchange for fewer connections."),
        "airlines": [
            ("Qantas + Qatar codeshare", "Doha (DOH)",          "A$1,950–A$2,600", "Codeshare with Qatar. Single ticket, baggage through-checked."),
            ("Emirates",                 "Dubai (DXB)",          "A$2,100–A$2,800", "Reliable schedule, premium product."),
            ("Qantas + South African",   "Perth + Joburg (JNB)", "A$1,800–A$2,400", "Cheapest. Two stops. Check baggage through-checking carefully."),
            ("Ethiopian + Qantas",       "Addis Ababa (ADD)",    "A$2,000–A$2,700", "Single ticket from Qantas booking. Good fare in low season."),
        ],
        "season": ("Australia's cheap months on this corridor are <strong>February–May</strong> and <strong>August–early November</strong>. Peak is "
                   "<strong>December–January</strong> (Australian summer aligning with Zimbabwean diaspora Christmas) and <strong>June–July</strong>. "
                   "Book 12–16 weeks ahead; last-minute December fares from Sydney regularly exceed A$3,500."),
        "layovers": [
            ("Dubai (Emirates)",            "8–10 hour total layover possible — SYD–DXB is 14h, DXB–HRE adds another 7h with a 2–4h transit."),
            ("Doha (Qatar/Qantas)",         "Similar comfort to Dubai. Often the cheapest reliable one-stop option."),
            ("Perth + Joburg",              "The cheapest but the longest. SAA's JNB–HRE onward leg is on a separate ticket in some itineraries."),
        ],
        "baggage": "Qatar and Emirates both permit 2 × 23 kg checked in economy on Australia–Africa long-haul. Qantas + JNB itineraries vary by booking class.",
        "visa": "Australian passport holders need a visa for Zimbabwe but it's issued on arrival at HRE for US$55 cash. No advance application needed.",
        "pullout": "Two-stop routings via Perth + Johannesburg are usually 10–20% cheaper than one-stop Gulf routings — the trade-off is time, not safety.",
        "faqs": [
            ("How much is a flight from Sydney to Harare?",
             "A$1,800 to A$3,500 return depending on season and lead time. Cheapest months are February–May and August–early November; most expensive is December–January and June–July."),
            ("Are there direct flights from Sydney to Harare?",
             "No. Routings always have one or two stops, most commonly via Dubai, Doha, or Perth + Johannesburg."),
            ("How long is the flight from Sydney to Harare?",
             "22 to 28 hours including layovers. Pure flight time across two legs is around 18 hours; the rest is the transit stop."),
            ("What is the cheapest way to fly Sydney to Harare?",
             "Two-stop routings via Perth + Johannesburg (Qantas + South African) typically come in lowest, often under A$2,000 in low season. The trade-off is more total elapsed time."),
            ("Can I fly to Harare from Sydney this week?",
             "Yes — daily availability on Emirates and Qatar codeshares. Last-minute Sydney–Harare in low season can sit around A$2,400–A$2,800; peak weeks add A$500+."),
            ("What's the best airline for Sydney to Harare?",
             "Qatar (via Doha) for the best balance of price and product. Emirates (via Dubai) for the most reliable schedule. Avoid Perth + JNB routings if you can't afford the extra elapsed time."),
            ("Do Australian passport holders need a visa for Zimbabwe?",
             "Yes, but it's issued on arrival at Harare International for US$55 cash single-entry. No advance application needed. Bring USD cash."),
            ("When is the cheapest month to fly Sydney to Harare?",
             "February, March, April, August and October are typically the lowest-fare months on this corridor. Book 12–16 weeks ahead for the bottom of the range."),
        ],
        "related": [
            ("Send AUD to Zimbabwe",      "/fx/send-money-from-australia-to-zimbabwe/", "Cheapest providers"),
            ("Zimbabwe visa on arrival",  "/moving-to-zimbabwe/visa-on-arrival.html",   "The US$55 visa desk"),
            ("Harare airport (HRE)",      "/airports/harare/",                    "Arrivals, taxis, schedule"),
            ("AUD to ZWG rate",           "/fx/aud-to-zwg/",                             "Today's rate"),
        ],
    },

    "cape-town-to-harare": {
        "title": f"Cheap flights Cape Town to Harare — {MONTH_YEAR} fares from R5,500",
        "h1": "Cheap flights Cape Town to Harare",
        "stand": ("Cape Town to Harare is a 3-hour direct flight on Airlink, or via Johannesburg on SAA/FastJet at a lower fare. Live prices in ZAR below."),
        "flag_from": "🇿🇦", "flag_to": "🇿🇼",
        "origin_short": "Cape Town", "origin_full": "Cape Town (CPT)",
        "dest_short": "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "ZAR", "currency_sym": "R",
        "widget_key": "cape-town-harare",
        "distance": "2,200 km", "flight_time": "3 hrs direct, 5–7 hrs via JNB", "stops": "0 or 1",
        "low_fare": 5500, "high_fare": 12000,
        "fare_range_label": "R5,500–R12,000",
        "lead": (f"Cape Town to Harare is one of southern Africa's easier regional corridors: roughly 2,200 km, three hours direct on Airlink, "
                 f"or via Johannesburg on SAA or FastJet at a lower fare. SAA and Airlink share the route via codeshare, so check the actual operator "
                 f"on your specific itinerary before booking. In {MONTH_YEAR}, low-season pricing applies and the cheaper end of the range is achievable "
                 f"with 4–8 weeks of lead time."),
        "airlines": [
            ("Airlink",                "Direct CPT–HRE",        "R6,500–R9,500", "Daily direct. 3-hour scheduled."),
            ("South African Airways",  "Via Johannesburg (JNB)","R5,500–R10,000", "Codeshare with Airlink. Multiple JNB onward connections."),
            ("FastJet",                "Via Johannesburg (JNB)","R5,500–R8,500", "Budget carrier. Bags extra. Cheapest option in low season."),
            ("Kenya Airways",          "Via Nairobi (NBO)",     "R7,000–R12,000","Rarely competitive on this corridor unless onwards to East Africa."),
        ],
        "season": ("Cape Town's tourist high season (December–February) lifts the corridor because the inbound CPT leg fills. Cheapest months are "
                   "<strong>March–May</strong> and <strong>September–early November</strong>. Book 4–8 weeks ahead — this is a more reactive corridor "
                   "than the long-haul ones, and fares move within a smaller band."),
        "layovers": [
            ("Direct (Airlink)",     "No layover. 3-hour scheduled flight. The simplest routing if your dates work."),
            ("JNB (SAA / FastJet)",  "1.5h JNB layover typical. Adds 2–4 hours total but can save R1,000–R2,000 versus direct."),
        ],
        "baggage": ("Airlink direct allows 1 × 23 kg checked in economy as standard, with a second bag at booking for R500–R900. SAA via JNB varies "
                    "by class. FastJet is the budget option — bags are extra at R350–R700 per bag added at booking, more at the airport."),
        "visa": "South African passport holders do not need a visa for Zimbabwe for stays under 90 days. Just bring your passport.",
        "pullout": "If you can take a JNB connection, FastJet via Johannesburg saves R1,500–R2,000 versus direct on Airlink.",
        "faqs": [
            ("How much is a flight from Cape Town to Harare?",
             "R5,500 to R12,000 return depending on direct vs one-stop and lead time. Direct on Airlink is usually R6,500–R9,500; via Joburg with SAA or FastJet can dip below R6,000 in low season."),
            ("Are there direct flights from Cape Town to Harare?",
             "Yes. Airlink operates direct CPT–HRE with a scheduled flight time of around 3 hours. SAA and FastJet route via Johannesburg, which is cheaper but longer."),
            ("How long is the direct flight from Cape Town to Harare?",
             "Approximately 3 hours direct on Airlink. Via Johannesburg the total journey time is 5–7 hours including the layover."),
            ("What is the cheapest way to fly Cape Town to Harare?",
             "Via Johannesburg with FastJet or SAA, booked 4–8 weeks ahead in low season (March–May, September–early November), can sit at R5,500–R6,500 return."),
            ("Can I book a Cape Town to Harare flight for this weekend?",
             "Yes — daily availability on Airlink direct and via JNB on SAA and FastJet. Same-week booking in low season is typically R7,500–R9,500 return; peak weeks add R2,000+."),
            ("Do South Africans need a visa for Zimbabwe?",
             "No. South African passport holders can visit Zimbabwe visa-free for up to 90 days. Just bring your passport."),
            ("Is FastJet safe?",
             "Yes. FastJet has a clean operating record and standard ICAO oversight via Zimbabwe's Civil Aviation Authority. The 'budget' label is about price and baggage, not safety."),
            ("What's the cheapest month to fly Cape Town to Harare?",
             "April, May, September, October are typically lowest. The corridor lifts in late November–February (tourism into CPT, holidays out of HRE)."),
        ],
        "related": [
            ("Johannesburg to Harare",     "/flights/johannesburg-to-harare/",         "Onward connection guide"),
            ("ZAR to ZWG rate",            "/fx/zar-to-zwg/",                          "Today's rate"),
            ("Send ZAR to Zimbabwe",       "/fx/send-money-from-south-africa-to-zimbabwe/", "Cheapest providers"),
            ("Harare airport (HRE)",       "/airports/harare/",                  "Arrivals, taxis, schedule"),
        ],
    },

    "johannesburg-to-harare": {
        "title": f"Cheap flights Johannesburg to Harare — {MONTH_YEAR} fares from R3,500",
        "h1": "Cheap flights Johannesburg to Harare",
        "stand": ("Johannesburg to Harare is the busiest air corridor between Zimbabwe and South Africa. Daily frequencies on SAA, Airlink and "
                  "FastJet; 1h 50m scheduled flight time. Live prices in ZAR below."),
        "flag_from": "🇿🇦", "flag_to": "🇿🇼",
        "origin_short": "Johannesburg", "origin_full": "Johannesburg (JNB)",
        "dest_short": "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "ZAR", "currency_sym": "R",
        "widget_key": "johannesburg-harare",
        "distance": "1,100 km", "flight_time": "1h 50m", "stops": "0",
        "low_fare": 3500, "high_fare": 8500,
        "fare_range_label": "R3,500–R8,500",
        "lead": (f"Johannesburg to Harare is the most-flown corridor between South Africa and Zimbabwe. Three airlines fly it daily — SAA, Airlink "
                 f"and FastJet — with 1h 50m scheduled flight times and 6–8 daily frequencies combined. SAA and Airlink share the route via codeshare; "
                 f"FastJet is the budget option. In {MONTH_YEAR}, book 2–6 weeks ahead for the cheapest fares; same-week bookings can still come in "
                 f"reasonable."),
        "airlines": [
            ("South African Airways", "Direct JNB–HRE",  "R4,500–R7,500", "Codeshare with Airlink. Bags included."),
            ("Airlink",               "Direct JNB–HRE",  "R4,200–R7,000", "Daily, multiple frequencies. Most reliable."),
            ("FastJet",               "Direct JNB–HRE",  "R3,500–R6,500", "Cheapest. Bags extra. Same scheduled time."),
            ("Kenya Airways (via NBO)", "Via Nairobi",   "R6,000–R10,000", "Only relevant for onward East Africa connections."),
        ],
        "season": ("Cheaper months are <strong>February–May</strong> and <strong>September–early November</strong>. Peak is December and South African "
                   "school holiday windows (April–early May, late June–mid July, late September–mid October). Christmas fares can double; book by October."),
        "layovers": [
            ("Direct on SAA / Airlink / FastJet", "No layover. 1h 50m scheduled flight, 6–8 daily frequencies."),
            ("Via Nairobi (Kenya Airways)",       "Only relevant if connecting onward — otherwise no reason to take an indirect routing."),
        ],
        "baggage": ("SAA includes 1 × 23 kg checked. Airlink the same, with extras at R500–R900 each at booking. FastJet is the budget carrier — "
                    "base fares exclude checked bags; budget R350–R700 per bag at booking, more at the airport."),
        "visa": "South African passport holders do not need a visa for Zimbabwe for stays under 90 days. UK, US, Australian and Canadian connections through JNB will need a Zimbabwe visa on arrival at Harare (USD cash).",
        "pullout": "FastJet is the cheapest one-way at R1,500–R2,500 — the catch is that bags are extra and routine fees stack up.",
        "faqs": [
            ("How much is a flight from Johannesburg to Harare?",
             "R3,500 to R8,500 return depending on carrier and season. FastJet is usually cheapest at R3,500–R6,500; SAA and Airlink sit at R4,500–R7,500. Christmas fares can exceed R10,000."),
            ("Are there direct flights from Johannesburg to Harare?",
             "Yes. SAA, Airlink and FastJet all fly direct Joburg to Harare, with 1h 50m scheduled flight time. Multiple daily frequencies on each."),
            ("How long is the flight from Johannesburg to Harare?",
             "1 hour 50 minutes scheduled flight time. Including check-in, the full journey is around 4 hours."),
            ("Which is the cheapest airline Johannesburg to Harare?",
             "FastJet is usually the cheapest, with one-way fares often under R2,000. SAA and Airlink come in higher but include more baggage and faster JNB connections."),
            ("How often do flights run Joburg to Harare?",
             "Multiple times daily. Combined across SAA, Airlink and FastJet there are typically 6–8 daily frequencies in each direction, including early morning, midday and evening departures."),
            ("Can I fly to Harare from Joburg today?",
             "Yes — same-day bookings are routine. Walk-up fares at OR Tambo are higher than online; budget R4,000–R6,000 one-way for a same-day booking."),
            ("What's the cheapest day to fly JNB to HRE?",
             "Tuesday and Wednesday departures are usually the cheapest; Sunday and Friday lift R500–R1,500 due to business and weekend travel demand."),
            ("Do I need a visa to fly from Joburg to Harare?",
             "South African passport holders, no — visa-free for 90 days. Other nationalities need a Zimbabwe visa, issued on arrival at HRE for US$55 cash."),
        ],
        "related": [
            ("Cape Town to Harare",   "/flights/cape-town-to-harare/",              "Direct on Airlink"),
            ("ZAR to ZWG rate",        "/fx/zar-to-zwg/",                            "Today's rate"),
            ("Send ZAR to Zimbabwe",   "/fx/send-money-from-south-africa-to-zimbabwe/", "Cheapest providers"),
            ("Harare airport (HRE)",   "/airports/harare/",                    "Arrivals, taxis, schedule"),
        ],
    },

    "new-york-to-harare": {
        "title": f"Cheap flights New York to Harare — {MONTH_YEAR} fares from $1,100",
        "h1": "Cheap flights New York to Harare",
        "stand": ("New York to Harare is the US East Coast diaspora's main corridor — one stop via Addis Ababa or Doha, "
                  "18–22 hours total. Live prices in USD below."),
        "flag_from": "🇺🇸", "flag_to": "🇿🇼",
        "origin_short": "New York", "origin_full": "New York (JFK / EWR)",
        "dest_short": "Harare", "dest_full": "Harare (HRE)",
        "currency_lbl": "USD", "currency_sym": "$",
        "widget_key": "new-york-harare",
        "distance": "12,500 km", "flight_time": "18–22 hrs", "stops": "1",
        "low_fare": 1100, "high_fare": 2400,
        "fare_range_label": "$1,100–$2,400",
        "lead": (f"New York to Harare is the busiest US–Zimbabwe corridor by far, drawing diaspora travellers from across the East Coast and Midwest. "
                 f"There are no non-stop flights; every routing is one-stop. In {MONTH_YEAR}, Ethiopian via Addis Ababa is consistently the cheapest "
                 f"option at $1,100–$1,500 return in low season, with Qatar via Doha a slightly more expensive but more comfortable alternative."),
        "airlines": [
            ("Ethiopian Airlines", "Addis Ababa (ADD)", "$1,100–$1,800", "The cheapest reliable option from the US East Coast. JFK departs nightly."),
            ("Qatar Airways",      "Doha (DOH)",        "$1,300–$2,000", "Better product, premium service. Both JFK and EWR daily."),
            ("Emirates",           "Dubai (DXB)",        "$1,400–$2,200", "Reliable, generous baggage. JFK daily plus EWR seasonal."),
            ("Delta + KLM",        "Amsterdam + JNB",    "$1,500–$2,400", "Two-stop. Convenient if you have SkyMiles status."),
        ],
        "season": ("Cheap months are <strong>February–March</strong>, <strong>May</strong>, and <strong>September–early November</strong>. "
                   "Peak is December (Zimbabwean Christmas), June–July (US summer + Zim school holidays), and Easter. "
                   "Book 10–14 weeks ahead; last-minute December fares routinely exceed $2,500."),
        "layovers": [
            ("Addis Ababa (Ethiopian)", "Africa's busiest hub. Allow 3+ hours; transit can be tight. Bole International is modernised."),
            ("Doha (Qatar)",            "Comfortable, well-organised. 2–4 hour layovers typical. Lounge accessible on Privilege Club Silver+."),
            ("Dubai (Emirates)",        "Best transit experience. Long layovers possible — Emirates allows day-room booking at the Dubai International Hotel."),
        ],
        "baggage": ("Ethiopian, Qatar and Emirates all allow 2 × 23 kg checked in economy on US–Africa long-haul. "
                    "Delta + KLM itineraries vary — usually 2 × 23 kg in economy classic, 1 × 23 kg in basic economy. "
                    "Excess at the counter is $200–$400 per bag; add at booking for ~$100."),
        "visa": ("US passport holders need a Zimbabwe visa, issued on arrival at Harare International for US$55 cash single-entry. "
                 "No advance application required. Bring USD cash — the visa desk does not accept card."),
        "pullout": "Ethiopian's JFK–ADD–HRE has been consistently the cheapest US–Zimbabwe routing for years — and it's also the fastest one-stop.",
        "faqs": [
            ("How much is a flight from New York to Harare?",
             "$1,100–$2,400 return depending on season and lead time. Ethiopian via Addis is usually cheapest at $1,100–$1,500 in low season; Qatar via Doha typically $1,300–$2,000. Christmas can exceed $2,500."),
            ("Are there direct flights from New York to Harare?",
             "No. There are no non-stop services between the US and Harare. Every itinerary has one stop, most commonly via Addis Ababa, Doha or Dubai."),
            ("How long is the flight from New York to Harare?",
             "18 to 22 hours total including the stop. Ethiopian JFK–ADD is 13 hours, ADD–HRE is 4 hours, with a 3-hour layover. Qatar JFK–DOH is 12 hours, DOH–HRE is 8 hours."),
            ("What is the cheapest airline from New York to Harare?",
             "Ethiopian Airlines via Addis Ababa is almost always the cheapest, often $200–$500 less than the next option. Service is reliable; the trade-off is a busier hub at ADD."),
            ("Can I fly to Harare from NYC tomorrow?",
             "Yes — Ethiopian, Qatar and Emirates all depart JFK daily for ADD/DOH/DXB with onward Harare connections. Same-day fares carry a $500–$900 premium versus an 8-week advance booking."),
            ("What's the cheapest month to fly NYC to Harare?",
             "February, March, May, September and October. These avoid the major diaspora travel windows (Christmas, July, Easter) and US summer peak."),
            ("Do I need a visa to fly to Zimbabwe from the US?",
             "Yes, but it's issued on arrival at Harare International for US$55 cash. No advance application needed. Bring USD cash for the visa desk."),
            ("What's the best time to book NYC to Harare?",
             "10 to 14 weeks ahead for the low end of the price range. For Christmas travel, book by August. Last-minute December fares routinely exceed $2,500."),
        ],
        "related": [
            ("Flights from Harare",      "/flights/from-harare/",            "Returning to the US"),
            ("Zimbabwe visa on arrival", "/moving-to-zimbabwe/visa-on-arrival.html", "The US$55 visa desk"),
            ("Harare airport (HRE)",     "/airports/harare/",          "Live arrivals + practical guide"),
            ("USD to ZWG rate",           "/fx/usd-to-zwg/",                   "Today's rate"),
        ],
    },

    "dubai-to-harare": {
        "title": f"Cheap flights Dubai to Harare — {MONTH_YEAR} direct on Emirates",
        "h1": "Cheap flights Dubai to Harare",
        "stand": ("Dubai to Harare is the only true direct long-haul into Zimbabwe — Emirates operates daily nonstop, 8 hours flight time. "
                  "Live prices in AED below."),
        "flag_from": "🇦🇪", "flag_to": "🇿🇼",
        "origin_short": "Dubai", "origin_full": "Dubai (DXB)",
        "dest_short": "Harare", "dest_full": "Harare (HRE)",
        "currency_lbl": "AED", "currency_sym": "AED",
        "widget_key": "dubai-harare",
        "distance": "5,400 km", "flight_time": "8 hrs direct", "stops": "0",
        "low_fare": 2400, "high_fare": 5500,
        "fare_range_label": "AED 2,400–AED 5,500",
        "lead": (f"Dubai to Harare is the only true direct long-haul service into Zimbabwe — Emirates operates a daily nonstop, "
                 f"with scheduled flight time of around 8 hours. The route serves both the Gulf Zimbabwean diaspora and as the connection hub "
                 f"for UK, Australian and US travellers using Dubai as a transfer point. In {MONTH_YEAR}, low-season pricing on the DXB–HRE leg "
                 f"alone is AED 2,400–AED 3,500 return."),
        "airlines": [
            ("Emirates",     "Direct DXB–HRE",       "AED 2,400–AED 4,500", "Daily nonstop. The only direct long-haul service to Zimbabwe."),
            ("Air Arabia",   "via Sharjah connections", "AED 2,200–AED 3,800", "Some routings via SHJ to JNB then onward. Cheaper but longer."),
        ],
        "season": ("Cheap months are <strong>February–April</strong> and <strong>September–November</strong>. Peak is December–January "
                   "(Gulf diaspora Christmas + Zimbabwean inbound), June–August (UAE summer departures). Book 6–10 weeks ahead."),
        "layovers": [
            ("Direct on Emirates", "No layover. 8-hour scheduled flight, departs DXB overnight for an early-morning HRE arrival."),
        ],
        "baggage": ("Emirates allows 30 kg checked in economy on UAE–Africa routes (a higher allowance than most other Emirates corridors). "
                    "Skywards members get +5–10 kg depending on tier."),
        "visa": ("UAE residents and Gulf nationals need a Zimbabwe visa, issued on arrival at HRE for US$55 cash. "
                 "Bring USD; the visa desk does not accept AED or card."),
        "pullout": "Emirates DXB–HRE is the only direct long-haul flight into Zimbabwe — that's why it's the most reliable diaspora option from any origin connecting through Dubai.",
        "faqs": [
            ("Are there direct flights from Dubai to Harare?",
             "Yes. Emirates operates a daily nonstop DXB–HRE, scheduled around 8 hours. It is the only direct long-haul service into Zimbabwe."),
            ("How much is a flight from Dubai to Harare?",
             "AED 2,400–AED 5,500 return depending on season and class. Low-season direct is AED 2,400–AED 4,500 on Emirates. December–January adds AED 1,000+."),
            ("How long is the direct flight Dubai to Harare?",
             "8 hours scheduled flight time. Emirates departs DXB late evening (typically 22:00–01:00) for an early-morning HRE arrival."),
            ("Which airlines fly Dubai to Harare?",
             "Emirates is the only direct operator. Connecting options via Sharjah (Air Arabia) and Doha (Qatar Airways) exist but add 4–8 hours."),
            ("Can I fly from Dubai to Harare today?",
             "Yes — Emirates' daily DXB–HRE service has same-day availability outside peak weeks. Walk-up at DXB carries a 20–40% premium vs online."),
            ("What time does the Emirates flight leave Dubai for Harare?",
             "Typically 22:00–01:00 local. The flight is timed to arrive in Harare early morning, both for diaspora travellers and for onward connections within southern Africa."),
            ("Do UAE residents need a visa for Zimbabwe?",
             "Yes. Visa on arrival at Harare for US$55 cash single-entry. No advance application needed. Bring USD."),
            ("What's the cheapest day to fly Dubai to Harare?",
             "Tuesday and Wednesday departures typically run AED 200–AED 500 below Friday/Sunday on Emirates."),
        ],
        "related": [
            ("Flights from Harare",       "/flights/from-harare/",            "Return to Dubai"),
            ("Zimbabwe visa on arrival",  "/moving-to-zimbabwe/visa-on-arrival.html", "The US$55 visa desk"),
            ("Harare airport (HRE)",      "/airports/harare/",          "Live arrivals + practical guide"),
        ],
    },

    "toronto-to-harare": {
        "title": f"Cheap flights Toronto to Harare — {MONTH_YEAR} fares from C$1,400",
        "h1": "Cheap flights Toronto to Harare",
        "stand": ("Toronto to Harare is the largest Canada–Zimbabwe corridor — one or two stops via Addis Ababa, London or Joburg, "
                  "20–24 hours total. Live prices in CAD below."),
        "flag_from": "🇨🇦", "flag_to": "🇿🇼",
        "origin_short": "Toronto", "origin_full": "Toronto (YYZ)",
        "dest_short": "Harare", "dest_full": "Harare (HRE)",
        "currency_lbl": "CAD", "currency_sym": "C$",
        "widget_key": "toronto-harare",
        "distance": "12,800 km", "flight_time": "20–24 hrs", "stops": "1–2",
        "low_fare": 1400, "high_fare": 3000,
        "fare_range_label": "C$1,400–C$3,000",
        "lead": (f"Toronto to Harare is the largest Canada–Zimbabwe corridor, serving the Canadian Zimbabwean diaspora concentrated in the Greater "
                 f"Toronto Area and the Prairies. There are no direct flights; routings are one-stop via Addis Ababa (Ethiopian) or two-stop via "
                 f"London + onward. In {MONTH_YEAR}, Ethiopian via Addis is consistently the cheapest at C$1,400–C$1,900 return in low season."),
        "airlines": [
            ("Ethiopian Airlines",    "Addis Ababa (ADD)",     "C$1,400–C$2,200", "Cheapest. YYZ–ADD nonstop, then ADD–HRE. Daily."),
            ("Air Canada + connections", "London or Frankfurt", "C$1,800–C$2,800", "Two-stop via European hub then southern Africa connection."),
            ("KLM via Amsterdam",     "AMS + JNB",              "C$1,700–C$2,600", "Reliable two-stop with good baggage."),
            ("Qatar Airways",         "Doha (DOH)",              "C$1,900–C$3,000", "Premium product, one-stop via DOH."),
        ],
        "season": ("Cheap months are <strong>February–May</strong> and <strong>September–early November</strong>. Peak is December–January "
                   "(Canadian winter + Zim diaspora Christmas) and June–August. Book 10–14 weeks ahead; last-minute December fares can exceed C$3,500."),
        "layovers": [
            ("Addis Ababa (Ethiopian)", "Single stop, busiest African hub. Allow 3+ hours."),
            ("London (Air Canada + BA)", "Two-stop. LHR is the common transfer, then BA/Virgin onward to Joburg + Airlink to HRE."),
            ("Amsterdam (KLM)",          "Two-stop via AMS to JNB. Generous baggage on KLM."),
        ],
        "baggage": ("Ethiopian and Qatar permit 2 × 23 kg checked in economy on Canada–Africa long-haul. "
                    "Air Canada + connection itineraries vary by booking class. Excess at airport is C$200+ per bag."),
        "visa": ("Canadian passport holders need a Zimbabwe visa, issued on arrival at HRE for US$55 cash. Bring USD cash."),
        "pullout": "Ethiopian's YYZ–ADD nonstop is the cheapest AND fastest Toronto–Harare routing — no contest in this corridor.",
        "faqs": [
            ("How much is a flight from Toronto to Harare?",
             "C$1,400–C$3,000 return depending on season and lead time. Ethiopian via Addis is usually cheapest at C$1,400–C$1,900 in low season. Christmas can exceed C$3,500."),
            ("Are there direct flights from Toronto to Harare?",
             "No. There are no non-stop services. Ethiopian via Addis Ababa is the only true one-stop; other routings involve two stops via European hubs."),
            ("How long is the flight from Toronto to Harare?",
             "20 to 24 hours including layovers. Ethiopian's YYZ–ADD–HRE is the shortest at around 20 hours; two-stop routings via Europe extend to 24+ hours."),
            ("What is the cheapest airline from Toronto to Harare?",
             "Ethiopian Airlines via Addis Ababa, almost always C$300–C$600 cheaper than the next option. Their YYZ nonstop launched in 2019 and has consistently held the price advantage."),
            ("Can I fly to Harare from Toronto this week?",
             "Yes — Ethiopian YYZ–ADD departs 4–5 times weekly. Same-week bookings in low season are C$2,200–C$2,800; peak weeks add C$700+."),
            ("Do Canadian passport holders need a visa for Zimbabwe?",
             "Yes, but it's issued on arrival at Harare International for US$55 cash single-entry. No advance application required. Bring USD cash."),
            ("What's the cheapest month to fly Toronto to Harare?",
             "March, April, September and October are typically lowest. February and May are also good. Avoid December–January and June–August peaks."),
            ("When should I book Toronto to Harare?",
             "10–14 weeks ahead for the bottom of the range. For December travel, book by August. Last-minute Christmas bookings can exceed C$3,500."),
        ],
        "related": [
            ("Flights from Harare",       "/flights/from-harare/",            "Return to Canada"),
            ("Zimbabwe visa on arrival",  "/moving-to-zimbabwe/visa-on-arrival.html", "The US$55 visa desk"),
            ("Harare airport (HRE)",      "/airports/harare/",          "Live arrivals + practical guide"),
            ("Send CAD to Zimbabwe",      "/fx/send-money-from-canada-to-zimbabwe/", "Cheapest providers"),
        ],
    },

    "london-to-victoria-falls": {
        "title": f"Cheap flights London to Victoria Falls — {MONTH_YEAR} fares from £800",
        "h1": "Cheap flights London to Victoria Falls",
        "stand": ("London to Victoria Falls is the British tourist's main route to the Smoke that Thunders. One-stop via Joburg (BA + Airlink), "
                  "Addis Ababa (Ethiopian) or Doha (Qatar). Live prices in GBP below."),
        "flag_from": "🇬🇧", "flag_to": "🇿🇼",
        "origin_short": "London", "origin_full": "London (LON)",
        "dest_short": "Victoria Falls", "dest_full": "Victoria Falls (VFA)",
        "currency_lbl": "GBP", "currency_sym": "£",
        "widget_key": "london-victoria-falls",
        "distance": "8,500 km", "flight_time": "14–18 hrs", "stops": "1",
        "low_fare": 800, "high_fare": 2400,
        "fare_range_label": "£800–£2,400",
        "lead": (f"Victoria Falls (VFA) is one of southern Africa's busiest tourist gateways — and the corridor from London is the British holiday traveller's "
                 f"default route to the Smoke that Thunders. There are no direct flights; the common routings are via Johannesburg (BA + Airlink), Addis Ababa "
                 f"(Ethiopian) or Doha (Qatar). In {MONTH_YEAR}, low-season pricing applies and fares cluster at £800–£1,400 return; peak (June–October Zim "
                 f"dry season aligned with UK summer) lifts to £1,800–£2,400."),
        "airlines": [
            ("Ethiopian Airlines", "Addis Ababa (ADD)",   "£800–£1,500",  "Cheapest reliable option. ADD–VFA direct."),
            ("BA + Airlink",       "Johannesburg (JNB)",  "£950–£1,800",  "BA codeshare. Airlink operates the JNB–VFA leg."),
            ("Qatar Airways",      "Doha (DOH)",          "£1,000–£1,900","Comfortable, one-stop. DOH–HRE then onward Airlink to VFA."),
            ("Emirates",           "Dubai + JNB",          "£1,200–£2,200","Two-stop via DXB then JNB. Most generous baggage."),
        ],
        "season": ("Victoria Falls has a counter-cyclical pricing pattern to Harare. <strong>Dry season (May–October)</strong> is peak tourist demand and "
                   "fares lift; <strong>wet season (November–April)</strong> sees lower fares but heavier rains. Cheap months: <strong>February–April</strong> "
                   "and <strong>November</strong>. Avoid August (UK + South African school holidays + dry-season tourism)."),
        "layovers": [
            ("Addis Ababa (Ethiopian)", "Single stop. Bole International is the cheapest hub and the most reliable for VFA."),
            ("Johannesburg (BA + Airlink)", "Single stop. Airlink operates the onward JNB–VFA leg; check baggage through-checking."),
            ("Doha (Qatar)", "Premium product. Connects via Harare then onward Airlink — adds an hour vs Addis routing."),
            ("Dubai + Joburg (Emirates)", "Two-stop, longer total time. Choose for baggage allowance, not speed."),
        ],
        "baggage": "Ethiopian and Qatar allow 2 × 23 kg checked in economy on UK–Africa long-haul. Emirates' two-stop usually permits 2 × 23 kg. BA + Airlink varies — check through-baggage carefully on the JNB–VFA leg.",
        "visa": ("UK passport holders need a Zimbabwe visa or the KAZA UniVisa, both issued on arrival. The <strong>KAZA UniVisa (US$50)</strong> "
                 "is the right choice for Victoria Falls trips — it covers Zimbabwe and Zambia and is valid for day trips into Botswana. "
                 "See the <a href=\"/moving-to-zimbabwe/visa-on-arrival.html\">visa on arrival guide</a>."),
        "pullout": "For Victoria Falls trips, the KAZA UniVisa (US$50 cash) is what you want — it covers both Zim and Zambia for day trips across the bridge.",
        "faqs": [
            ("How much is a flight from London to Victoria Falls?",
             "£800–£2,400 return depending on season. Low season (February–April, November) is £800–£1,500 on Ethiopian via Addis. Peak (June–October UK summer + Zim dry season) lifts to £1,800–£2,400."),
            ("Are there direct flights from London to Victoria Falls?",
             "No. Every routing has at least one stop. Most common are via Addis Ababa (Ethiopian), Johannesburg (BA + Airlink) or Doha (Qatar)."),
            ("How long is the flight from London to Victoria Falls?",
             "14 to 18 hours including the stop. Ethiopian's LHR–ADD–VFA is shortest at about 14 hours. BA + Airlink via JNB is 15–17 hours. Two-stop via Dubai + JNB is 18+ hours."),
            ("Which airline is cheapest London to Victoria Falls?",
             "Ethiopian Airlines via Addis Ababa is consistently the cheapest, often £150–£400 below the next option. The trade-off is a busier hub at ADD."),
            ("When is the best time to visit Victoria Falls?",
             "For peak waterfall flow, visit February–May (after the rainy season). For the best Zambezi rapids whitewater rafting, visit August–November (low water). Best wildlife viewing: dry season May–October."),
            ("What visa do I need for Victoria Falls?",
             "If you're visiting only the Zimbabwean side: a Zimbabwe visa on arrival, US$55 cash. If you plan to cross to the Zambian side or Livingstone for day trips: the KAZA UniVisa, US$50 cash, covers both Zimbabwe and Zambia."),
            ("Can I fly to Victoria Falls tomorrow?",
             "Yes — daily availability on Ethiopian via Addis and BA + Airlink via Joburg. Last-minute fares in low season can come in around £1,100–£1,500."),
            ("Is Victoria Falls airport (VFA) the right airport?",
             "Yes for the Zimbabwean side. For the Zambian side (Livingstone), fly into Livingstone Airport (LVI). Both are 15 minutes from the Falls themselves and 5 minutes from each other via the Victoria Falls Bridge border."),
        ],
        "related": [
            ("Victoria Falls airport (VFA)", "/airports/victoria-falls/", "Live arrivals + practical guide"),
            ("Harare to Victoria Falls",      "/flights/from-harare/",            "Domestic connection"),
            ("Zimbabwe visa on arrival",      "/moving-to-zimbabwe/visa-on-arrival.html", "KAZA UniVisa"),
            ("Send GBP to Zimbabwe",           "/fx/send-money-from-uk-to-zimbabwe/", "For your trip"),
        ],
    },

    "from-harare": {
        "title": f"Flights from Harare — book your return to the UK, US, SA, Australia | {MONTH_YEAR}",
        "h1": "Flights from Harare",
        "stand": "Live USD price search for flights departing Harare to anywhere in the world. UK, USA, South Africa, Dubai, Australia and Canada are the busiest diaspora-return corridors.",
        "flag_from": "🇿🇼", "flag_to": "🌍",
        "origin_short": "Harare", "origin_full": "Harare (HRE)",
        "dest_short": "anywhere", "dest_full": "any destination",
        "currency_lbl": "USD", "currency_sym": "$",
        "widget_key": "from-harare",
        "distance": "varies", "flight_time": "varies by route", "stops": "1+",
        "low_fare": 700, "high_fare": 2500,
        "fare_range_label": "$700–$2,500",
        "lead": (f"Harare is well-connected for a southern African hub: five major carriers operate daily long-haul departures, each routing through "
                 f"their hub (Dubai, Doha, Addis Ababa, Nairobi or Johannesburg) before fanning out to the diaspora's home cities. In {MONTH_YEAR}, "
                 f"outbound fares are tracking towards their low-season floor — book within the next 6–10 weeks for the cheaper end of the range."),
        "airlines": [
            ("Emirates",           "via Dubai (DXB)",          "to UK, EU, USA, Australia", "Reliable schedule, premium product, generous baggage."),
            ("Qatar Airways",      "via Doha (DOH)",           "to UK, EU, USA",            "Cheapest of the Gulf options to the UK."),
            ("Ethiopian Airlines", "via Addis Ababa (ADD)",    "to USA, Canada, EU, Asia",  "Cheapest to North America."),
            ("Kenya Airways",      "via Nairobi (NBO)",        "to UK, EU, India",          "Solid African network."),
            ("SAA / Airlink",      "via Johannesburg (JNB)",   "to UK, EU, USA, Australia", "Cheapest route to Australia via Perth onward."),
        ],
        "season": ("Outbound prices from Harare follow the inbound diaspora calendar in reverse. Cheapest outbound months are typically "
                   "<strong>January–February</strong> (after Christmas), <strong>August</strong> (after July returns) and <strong>November</strong> "
                   "(pre-Christmas inbound rush). Peak outbound is <strong>mid-January</strong> and <strong>late July–early August</strong>."),
        "layovers": [
            ("Emirates via Dubai",       "The most reliable hub for onward UK, US, EU, Australian connections."),
            ("Qatar via Doha",           "Similar to Emirates, often a bit cheaper to the UK."),
            ("Ethiopian via Addis",      "The cheapest option for North America and a key hub for African connections."),
            ("Kenya Airways via Nairobi", "Decent African network, occasionally competitive for the UK."),
            ("South African via Joburg",  "The cheapest route to Australia (via Perth onward)."),
        ],
        "baggage": ("Emirates, Qatar and Ethiopian all permit 2 × 23 kg checked in economy on the Harare–[hub]–[destination] long-haul ticket. "
                    "Kenya Airways and SAA itineraries vary by class."),
        "visa": "Destination visa requirements apply. UK/US/Australian/Canadian green-card holders should check their own destination requirements.",
        "pullout": "Tuesday and Wednesday departures from Harare are routinely $80–$200 cheaper than Friday/Sunday on the long-haul corridors.",
        "faqs": [
            ("How much is a flight from Harare to London?",
             "Typically US$900–US$1,800 return, with the cheap end in January–February and August. Emirates via Dubai and Qatar via Doha are the most-flown options; Kenya Airways via Nairobi is often a few hundred USD cheaper."),
            ("What's the cheapest flight from Harare to the USA?",
             "Ethiopian via Addis Ababa is consistently the cheapest to the US East Coast (US$1,100–US$1,900 return to NYC/Washington). For the West Coast, the same routing applies but adds another connection."),
            ("Which airlines fly from Harare?",
             "Five main carriers operate daily out of Harare International (HRE): Emirates (DXB), Qatar Airways (DOH), Ethiopian Airlines (ADD), Kenya Airways (NBO) and South African Airways / Airlink (JNB)."),
            ("When is the cheapest time to fly out of Harare?",
             "January–February (after the Christmas inbound rush), August (after July returns to school) and November (before the December inbound)."),
            ("Can I fly out of Harare tomorrow?",
             "Yes — daily departures on Emirates, Qatar, Ethiopian, Kenya Airways and SAA. Same-day fares carry a premium of $200–$500 versus an 8-week advance booking."),
            ("What are the cheapest last-minute flights from Harare this week?",
             "Run the widget above for your specific destination. In low season, Kenya Airways via Nairobi typically has the cheapest same-week fares to the UK; Ethiopian via Addis to the USA."),
            ("Do I need a return ticket to leave Zimbabwe?",
             "Some destinations require proof of onward travel for entry. For UK/US/EU/Australian visa holders this is rarely an issue. For visitor visas, having a return ticket on the same booking smooths immigration."),
            ("What time do international flights leave Harare?",
             "Most long-haul departures cluster between 23:00 and 04:00 — the carriers' hubs are 6–9 hours east of Harare, so an overnight outbound puts you in DXB/DOH/ADD/NBO at the right time for onward morning connections."),
        ],
        "related": [
            ("London to Harare",      "/flights/london-to-harare/",        "Inbound corridor"),
            ("Joburg to Harare",      "/flights/johannesburg-to-harare/",  "Regional corridor"),
            ("Send money home",        "/fx/",                              "Cheapest providers"),
            ("Harare airport (HRE)",   "/airports/harare/",          "Arrivals, taxis, schedule"),
        ],
    },
}

# ---------------------------------------------------------------------------
# AIRPORT PAGE CONFIG
# ---------------------------------------------------------------------------

AIRPORTS = {
    "harare": {
        "title": f"Harare International Airport (HRE) — arrivals, departures, airlines | {MONTH_YEAR}",
        "h1": "Harare International Airport",
        "subtitle": "Robert Gabriel Mugabe International (HRE / FVHA)",
        "stand": ("Live arrivals and departures for HRE, plus the practical guide: airlines, transport, visa-on-arrival, SIM cards. "
                  "Harare International is Zimbabwe's primary international gateway."),
        "iata": "HRE", "icao": "FVHA",
        "lat": -17.9319, "lon": 31.0928,
        "lead": ("Harare International — formally Robert Gabriel Mugabe International — sits 15 km southeast of central Harare and is the country's "
                 "main international gateway. Renovated and expanded in 2017–2022 with a Chinese-funded $153m programme, the airport now has separate "
                 "international and domestic terminals and handles roughly 3 million passengers a year. International long-haul service is concentrated "
                 "between 23:00 and 04:00 — the major hub carriers (Emirates, Qatar, Ethiopian, Kenya Airways, SAA) all depart Harare for their hubs "
                 "overnight to connect to morning departures in DXB, DOH, ADD, NBO and JNB."),
        "facts": [
            ("IATA / ICAO", "HRE / FVHA"),
            ("Distance to CBD", "15 km"),
            ("Annual passengers", "~3 million"),
            ("Runways", "1 (05/23)"),
        ],
        "airlines_outbound": [
            ("Emirates",           "EK",  "Dubai (DXB)",          "Daily, ~01:00"),
            ("Qatar Airways",      "QR",  "Doha (DOH)",           "Daily, ~02:00"),
            ("Ethiopian Airlines", "ET",  "Addis Ababa (ADD)",    "Daily, ~03:00"),
            ("Kenya Airways",      "KQ",  "Nairobi (NBO)",        "Daily, ~14:00"),
            ("South African Airways", "SA","Johannesburg (JNB)",   "3-4x daily"),
            ("Airlink",            "4Z",  "Johannesburg (JNB), Cape Town (CPT)","Multiple daily"),
            ("FastJet",            "FN",  "Johannesburg (JNB), Victoria Falls (VFA)","Daily"),
            ("Air Zimbabwe",       "UM",  "Victoria Falls (VFA), Bulawayo (BUQ)","Limited"),
            ("Mauritania Airlines",  "L6","Lubumbashi via Lusaka","Schedule varies"),
            ("Proflight Zambia",   "P0",  "Lusaka (LUN)",         "Multiple weekly"),
        ],
        "getting_to": [
            ("Taxi from CBD",      "USD 25–40, ~25 minutes. Pre-book via your hotel for the better rate."),
            ("Hotel shuttle",      "Most international hotels (Meikles, Rainbow Towers, Cresta Lodge) offer a USD 25–40 shuttle. Pre-book."),
            ("Uber / Bolt",         "Available but limited driver coverage at the airport. Pricing comparable to taxi."),
            ("Personal vehicle",    "USD 5/day in long-term car parking, USD 1/hour short-term."),
            ("Public transport",    "Combi (minibus taxi) to Mbare market then onward to CBD. Not recommended for international arrivals with luggage."),
        ],
        "practical": [
            ("Currency",   "ATMs in the international arrivals hall dispense USD. Airport bureau de change typically gives a poor rate — use a city bureau or just an ATM."),
            ("SIM card",   "Econet and NetOne kiosks in the arrivals hall sell prepaid SIM cards (USD 5–10 starter). Bring your passport for registration. A <a href=\"/moving-to-zimbabwe/sim-card-and-mobile.html\">Zimbabwe eSIM</a> purchased before flying avoids this queue entirely."),
            ("Visa on arrival", "UK, US, Australian, Canadian passport holders get visa on arrival for USD 55 cash (single entry) or USD 50 (KAZA UniVisa). South Africans visa-free 90 days. USD cash only."),
            ("Customs",    "Standard duty-free allowance of 1L spirits + 200 cigarettes. Declare goods >USD 500. Electronics, second-hand goods, food and gifts are routinely declared by diaspora returnees."),
            ("Wi-Fi",      "Free 30-minute Wi-Fi available throughout the terminal."),
        ],
        "pullout": "International departures cluster between 23:00 and 04:00 — most diaspora travellers arrive at the airport by 22:00.",
        "faqs": [
            ("What is Harare airport's code?",
             "IATA code HRE, ICAO code FVHA. Some older sources still use the colonial-era 'FVHA' designator; both refer to Robert Gabriel Mugabe International, Zimbabwe's main international gateway."),
            ("Which airlines fly to Harare?",
             "Emirates (Dubai), Qatar Airways (Doha), Ethiopian Airlines (Addis Ababa), Kenya Airways (Nairobi), South African Airways and Airlink (Johannesburg/Cape Town), FastJet (regional), Air Zimbabwe (domestic). Five major long-haul carriers plus several regional and domestic operators."),
            ("How far is Harare airport from the city?",
             "15 km southeast of central Harare. A taxi to the CBD is USD 25–40 and takes about 25 minutes in normal traffic."),
            ("What time do international flights leave Harare?",
             "International long-haul departures cluster between 23:00 and 04:00. Most travellers arrive at HRE by 22:00 to be at the gate for boarding. Domestic and regional departures (JNB, CPT, VFA) are spread through the day."),
            ("Is there free Wi-Fi at Harare airport?",
             "Yes. The terminal has free 30-minute Wi-Fi access throughout. For longer use, network-connected workspaces in the airport hotel (Avenir Suites) offer paid options."),
            ("Where do I get a SIM card at Harare airport?",
             "Econet and NetOne kiosks in the international arrivals hall sell prepaid SIM cards. Starter packs are USD 5–10. You'll need your passport for ID registration. A pre-purchased Zimbabwe eSIM avoids this entirely."),
            ("How much is the visa at Harare airport?",
             "USD 55 cash for single entry (most diaspora visitors), USD 70 for double entry, USD 50 for the KAZA UniVisa (Zimbabwe + Zambia, also good for day trips into Botswana). USD cash only — the visa desk does not accept card."),
            ("Is there a hotel at Harare airport?",
             "Yes. Avenir Suites is the on-airport hotel, with shuttle service. Several mid-range hotels are within 5 km of the airport. The Rainbow Towers, Meikles and Bronte are in the CBD."),
            ("Can I check live arrivals at Harare airport?",
             "Yes. Live arrivals and departures for HRE are embedded at the top of this page (sourced from Avionio). You can also check FlightAware at <a href=\"https://flightaware.com/live/airport/FVHA\" rel=\"noopener\" target=\"_blank\">flightaware.com/live/airport/FVHA</a> for additional flight-tracker detail."),
            ("Can I bring USD cash into Zimbabwe?",
             "Yes. Travellers can bring up to USD 10,000 without declaration. Above that, declare to customs on arrival. USD is the dominant pricing currency in Zimbabwe and ATMs at HRE dispense USD."),
        ],
        "related": [
            ("Cheap flights to Harare",         "/flights/", "Hub"),
            ("London to Harare",                "/flights/london-to-harare/", "Diaspora's main corridor"),
            ("Visa on arrival",                 "/moving-to-zimbabwe/visa-on-arrival.html", "The US$55 visa desk"),
            ("Zimbabwe SIM / eSIM",             "/moving-to-zimbabwe/sim-card-and-mobile.html", "Before you fly"),
        ],
    },

    "victoria-falls": {
        "title": f"Victoria Falls Airport (VFA) — live arrivals, departures, airlines | {MONTH_YEAR}",
        "h1": "Victoria Falls International Airport",
        "subtitle": "Victoria Falls (VFA / FVFA)",
        "stand": ("Live arrivals and departures for VFA, plus the practical guide. Victoria Falls is Zimbabwe's main tourist gateway — "
                  "British Airways, Ethiopian, Airlink, FastJet and seasonal carriers."),
        "iata": "VFA", "icao": "FVFA",
        "lat": -18.0959, "lon": 25.8390,
        "lead": ("Victoria Falls International — IATA code VFA, ICAO code FVFA — is Zimbabwe's tourism gateway and one of southern Africa's busiest "
                 "leisure airports. The terminal was rebuilt in 2016 and now handles long-haul tourism traffic plus regional connections. The airport "
                 "sits 18 km southeast of Victoria Falls town. It is the natural arrival point for safari and falls itineraries, and visitors crossing "
                 "to the Zambian side (Livingstone) frequently land at VFA and cross via the Victoria Falls Bridge."),
        "facts": [
            ("IATA / ICAO", "VFA / FVFA"),
            ("Distance to town", "18 km"),
            ("Annual passengers", "~600,000"),
            ("Terminal renovated", "2016"),
        ],
        "airlines_outbound": [
            ("British Airways",       "BA",  "London (LHR)",                "Seasonal direct"),
            ("Ethiopian Airlines",    "ET",  "Addis Ababa (ADD)",           "Daily"),
            ("Airlink",               "4Z",  "Johannesburg (JNB), Cape Town (CPT)","Daily"),
            ("South African Airways", "SA",  "Johannesburg (JNB)",          "Several weekly"),
            ("FastJet",               "FN",  "Johannesburg (JNB), Harare (HRE)","Multiple weekly"),
            ("Air Zimbabwe",          "UM",  "Harare (HRE)",                "Limited"),
            ("Proflight Zambia",      "P0",  "Lusaka (LUN)",                "Multiple weekly"),
        ],
        "getting_to": [
            ("Taxi from town",        "USD 35–50, ~25 minutes from Victoria Falls town. Hotel-arranged is usually cheaper than the rank."),
            ("Hotel shuttle",          "Most upper-tier hotels (Victoria Falls Hotel, Ilala Lodge, Elephant Hills, A'Zambezi River Lodge) include a free or modest shuttle. Confirm at booking."),
            ("Crossing to Zambia",     "Victoria Falls Bridge border is 4 km from town. Walk-across is permitted with the right visa; KAZA UniVisa makes day-tripping seamless."),
            ("Private transfer",        "USD 50–80 prebooked through tour operators — popular when combined with same-day game-drive transfers in Hwange or Chobe."),
        ],
        "practical": [
            ("Currency",   "ATMs in arrivals dispense USD. Hotels in Victoria Falls quote in USD. Some shops accept ZAR; ZWG less common in tourist contexts."),
            ("SIM card",   "Econet and NetOne kiosks in the small arrivals area. For tourists, a Zimbabwe eSIM purchased before flying is usually simpler — see our <a href=\"/moving-to-zimbabwe/sim-card-and-mobile.html\">SIM guide</a>."),
            ("KAZA UniVisa", "If you're visiting both Zimbabwe and Zambia (very common at VFA), buy the KAZA UniVisa on arrival for US$50. It also allows day trips into Botswana. Cash only."),
            ("Customs",    "Standard duty-free allowance. Wildlife/CITES items (ivory, taxidermy, certain hardwood) are heavily controlled — do not bring out."),
            ("Wi-Fi",      "Free 30-minute Wi-Fi in the terminal. Hotels in Victoria Falls town have stronger connectivity."),
        ],
        "pullout": "VFA is the natural gateway for combined Zimbabwe + Zambia + Botswana itineraries — the KAZA UniVisa (US$50) at the immigration desk is the document you want.",
        "faqs": [
            ("What is Victoria Falls airport's code?",
             "IATA code VFA, ICAO code FVFA. The full name is Victoria Falls International Airport. It is located 18 km southeast of Victoria Falls town in western Zimbabwe."),
            ("Which airlines fly to Victoria Falls?",
             "Direct service: British Airways (seasonal LHR), Ethiopian Airlines (daily ADD), Airlink (daily JNB and CPT), FastJet (multiple weekly JNB and HRE), South African Airways (weekly JNB), Air Zimbabwe (limited HRE), Proflight Zambia (LUN)."),
            ("How far is Victoria Falls airport from the town?",
             "18 km southeast. Taxi to town is USD 35–50 and takes about 25 minutes. Most tourist hotels include shuttle service in the rate."),
            ("Can I cross to the Zambian side from VFA?",
             "Yes. The Victoria Falls Bridge border post is 4 km from town. With the KAZA UniVisa (US$50, multiple-entry between Zimbabwe and Zambia) you can walk or drive across freely for day trips. The bridge offers one of the world's best views of the Falls."),
            ("Is there live flight status for Victoria Falls airport?",
             "Yes. Live arrivals and departures for VFA are embedded at the top of this page (sourced from Avionio). For additional flight-tracker detail, check FlightAware at <a href=\"https://flightaware.com/live/airport/FVFA\" rel=\"noopener\" target=\"_blank\">flightaware.com/live/airport/FVFA</a>."),
            ("What visa do I need at Victoria Falls airport?",
             "For Zimbabwe-only: a single-entry visa, US$55 cash. For Zimbabwe + Zambia (very common for Falls visitors): KAZA UniVisa, US$50 cash, covers both countries and allows Botswana day trips. South African passport holders are visa-free for 90 days."),
            ("Can I fly from Victoria Falls to Cape Town directly?",
             "Yes. Airlink operates direct VFA–CPT, multiple weekly. The route is popular for combined Cape Town + Victoria Falls tourist itineraries."),
            ("What's the best time of year to visit Victoria Falls?",
             "Peak waterfall flow: February–May (after rainy season). Best wildlife viewing and lower humidity: May–October. Whitewater rafting season (low water): August–November. Christmas–January is peak tourist season; expect higher fares."),
        ],
        "related": [
            ("London to Victoria Falls",      "/flights/london-to-victoria-falls/", "The British tourist route"),
            ("Harare airport (HRE)",          "/airports/harare/",            "The main international gateway"),
            ("Bulawayo airport (BUQ)",        "/airports/bulawayo/",          "The Matabeleland gateway"),
            ("Zimbabwe visa on arrival",       "/moving-to-zimbabwe/visa-on-arrival.html", "KAZA UniVisa"),
        ],
    },

    "bulawayo": {
        "title": f"Bulawayo Airport (BUQ) — arrivals, departures, airlines | {MONTH_YEAR}",
        "h1": "Joshua Mqabuko Nkomo International Airport",
        "subtitle": "Bulawayo (BUQ / FVBU)",
        "stand": ("Live arrivals and departures for BUQ, plus the airport guide. Bulawayo is Zimbabwe's second international "
                  "gateway: daily Johannesburg service on Airlink and FastJet, domestic connections to Harare and Victoria Falls."),
        "iata": "BUQ", "icao": "FVBU",
        "lat": -20.0174, "lon": 28.6177,
        "lead": ("Joshua Mqabuko Nkomo International Airport — known locally as Bulawayo Airport, or BUQ — is Zimbabwe's second international airport, "
                 "serving the country's second city and the Matabeleland region. It sits 25 km north of central Bulawayo. The airport handles roughly "
                 "200,000 passengers a year and is dominated by the Johannesburg corridor, with daily service from Airlink and FastJet plus weekly SAA "
                 "frequencies. There is no long-haul direct service from BUQ — international travellers typically connect via Joburg or Harare."),
        "facts": [
            ("IATA / ICAO", "BUQ / FVBU"),
            ("Distance to CBD", "25 km"),
            ("Annual passengers", "~200,000"),
            ("Runways", "1 (13/31)"),
        ],
        "airlines_outbound": [
            ("Airlink",            "4Z",  "Johannesburg (JNB)",     "Daily"),
            ("FastJet",            "FN",  "Johannesburg (JNB)",     "Daily"),
            ("South African Airways","SA","Johannesburg (JNB)",     "Several weekly"),
            ("Air Zimbabwe",       "UM",  "Harare (HRE), Victoria Falls (VFA)", "Limited frequency"),
        ],
        "getting_to": [
            ("Taxi from CBD",      "USD 20–35, ~30 minutes. Pre-book via your hotel for the better rate."),
            ("Hotel shuttle",      "Major hotels (Bulawayo Rainbow, Holiday Inn Bulawayo) offer shuttles for USD 20–30. Pre-book."),
            ("Personal vehicle",    "Free parking is available outside the small main terminal."),
            ("Public transport",    "Combi taxis run on the main highway near the airport — walk to the road and flag down. Not recommended with luggage."),
        ],
        "practical": [
            ("Currency",       "Limited ATMs at BUQ — withdraw USD in Bulawayo CBD before departing or use a major bank ATM at one of the central hotels."),
            ("SIM card",       "Econet kiosk in the arrivals hall sells prepaid SIM cards. Smaller airport — outside operating hours you may have to buy in Bulawayo city centre."),
            ("Visa on arrival","International visitors (UK, US, AU, CA passports) get visa on arrival at BUQ — same US$55 cash policy as Harare."),
            ("Customs",        "Standard duty-free allowance. Quieter customs lane than Harare; arrivals are easier."),
            ("Wi-Fi",          "Limited free Wi-Fi available in the main terminal."),
        ],
        "pullout": "Bulawayo Airport has no long-haul direct service — for UK/US/EU travel, connect via Johannesburg or fly through Harare.",
        "faqs": [
            ("What is Bulawayo airport's code?",
             "IATA code BUQ, ICAO code FVBU. Full name: Joshua Mqabuko Nkomo International Airport. Located 25 km north of Bulawayo CBD."),
            ("Which airlines fly to Bulawayo?",
             "Airlink (daily JNB), FastJet (daily JNB), South African Airways (several weekly JNB), Air Zimbabwe (limited HRE/VFA frequency). No long-haul direct service from BUQ."),
            ("How far is Bulawayo airport from the city?",
             "25 km north of central Bulawayo. Taxi to CBD is USD 20–35 and takes about 30 minutes."),
            ("Are there international flights from Bulawayo?",
             "Yes, but only regional — daily Johannesburg service on Airlink and FastJet. There is no direct long-haul service. UK, US, EU and Australian travellers connect via Johannesburg."),
            ("Is Bulawayo airport open 24 hours?",
             "No. BUQ operates with daytime hours roughly 06:00–20:00, aligned with the JNB and domestic schedule. Out-of-hours arrivals are rare and pre-coordinated."),
            ("How do I get from Bulawayo airport to Victoria Falls?",
             "Fly Air Zimbabwe to Victoria Falls (VFA, scheduled but with limited frequency), or take the daytime road transfer (~440 km, 5–6 hours via Hwange National Park)."),
            ("Can I get a SIM card at Bulawayo airport?",
             "Yes, but the kiosks have limited hours. Econet typically operates during peak arrival windows. For reliability, a pre-purchased eSIM is easier."),
            ("Is there a hotel near Bulawayo airport?",
             "The closest mid-range options are 10–15 km away towards the city. Bulawayo Rainbow Hotel and Holiday Inn Bulawayo are in the CBD, 25 km away."),
        ],
        "related": [
            ("Cheap flights to Harare",         "/flights/", "Hub"),
            ("Joburg to Harare",                "/flights/johannesburg-to-harare/", "Connecting via JNB"),
            ("Cape Town to Harare",             "/flights/cape-town-to-harare/",    "Direct on Airlink"),
            ("Harare airport (HRE)",            "/airports/harare/",         "The main gateway"),
        ],
    },
}

# ---------------------------------------------------------------------------
# RENDERERS
# ---------------------------------------------------------------------------

def hero_image_for(slug):
    """Return <img>-ready relative path if /img/flights/<slug>.{ext} OR
    /img/airports/<slug>.{ext} exists. Corridor pages use /img/flights/;
    airport pages use /img/airports/. Falls back to /img/flights/ for both
    so legacy uploads still work."""
    for base in ("airports", "flights"):
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            p = ROOT / "img" / base / f"{slug}{ext}"
            if p.exists():
                return f"/img/{base}/{p.name}"
    return None

def hero_block(slug, alt_text):
    """Render the hero banner image block if an image exists for this slug."""
    img = hero_image_for(slug)
    if not img:
        return ""
    return f'''<figure class="fl-hero-img">
    <div class="fl-hero-img-inner"><img src="{img}" alt="{html.escape(alt_text)}" loading="eager"></div>
  </figure>'''

def render_corridor(slug, c):
    """Render a flight corridor page (e.g. london-to-harare)."""
    widget = widgets[c["widget_key"]]["embed"]
    canonical = f"https://www.mutapatimes.com/flights/{slug}/"

    # Sponsored Harare hotels carousel on Harare corridors only.
    harare_route = slug == "from-harare" or slug.endswith("-to-harare")
    hotels_rail = HOTELS_RAIL if harare_route else ""
    hotels_script = HOTELS_SCRIPT if harare_route else ""

    # Tables / lists
    airline_rows = "\n".join(
        f"          <tr><td><strong>{html.escape(name)}</strong></td><td>{html.escape(hub)}</td><td>{html.escape(fare)}</td><td>{html.escape(note)}</td></tr>"
        for name, hub, fare, note in c["airlines"]
    )
    layover_items = "\n".join(
        f"        <li><strong>{html.escape(hub)}</strong> &mdash; {note}</li>"
        for hub, note in c["layovers"]
    )

    # FAQ
    faq_html = "\n".join(
        f'''        <details>
          <summary>{html.escape(q)}</summary>
          <p>{a}</p>
        </details>''' for q, a in c["faqs"]
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text": stripped(a)}} for q, a in c["faqs"]]
    }, ensure_ascii=False)

    breadcrumb_ld = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Flights","item":"https://www.mutapatimes.com/flights/"},
            {"@type":"ListItem","position":3,"name": f"{c['origin_short']} to {c['dest_short']}", "item": canonical}
        ]
    }, ensure_ascii=False)
    trip_ld = json.dumps({
        "@context":"https://schema.org","@type":"Trip",
        "name": f"{c['origin_short']} to {c['dest_short']}",
        "description": f"Flight from {c['origin_full']} to {c['dest_full']}",
        "provider": {"@type":"Organization","name":"The Mutapa Times","url":"https://www.mutapatimes.com"}
    }, ensure_ascii=False)

    # Live price data (Travelpayouts Data API, refreshed twice daily).
    # See scripts/fetch_flight_prices.py — aggregates across multiple endpoints.
    live = prices_by_slug.get(slug, {}) or {}
    cheapest_obs = live.get("cheapest_overall") or live.get("cheapest") or live.get("cheapest_30d") or {}
    cheapest_direct_obs = live.get("cheapest_direct") or {}
    live_price = cheapest_obs.get("price") or cheapest_obs.get("value")
    live_airline = cheapest_obs.get("airline")
    live_dep = (cheapest_obs.get("departure_at") or "")[:10]
    live_stops = cheapest_obs.get("stops") if "stops" in cheapest_obs else cheapest_obs.get("number_of_changes")

    fare_callout_html = ""
    if live_price:
        stops_lbl = "direct" if live_stops == 0 else (f"{live_stops}-stop" if live_stops else "")
        meta_bits = []
        if live_airline: meta_bits.append(f"<strong>{html.escape(str(live_airline))}</strong>")
        if stops_lbl: meta_bits.append(html.escape(stops_lbl))
        if live_dep: meta_bits.append(f"departing {live_dep}")
        meta_str = " &middot; ".join(meta_bits) if meta_bits else "observed across the route"
        fare_callout_html = f'''<aside class="fl-fare">
    <div class="fl-fare-inner">
      <div>
        <p class="fl-fare-label"><span class="fl-fare-pulse" aria-hidden="true"></span>Cheapest fare observed</p>
        <p class="fl-fare-price">{c["currency_sym"]}{int(live_price):,}</p>
        <p class="fl-fare-meta">{meta_str}</p>
        <p class="fl-fare-asof">Updated {prices_fetched_at} &middot; aggregated across {live.get("observations", 0)} cached observations via Travelpayouts.</p>
      </div>
      <a class="fl-fare-cta" href="#fl-widget">Search current fares &rarr;</a>
    </div>
  </aside>'''

    # Monthly cheapest table (renders only when we have multiple months)
    monthly = live.get("monthly", []) or []
    monthly_html = ""
    if len(monthly) >= 3:
        rows = []
        for m in monthly[:8]:
            dep = m.get("departure_at") or ""
            try:
                d = datetime.date.fromisoformat(dep[:10])
                label = d.strftime("%b %Y")
            except Exception:
                label = dep[:7] if dep else "—"
            airline = m.get("airline") or "—"
            stops = m.get("stops")
            stops_lbl = "direct" if stops == 0 else (f"{stops}-stop" if stops else "—")
            rows.append(f'        <tr><td><strong>{label}</strong></td><td class="fl-mon-price">{c["currency_sym"]}{int(m["price"]):,}</td><td>{html.escape(str(airline)) if airline else "—"}</td><td>{html.escape(stops_lbl)}</td><td>{dep[:10] if dep else "—"}</td></tr>')
        monthly_html = f'''<section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">03B</span><span>By month</span></p>
    <h2 class="fl-section-h2">Cheapest fare each month</h2>
    <div class="fl-prose">
      <p>Cheapest fare observed for each month on the {c["origin_short"]} &mdash; {c["dest_short"]} corridor, aggregated from Travelpayouts cache. Use this to time your booking. Live prices for your specific dates are in the <a href="#fl-widget">search above</a>.</p>
    </div>
    <div class="fl-table-wrap">
      <table class="fl-table">
        <thead><tr><th>Month</th><th class="fl-mon-price">Cheapest</th><th>Airline</th><th>Stops</th><th>Best date</th></tr></thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>
  </section>'''

    # By-airline mini-table
    by_airline = live.get("by_airline", []) or []
    airline_live_html = ""
    if len(by_airline) >= 2:
        rows = []
        for a in by_airline:
            airline = a.get("airline") or "—"
            stops = a.get("stops")
            stops_lbl = "direct" if stops == 0 else (f"{stops}-stop" if stops else "—")
            dep = a.get("departure_at") or ""
            rows.append(f'        <tr><td><strong>{html.escape(str(airline))}</strong></td><td class="fl-mon-price">{c["currency_sym"]}{int(a["price"]):,}</td><td>{html.escape(stops_lbl)}</td><td>{dep[:10] if dep else "—"}</td></tr>')
        airline_live_html = f'''<section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">02B</span><span>Live by airline</span></p>
    <h2 class="fl-section-h2">Cheapest right now, by airline</h2>
    <div class="fl-table-wrap">
      <table class="fl-table">
        <thead><tr><th>Airline</th><th class="fl-mon-price">Cheapest seen</th><th>Stops</th><th>Departure</th></tr></thead>
        <tbody>
{chr(10).join(rows)}
        </tbody>
      </table>
    </div>
  </section>'''

    # AggregateOffer for the route — uses live cheapest if available
    offer_low = int(live_price) if live_price else c["low_fare"]
    offer_ld = json.dumps({
        "@context":"https://schema.org","@type":"Product",
        "name": f"{c['origin_short']} to {c['dest_short']} flight",
        "description": f"Return flight from {c['origin_full']} to {c['dest_full']}, indicative {MONTH_YEAR} fares.",
        "offers": {
            "@type":"AggregateOffer",
            "priceCurrency": c["currency_lbl"],
            "lowPrice": offer_low,
            "highPrice": c["high_fare"],
            "offerCount": len(c["airlines"]),
            "availability":"https://schema.org/InStock",
            "validFrom": DATE_ISO,
        }
    }, ensure_ascii=False)

    related_html = "\n".join(
        f'      <a class="fl-related-link" href="{href}"><strong>{html.escape(name)}</strong><span>{html.escape(meta)}</span></a>'
        for name, href, meta in c["related"]
    )

    desc = f"{c['origin_short']} to {c['dest_short']} flights — typical fares {c['fare_range_label']}, airline comparison, layover guide, live price search."

    head = page_head(
        c["title"] + " | The Mutapa Times",
        canonical,
        desc,
        c["stand"],
        [breadcrumb_ld, faq_ld, trip_ld, offer_ld],
        depth=2,
    )

    pullout_html = f'<p class="fl-pullout">{html.escape(c["pullout"])}</p>' if c.get("pullout") else ""

    return f'''<!doctype html>
<html class="no-js" lang="en">
{head}
<body class="fl-page">
{TOPBAR}
{DRAWER}
<main>

  <header class="fl-hero">
    <div class="fl-hero-inner">
      <p class="fl-eyebrow"><a href="/flights/">Flights</a> &middot; {c["flag_from"]} {c["origin_short"]} → {c["flag_to"]} {c["dest_short"]} &middot; {MONTH_YEAR}</p>
      <h1 class="fl-title">{html.escape(c["h1"])}</h1>
      <p class="fl-stand">{c["stand"]}</p>
      <hr class="fl-rule">
    </div>
  </header>

  {hero_block(slug, c["h1"])}

  <div class="fl-facts" role="list">
    <div class="fl-fact"><p class="fl-fact-label">Distance</p><p class="fl-fact-value">{html.escape(c["distance"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Flight time</p><p class="fl-fact-value">{html.escape(c["flight_time"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Stops</p><p class="fl-fact-value">{html.escape(c["stops"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Typical fare</p><p class="fl-fact-value">{html.escape(c["fare_range_label"])}</p></div>
  </div>

  {fare_callout_html}

  <div class="fl-widget-wrap" id="fl-widget">
    <p class="fl-widget-label">Live price search &mdash; {c["origin_short"]} → {c["dest_short"]} in {c["currency_lbl"]}</p>
    <div class="fl-widget">
      {widget}
    </div>
  </div>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">01</span><span>The route</span></p>
    <h2 class="fl-section-h2">{c["origin_short"]} to {c["dest_short"]} — the practical guide</h2>
    <div class="fl-prose">
      <p>{c["lead"]}</p>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">02</span><span>Airlines &amp; fares</span></p>
    <h2 class="fl-section-h2">Who flies it, what they charge</h2>
    <div class="fl-table-wrap">
      <table class="fl-table">
        <thead><tr><th>Airline</th><th>Routing</th><th>Typical fare</th><th>Notes</th></tr></thead>
        <tbody>
{airline_rows}
        </tbody>
      </table>
    </div>
    {pullout_html}
  </section>

  {airline_live_html}

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">03</span><span>When to book</span></p>
    <h2 class="fl-section-h2">Cheapest months and lead time</h2>
    <div class="fl-prose">
      <p>{c["season"]}</p>
    </div>
  </section>

  {monthly_html}

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">04</span><span>Layovers</span></p>
    <h2 class="fl-section-h2">Which hub to pick</h2>
    <div class="fl-prose">
      <ul>
{layover_items}
      </ul>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">05</span><span>Practical</span></p>
    <h2 class="fl-section-h2">Baggage &amp; {"visa on arrival" if slug != "from-harare" else "destination requirements"}</h2>
    <div class="fl-prose">
      <p><strong>Baggage.</strong> {c["baggage"]}</p>
      <p><strong>{"Visa." if slug != "from-harare" else "Re-entry."}</strong> {c["visa"]}</p>
    </div>
  </section>

  <aside class="fl-cta">
    <div class="fl-cta-inner">
      <h3>Before you fly: Zimbabwe eSIM</h3>
      <p>Get connectivity sorted before you land. An eSIM with a Zimbabwean data plan means you arrive online — no airport SIM queues, no roaming charges.</p>
      <a class="fl-cta-btn" href="/moving-to-zimbabwe/sim-card-and-mobile.html">Compare Zimbabwe eSIM options &rarr;</a>
    </div>
  </aside>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">06</span><span>FAQ</span></p>
    <h2 class="fl-section-h2">Frequently asked questions</h2>
    <div class="fl-faq">
{faq_html}
    </div>
  </section>

  <section class="fl-related">
    <p class="fl-section-eyebrow"><span class="fl-section-num">07</span><span>Related</span></p>
    <h2 class="fl-section-h2" style="margin-bottom:18px">Keep going</h2>
    <div class="fl-related-grid">
{related_html}
    </div>
  </section>

  <section class="fl-sources" aria-label="Sources">
    <h2>Sources &amp; further reading</h2>
    <ul>
      <li>Live price data: <a href="https://www.travelpayouts.com/" rel="noopener" target="_blank">Travelpayouts</a>, aggregating Skyscanner, Aviasales, WayAway and Kiwi.com.</li>
      <li>Fare ranges and route commentary are editorial, last reviewed {DATE_ISO}.</li>
    </ul>
    <p class="fl-sources-note">The Mutapa Times may earn a referral commission when readers book through the embedded search; this does not change the price you pay or which airlines we list.</p>
  </section>

  <p class="fl-back"><a href="/flights/">&larr; Back to all flight corridors</a></p>
{hotels_rail}</main>
{FOOTER}{hotels_script}
</body>
</html>
'''


def render_airport(slug, c):
    """Render an airport landing page (HRE / BUQ / VFA)."""
    canonical = f"https://www.mutapatimes.com/airports/{slug}/"

    # Sponsored Harare hotels carousel on the HRE airport page only.
    hotels_rail = HOTELS_RAIL if slug == "harare" else ""
    hotels_script = HOTELS_SCRIPT if slug == "harare" else ""
    facts_html = "\n".join(
        f'    <div class="fl-fact"><p class="fl-fact-label">{html.escape(lbl)}</p><p class="fl-fact-value">{html.escape(val)}</p></div>'
        for lbl, val in c["facts"]
    )
    airline_rows = "\n".join(
        f"          <tr><td><strong>{html.escape(name)}</strong></td><td>{html.escape(code)}</td><td>{html.escape(dest)}</td><td>{html.escape(freq)}</td></tr>"
        for name, code, dest, freq in c["airlines_outbound"]
    )
    getting_to_items = "\n".join(
        f"        <li><strong>{html.escape(method)}</strong> &mdash; {html.escape(note)}</li>"
        for method, note in c["getting_to"]
    )
    practical_items = "\n".join(
        f"        <li><strong>{html.escape(lbl)}.</strong> {note}</li>"
        for lbl, note in c["practical"]
    )

    faq_html = "\n".join(
        f'''        <details>
          <summary>{html.escape(q)}</summary>
          <p>{a}</p>
        </details>''' for q, a in c["faqs"]
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text": stripped(a)}} for q, a in c["faqs"]]
    }, ensure_ascii=False)

    breadcrumb_ld = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Airports","item":"https://www.mutapatimes.com/airports/"},
            {"@type":"ListItem","position":3,"name": c["h1"], "item": canonical}
        ]
    }, ensure_ascii=False)

    place_ld = json.dumps({
        "@context":"https://schema.org","@type":"Airport",
        "name": c["h1"],
        "iataCode": c["iata"],
        "icaoCode": c["icao"],
        "url": canonical,
        "address": {"@type":"PostalAddress","addressCountry":"ZW"},
        "geo": {"@type":"GeoCoordinates","latitude": c["lat"], "longitude": c["lon"]},
    }, ensure_ascii=False)

    related_html = "\n".join(
        f'      <a class="fl-related-link" href="{href}"><strong>{html.escape(name)}</strong><span>{html.escape(meta)}</span></a>'
        for name, href, meta in c["related"]
    )

    desc = f"{c['h1']} ({c['iata']}): airlines, schedule, taxi rates, visa-on-arrival info and getting to/from the airport."

    head = page_head(
        c["title"] + " | The Mutapa Times",
        canonical,
        desc,
        c["stand"],
        [breadcrumb_ld, faq_ld, place_ld],
        depth=2,
    )

    pullout_html = f'<p class="fl-pullout">{html.escape(c["pullout"])}</p>' if c.get("pullout") else ""
    iata_lower = c["iata"].lower()
    fallback_link = "https://flightaware.com/live/airport/" + c["icao"]

    return f'''<!doctype html>
<html class="no-js" lang="en">
{head}
<body class="fl-page">
{TOPBAR}
{DRAWER}
<main>

  <header class="fl-hero">
    <div class="fl-hero-inner">
      <p class="fl-eyebrow"><a href="/airports/">Airports</a> &middot; Zimbabwe &middot; {MONTH_YEAR}</p>
      <h1 class="fl-title">{html.escape(c["h1"])}</h1>
      <p class="fl-stand">{c["subtitle"]} &mdash; {c["stand"]}</p>
      <hr class="fl-rule">
    </div>
  </header>

  {hero_block(slug, c["h1"])}

  <div class="fl-facts" role="list">
{facts_html}
  </div>

  <section class="avionio-board" aria-label="Live arrivals and departures">
    <p class="avionio-label"><span class="avionio-live-dot" aria-hidden="true"></span> Live arrivals &amp; departures &middot; {c["iata"]}</p>
    <div class="avionio-tabs" role="tablist" aria-label="Flight board">
      <button type="button" class="avionio-tab is-active" data-tab="arrivals" role="tab" aria-selected="true" aria-controls="avionio-pane-arrivals">Arrivals</button>
      <button type="button" class="avionio-tab" data-tab="departures" role="tab" aria-selected="false" aria-controls="avionio-pane-departures">Departures</button>
    </div>
    <div class="avionio-pane is-active" data-pane="arrivals" id="avionio-pane-arrivals" role="tabpanel" aria-label="Arrivals">
      <iframe class="avionio-frame" data-iframe="arrivals" height="650" frameborder="0" scrolling="no"
              src="https://www.avionio.com/widget/en/{iata_lower}/arrivals"
              title="{c['iata']} arrivals"></iframe>
    </div>
    <div class="avionio-pane" data-pane="departures" id="avionio-pane-departures" role="tabpanel" aria-label="Departures" hidden>
      <iframe class="avionio-frame" data-iframe="departures" height="650" frameborder="0" scrolling="no"
              src="https://www.avionio.com/widget/en/{iata_lower}/departures"
              title="{c['iata']} departures"></iframe>
    </div>
    <p class="avionio-credit">Live data: <a href="https://www.avionio.com/en/airport/{iata_lower}/arrivals" rel="noopener" target="_blank">Avionio</a> &middot; full board on <a href="{fallback_link}" rel="noopener" target="_blank">FlightAware</a></p>
  </section>
  <script>
  (function(){{
    var tabs = document.querySelectorAll('.avionio-tab');
    var panes = document.querySelectorAll('.avionio-pane');
    tabs.forEach(function(t) {{
      t.addEventListener('click', function() {{
        var target = t.dataset.tab;
        tabs.forEach(function(t2) {{
          var active = t2 === t;
          t2.classList.toggle('is-active', active);
          t2.setAttribute('aria-selected', active ? 'true' : 'false');
        }});
        panes.forEach(function(p) {{
          var active = p.dataset.pane === target;
          p.classList.toggle('is-active', active);
          if (active) p.removeAttribute('hidden'); else p.setAttribute('hidden', '');
        }});
      }});
    }});
    window.addEventListener('message', function(e) {{
      if (typeof e.data !== 'string') return;
      var frames = document.querySelectorAll('.avionio-frame');
      var target = null;
      frames.forEach(function(f) {{ if (f.contentWindow === e.source) target = f; }});
      if (!target) return;
      if (e.data.indexOf('avionioHeight:') > -1) {{
        target.style.height = (parseInt(e.data.split('avionioHeight:')[1]) + 30) + 'px';
      }} else if (e.data.indexOf('avionioHeightScroll:') > -1) {{
        var se = document.documentElement || document.body;
        var sp = se.scrollTop - (se.scrollHeight - se.clientHeight);
        target.style.height = (parseInt(e.data.split('avionioHeightScroll:')[1]) + 30) + 'px';
        se.scrollTop = sp + se.scrollHeight - se.clientHeight;
      }}
    }}, false);
  }})();
  </script>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">01</span><span>Overview</span></p>
    <h2 class="fl-section-h2">About {c["iata"]}</h2>
    <div class="fl-prose">
      <p>{c["lead"]}</p>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">02</span><span>Airlines</span></p>
    <h2 class="fl-section-h2">Airlines &amp; routes</h2>
    <div class="fl-table-wrap">
      <table class="fl-table">
        <thead><tr><th>Airline</th><th>Code</th><th>Destination(s)</th><th>Frequency</th></tr></thead>
        <tbody>
{airline_rows}
        </tbody>
      </table>
    </div>
    {pullout_html}
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">03</span><span>Transport</span></p>
    <h2 class="fl-section-h2">Getting to {c["iata"]}</h2>
    <div class="fl-prose">
      <ul>
{getting_to_items}
      </ul>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">04</span><span>Practical</span></p>
    <h2 class="fl-section-h2">At the airport</h2>
    <div class="fl-prose">
      <ul>
{practical_items}
      </ul>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">05</span><span>FAQ</span></p>
    <h2 class="fl-section-h2">Frequently asked questions</h2>
    <div class="fl-faq">
{faq_html}
    </div>
  </section>

  <section class="fl-related">
    <p class="fl-section-eyebrow"><span class="fl-section-num">06</span><span>Related</span></p>
    <h2 class="fl-section-h2" style="margin-bottom:18px">Keep going</h2>
    <div class="fl-related-grid">
{related_html}
    </div>
  </section>

  <section class="fl-sources" aria-label="Sources">
    <h2>Sources &amp; further reading</h2>
    <ul>
      <li>Live arrivals &amp; departures: <a href="https://www.avionio.com/en/airport/{iata_lower}/arrivals" rel="noopener" target="_blank">Avionio &mdash; {c["iata"]}</a>.</li>
      <li><a href="{fallback_link}" rel="noopener" target="_blank">FlightAware live tracker for {c["iata"]}</a> (alternative).</li>
      <li><a href="https://www.acz.co.zw/" rel="noopener" target="_blank">Airports Company of Zimbabwe</a> &mdash; the operating authority.</li>
      <li>Airlines, frequencies and routes are editorial, last reviewed {DATE_ISO}; verify with the carrier before travel.</li>
    </ul>
    <p class="fl-sources-note">This page is editorial reference. Schedule and operator changes are common in Zimbabwean aviation; cross-check with the airline before booking.</p>
  </section>

  <p class="fl-back"><a href="/airports/">&larr; Back to all airports</a></p>
{hotels_rail}</main>
{FOOTER}{hotels_script}
</body>
</html>
'''


def render_hub():
    """The /flights/ hub."""
    canonical = "https://www.mutapatimes.com/flights/"
    title = f"Cheap flights to Harare {MONTH_YEAR} — diaspora flight guide"
    stand = ("A diaspora-first guide to flying Zimbabwe. Which airlines fly the route, what fares look like in low vs high season, the practical "
             "layover patterns, and a live price search per origin city. We do not sell tickets — we link out to the booking aggregators with the "
             "best published rate.")
    desc = f"Cheap flights to Harare in {MONTH_YEAR}: live price search, airline comparison, fare ranges, layover guide — for the diaspora."

    breadcrumb_ld = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Flights","item": canonical}
        ]
    }, ensure_ascii=False)
    page_ld = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title,
        "description": desc,
        "url": canonical,
        "inLanguage":"en",
        "publisher":{"@type":"Organization","name":"The Mutapa Times",
                     "logo":{"@type":"ImageObject","url":"https://www.mutapatimes.com/img/logo.png"}}
    }, ensure_ascii=False)

    head = page_head(
        title + " | The Mutapa Times",
        canonical,
        desc,
        stand,
        [breadcrumb_ld, page_ld],
        depth=1,
    )

    return f'''<!doctype html>
<html class="no-js" lang="en">
{head}
<body class="fl-page">
{TOPBAR}
{DRAWER}
<main>

  <header class="fl-hero">
    <div class="fl-hero-inner">
      <p class="fl-eyebrow">Mutapa Times &middot; Travel &middot; {MONTH_YEAR}</p>
      <h1 class="fl-title">Cheap flights to Harare</h1>
      <p class="fl-stand">{stand}</p>
      <hr class="fl-rule">
    </div>
  </header>

  <section class="fl-corridors" aria-label="Flight corridors">
    <a class="fl-corridor" href="/flights/london-to-harare/">
      <p class="fl-corridor-route">🇬🇧 London → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">London to Harare</p>
      <p class="fl-corridor-meta">Emirates &amp; Qatar via DXB/DOH, plus Ethiopian, Kenya Airways, South African. From £700.</p>
    </a>
    <a class="fl-corridor" href="/flights/johannesburg-to-harare/">
      <p class="fl-corridor-route">🇿🇦 Johannesburg → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">Johannesburg to Harare</p>
      <p class="fl-corridor-meta">1h 50m direct. SAA, Airlink, FastJet. Busiest regional corridor. From R3,500.</p>
    </a>
    <a class="fl-corridor" href="/flights/cape-town-to-harare/">
      <p class="fl-corridor-route">🇿🇦 Cape Town → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">Cape Town to Harare</p>
      <p class="fl-corridor-meta">3h direct on Airlink, or via JNB on SAA/FastJet. From R5,500.</p>
    </a>
    <a class="fl-corridor" href="/flights/sydney-to-harare/">
      <p class="fl-corridor-route">🇦🇺 Sydney → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">Sydney to Harare</p>
      <p class="fl-corridor-meta">22–28 hours, one or two stops via Gulf or Perth + Joburg. From A$1,800.</p>
    </a>
    <a class="fl-corridor" href="/flights/from-harare/">
      <p class="fl-corridor-route">🇿🇼 Harare → 🌍 Anywhere</p>
      <p class="fl-corridor-name">Flights from Harare</p>
      <p class="fl-corridor-meta">Outbound to UK, USA, SA, Dubai, Australia, Canada. Live USD search.</p>
    </a>
    <a class="fl-corridor" href="/airports/" style="grid-column: 1 / -1; background: linear-gradient(135deg, #fbfaf6 0%, #f3eedf 100%); border-left: 4px solid var(--accent);">
      <p class="fl-corridor-route">🇿🇼 Live boards &middot; HRE · BUQ · VFA</p>
      <p class="fl-corridor-name">Airport guides &amp; live arrivals/departures &rarr;</p>
      <p class="fl-corridor-meta">All three Zimbabwean international airports — live boards from Avionio, full practical guides, taxis, visa-on-arrival, SIM cards. Moved from /flights/ in May 2026.</p>
    </a>
    <a class="fl-corridor" href="/flights/london-to-victoria-falls/">
      <p class="fl-corridor-route">🇬🇧 London → 🇿🇼 Victoria Falls</p>
      <p class="fl-corridor-name">London to Victoria Falls</p>
      <p class="fl-corridor-meta">British tourist's main route to the Falls. From £800. KAZA UniVisa.</p>
    </a>
    <a class="fl-corridor" href="/flights/new-york-to-harare/">
      <p class="fl-corridor-route">🇺🇸 New York → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">New York to Harare</p>
      <p class="fl-corridor-meta">One-stop via Addis on Ethiopian, or Doha/Dubai. From $1,100.</p>
    </a>
    <a class="fl-corridor" href="/flights/dubai-to-harare/">
      <p class="fl-corridor-route">🇦🇪 Dubai → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">Dubai to Harare</p>
      <p class="fl-corridor-meta">Daily nonstop on Emirates. The only direct long-haul to Zimbabwe.</p>
    </a>
    <a class="fl-corridor" href="/flights/toronto-to-harare/">
      <p class="fl-corridor-route">🇨🇦 Toronto → 🇿🇼 Harare</p>
      <p class="fl-corridor-name">Toronto to Harare</p>
      <p class="fl-corridor-meta">One-stop on Ethiopian via Addis, or two-stop via Europe. From C$1,400.</p>
    </a>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">01</span><span>The airlines</span></p>
    <h2 class="fl-section-h2">Which airlines fly to Harare?</h2>
    <div class="fl-prose">
      <p>Harare's Robert Gabriel Mugabe International (HRE) is served by five main long-haul carriers and a fleet of regional and domestic operators:</p>
      <ul>
        <li><strong>Emirates</strong> &mdash; daily direct via Dubai (DXB). The most reliable long-haul option for UK, Australian and US passengers.</li>
        <li><strong>Qatar Airways</strong> &mdash; via Doha (DOH). Often the cheapest reliable option from the UK and a strong product.</li>
        <li><strong>Ethiopian Airlines</strong> &mdash; via Addis Ababa (ADD). The cheapest option from North America and a major hub for connections within Africa.</li>
        <li><strong>Kenya Airways</strong> &mdash; via Nairobi (NBO). Solid African network, occasionally the cheapest for European origins.</li>
        <li><strong>South African Airways</strong> &amp; <strong>Airlink</strong> &mdash; the regional carriers, dominant on Joburg–Harare and Cape Town–Harare with multiple daily frequencies.</li>
      </ul>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">02</span><span>When to book</span></p>
    <h2 class="fl-section-h2">When is the cheapest time to fly?</h2>
    <div class="fl-prose">
      <p>Harare fares move with the diaspora calendar, not the European tourism calendar. Cheapest months are typically <strong>February to May</strong> and <strong>September to early November</strong> — between the end of one school holiday and the start of the next.</p>
      <p>The expensive windows are <strong>mid-December to mid-January</strong> (Zimbabwean Christmas travel from the UK and SA), <strong>July</strong> (school-holiday-aligned visits home), and <strong>Easter week</strong>.</p>
      <p>Book 8–12 weeks ahead for the off-peak and 16+ weeks ahead for Christmas. Last-minute fares from the UK to Harare in December regularly exceed £2,000 return.</p>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">03</span><span>Flight time</span></p>
    <h2 class="fl-section-h2">How long is the flight?</h2>
    <div class="fl-prose">
      <p>Roughly: London 13–15 hours one-stop, Sydney 22–28 hours one or two stops, New York 18–22 hours one-stop, Toronto 20–24 hours one-stop, Dubai 8 hours direct, Joburg 1 hour 50 minutes direct.</p>
    </div>
  </section>

  <section class="fl-sources" aria-label="About this guide">
    <h2>About this guide</h2>
    <ul>
      <li>Live flight prices on individual corridor pages are served by <a href="https://www.travelpayouts.com/" rel="noopener" target="_blank">Travelpayouts</a>, aggregating Skyscanner, Aviasales, WayAway and Kiwi.com.</li>
      <li>Route patterns, airline list and seasonal price commentary are editorial.</li>
      <li>We may earn a referral commission when readers book through the embedded search — this does not change the price you pay and does not affect which airlines we list.</li>
    </ul>
    <p class="fl-sources-note">Last reviewed {DATE_ISO}. Spot something out of date? Email <a href="mailto:news@mutapatimes.com?subject=Flights%20guide%20update">news@mutapatimes.com</a>.</p>
  </section>
</main>
{FOOTER}
</body>
</html>
'''


def stripped(s):
    """Strip HTML tags from a string for JSON-LD answer text."""
    import re
    return re.sub(r"<[^>]+>", "", s).replace("&amp;", "&").replace("&mdash;", "—").replace("&middot;", "·").replace("&hellip;", "…").replace("&rarr;", "→").replace("&larr;", "←")


# ---------------------------------------------------------------------------
# AIRPORTS HUB (/airports/) — live boards for all three airports
# ---------------------------------------------------------------------------

def render_airports_hub():
    canonical = "https://www.mutapatimes.com/airports/"
    title = f"Zimbabwe airport guide — live arrivals & departures | {MONTH_YEAR}"
    desc = ("Live arrivals and departures for Harare (HRE), Bulawayo (BUQ) and "
            "Victoria Falls (VFA) — the three main Zimbabwean international airports. "
            "Practical guides, airline directories and route corridors.")
    breadcrumb_ld = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Airports","item": canonical},
        ],
    }, ensure_ascii=False)
    page_ld = json.dumps({
        "@context":"https://schema.org","@type":"CollectionPage",
        "headline": title, "description": desc, "url": canonical, "inLanguage":"en",
    }, ensure_ascii=False)

    # Build a tabbed live-board block: 3 airport tabs, each with arrivals+departures
    airports_meta = [
        ("harare", "Harare (HRE)", "hre", "https://flightaware.com/live/airport/FVHA"),
        ("bulawayo", "Bulawayo (BUQ)", "buq", "https://flightaware.com/live/airport/FVBU"),
        ("victoria-falls", "Victoria Falls (VFA)", "vfa", "https://flightaware.com/live/airport/FVFA"),
    ]
    airport_tabs = "\n".join(
        f'      <button type="button" class="ap-tab{" is-active" if i==0 else ""}" data-airport-tab="{slug}" role="tab" aria-selected="{"true" if i==0 else "false"}" aria-controls="ap-pane-{slug}">{html.escape(label)}</button>'
        for i, (slug, label, _, _) in enumerate(airports_meta)
    )
    airport_panes = []
    for i, (slug, label, iata_lower, fa_link) in enumerate(airports_meta):
        active_cls = " is-active" if i == 0 else ""
        airport_panes.append(f'''<div class="ap-pane{active_cls}" data-airport-pane="{slug}" id="ap-pane-{slug}" role="tabpanel" aria-label="{html.escape(label)}"{"" if i==0 else " hidden"}>
        <div class="avionio-board">
          <div class="avionio-tabs" role="tablist" aria-label="{html.escape(label)} board">
            <button type="button" class="avionio-tab is-active" data-board-tab="arrivals" data-for="{slug}" role="tab" aria-selected="true">Arrivals</button>
            <button type="button" class="avionio-tab" data-board-tab="departures" data-for="{slug}" role="tab" aria-selected="false">Departures</button>
          </div>
          <div class="avionio-pane is-active" data-board-pane="arrivals-{slug}">
            <iframe class="avionio-frame" data-iframe="{slug}-arr" height="500" frameborder="0" scrolling="no"
                    src="https://www.avionio.com/widget/en/{iata_lower}/arrivals" title="{html.escape(label)} arrivals"></iframe>
          </div>
          <div class="avionio-pane" data-board-pane="departures-{slug}" hidden>
            <iframe class="avionio-frame" data-iframe="{slug}-dep" height="500" frameborder="0" scrolling="no"
                    src="https://www.avionio.com/widget/en/{iata_lower}/departures" title="{html.escape(label)} departures"></iframe>
          </div>
          <p class="avionio-credit">Live data: <a href="https://www.avionio.com/en/airport/{iata_lower}/arrivals" rel="noopener" target="_blank">Avionio</a> &middot; full board on <a href="{fa_link}" rel="noopener" target="_blank">FlightAware</a> &middot; <a href="/airports/{slug}/">full airport guide &rarr;</a></p>
        </div>
      </div>''')
    panes_html = "\n      ".join(airport_panes)

    head = page_head(
        title + " | The Mutapa Times",
        canonical,
        desc,
        desc,
        [breadcrumb_ld, page_ld],
        depth=1,
    )

    return f'''<!doctype html>
<html class="no-js" lang="en">
{head}
<body class="fl-page">
{TOPBAR}
{DRAWER}
<main>
  <header class="fl-hero">
    <div class="fl-hero-inner">
      <p class="fl-eyebrow">Mutapa Times &middot; Airports &middot; {MONTH_YEAR}</p>
      <h1 class="fl-title">Zimbabwe airport guide</h1>
      <p class="fl-stand">Live arrivals and departures for Harare, Bulawayo and Victoria Falls
        &mdash; plus practical guides for each airport, the airlines that fly them, and the
        most-flown route corridors. Switch airports with the tabs below.</p>
      <hr class="fl-rule">
    </div>
  </header>

  <section class="ap-board-wrap" aria-label="Live arrivals and departures across all airports">
    <p class="avionio-label" style="max-width:1080px;margin:24px auto 12px;padding:0 24px"><span class="avionio-live-dot" aria-hidden="true"></span> Live boards &middot; arrivals &amp; departures</p>
    <div class="ap-tabs" role="tablist" aria-label="Airport selector">
{airport_tabs}
    </div>
    <div class="ap-panes">
      {panes_html}
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">01</span><span>The airports</span></p>
    <h2 class="fl-section-h2">Three gateways</h2>
    <div class="fl-corridors" style="margin:14px 0 0">
      <a class="fl-corridor" href="/airports/harare/">
        <p class="fl-corridor-route">🇿🇼 HRE / FVHA</p>
        <p class="fl-corridor-name">Harare International</p>
        <p class="fl-corridor-meta">The main international gateway. Emirates, Qatar, Ethiopian, Kenya Airways, SAA. ~3M annual passengers. 15 km from CBD.</p>
      </a>
      <a class="fl-corridor" href="/airports/bulawayo/">
        <p class="fl-corridor-route">🇿🇼 BUQ / FVBU</p>
        <p class="fl-corridor-name">Joshua Mqabuko Nkomo International (Bulawayo)</p>
        <p class="fl-corridor-meta">Daily JNB direct via Airlink, FastJet. Domestic to HRE and VFA. ~200K passengers. 25 km from CBD.</p>
      </a>
      <a class="fl-corridor" href="/airports/victoria-falls/">
        <p class="fl-corridor-route">🇿🇼 VFA / FVFA</p>
        <p class="fl-corridor-name">Victoria Falls International</p>
        <p class="fl-corridor-meta">The tourism gateway. BA seasonal direct from LHR. Ethiopian, Airlink CPT & JNB. ~600K passengers. 18 km from town.</p>
      </a>
    </div>
  </section>

  <section class="fl-section">
    <p class="fl-section-eyebrow"><span class="fl-section-num">02</span><span>Inbound corridors</span></p>
    <h2 class="fl-section-h2">Most-flown routes to Zimbabwe</h2>
    <div class="fl-corridors" style="margin:14px 0 0">
      <a class="fl-corridor" href="/flights/london-to-harare/">
        <p class="fl-corridor-route">🇬🇧 London → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">London to Harare</p>
        <p class="fl-corridor-meta">From £700. Qatar, Ethiopian, Emirates, Kenya Airways.</p>
      </a>
      <a class="fl-corridor" href="/flights/london-to-victoria-falls/">
        <p class="fl-corridor-route">🇬🇧 London → 🇿🇼 Victoria Falls</p>
        <p class="fl-corridor-name">London to Victoria Falls</p>
        <p class="fl-corridor-meta">From £800. The tourist route. KAZA UniVisa.</p>
      </a>
      <a class="fl-corridor" href="/flights/johannesburg-to-harare/">
        <p class="fl-corridor-route">🇿🇦 Johannesburg → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">Johannesburg to Harare</p>
        <p class="fl-corridor-meta">1h 50m direct. SAA, Airlink, FastJet. From R3,500.</p>
      </a>
      <a class="fl-corridor" href="/flights/cape-town-to-harare/">
        <p class="fl-corridor-route">🇿🇦 Cape Town → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">Cape Town to Harare</p>
        <p class="fl-corridor-meta">3h direct on Airlink. From R5,500.</p>
      </a>
      <a class="fl-corridor" href="/flights/sydney-to-harare/">
        <p class="fl-corridor-route">🇦🇺 Sydney → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">Sydney to Harare</p>
        <p class="fl-corridor-meta">22–28 hours. From A$1,800.</p>
      </a>
      <a class="fl-corridor" href="/flights/new-york-to-harare/">
        <p class="fl-corridor-route">🇺🇸 New York → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">New York to Harare</p>
        <p class="fl-corridor-meta">From $1,100. Ethiopian via Addis.</p>
      </a>
      <a class="fl-corridor" href="/flights/dubai-to-harare/">
        <p class="fl-corridor-route">🇦🇪 Dubai → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">Dubai to Harare</p>
        <p class="fl-corridor-meta">Direct on Emirates. The only nonstop long-haul.</p>
      </a>
      <a class="fl-corridor" href="/flights/toronto-to-harare/">
        <p class="fl-corridor-route">🇨🇦 Toronto → 🇿🇼 Harare</p>
        <p class="fl-corridor-name">Toronto to Harare</p>
        <p class="fl-corridor-meta">From C$1,400. Ethiopian YYZ–ADD.</p>
      </a>
      <a class="fl-corridor" href="/flights/from-harare/">
        <p class="fl-corridor-route">🇿🇼 Harare → 🌍 Anywhere</p>
        <p class="fl-corridor-name">Flights from Harare</p>
        <p class="fl-corridor-meta">Outbound to UK, USA, SA, Australia, Canada, Dubai.</p>
      </a>
    </div>
  </section>

  <section class="fl-sources" aria-label="About this page">
    <h2>About this page</h2>
    <ul>
      <li>Live arrivals and departures data: <a href="https://www.avionio.com/" rel="noopener" target="_blank">Avionio</a>. Fallback live status: FlightAware.</li>
      <li>Route corridor fare ranges + airline data: aggregated from <a href="https://www.travelpayouts.com/" rel="noopener" target="_blank">Travelpayouts</a> (Skyscanner, Aviasales, WayAway).</li>
      <li>Practical airport guides (taxi rates, visa info, SIM card) are editorial, last reviewed {DATE_ISO}.</li>
    </ul>
  </section>
</main>
{FOOTER}
<style>
.ap-board-wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }}
.ap-tabs {{ display: flex; gap: 4px; border-bottom: 2px solid var(--rule);
  max-width: 1080px; margin: 0 auto; }}
.ap-tab {{ background: none; border: 0; padding: 14px 22px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 1em; font-weight: 600;
  color: var(--text-light); cursor: pointer; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: color 0.15s, border-color 0.15s; }}
.ap-tab:hover {{ color: var(--ink); }}
.ap-tab.is-active {{ color: var(--accent); border-bottom-color: var(--accent); }}
.ap-panes {{ max-width: 1080px; margin: 0 auto; }}
.ap-pane {{ display: none; padding: 18px 0 0; }}
.ap-pane.is-active {{ display: block; }}
</style>
<script>
(function() {{
  // Airport tab switcher
  var apTabs = Array.from(document.querySelectorAll('.ap-tab'));
  var apPanes = Array.from(document.querySelectorAll('.ap-pane'));
  apTabs.forEach(function(t) {{
    t.addEventListener('click', function() {{
      var target = t.dataset.airportTab;
      apTabs.forEach(function(t2) {{
        var on = t2 === t;
        t2.classList.toggle('is-active', on);
        t2.setAttribute('aria-selected', on ? 'true' : 'false');
      }});
      apPanes.forEach(function(p) {{
        var on = p.dataset.airportPane === target;
        p.classList.toggle('is-active', on);
        if (on) p.removeAttribute('hidden'); else p.setAttribute('hidden', '');
      }});
    }});
  }});
  // Per-airport arrivals/departures tab switcher
  document.querySelectorAll('.avionio-tab[data-board-tab]').forEach(function(t) {{
    t.addEventListener('click', function() {{
      var slug = t.dataset.for;
      var which = t.dataset.boardTab;
      var siblings = document.querySelectorAll('.avionio-tab[data-for="' + slug + '"]');
      siblings.forEach(function(s) {{
        var on = s === t;
        s.classList.toggle('is-active', on);
        s.setAttribute('aria-selected', on ? 'true' : 'false');
      }});
      document.querySelectorAll('[data-board-pane^="arrivals-' + slug + '"], [data-board-pane^="departures-' + slug + '"]').forEach(function(p) {{
        var paneType = p.dataset.boardPane.split('-')[0];
        var on = paneType === which;
        p.classList.toggle('is-active', on);
        if (on) p.removeAttribute('hidden'); else p.setAttribute('hidden', '');
      }});
    }});
  }});
  // Avionio iframe auto-resize (matches each iframe to its message)
  window.addEventListener('message', function(e) {{
    if (typeof e.data !== 'string') return;
    var frames = document.querySelectorAll('.avionio-frame');
    var target = null;
    frames.forEach(function(f) {{ if (f.contentWindow === e.source) target = f; }});
    if (!target) return;
    if (e.data.indexOf('avionioHeight:') > -1) {{
      target.style.height = (parseInt(e.data.split('avionioHeight:')[1]) + 30) + 'px';
    }} else if (e.data.indexOf('avionioHeightScroll:') > -1) {{
      var se = document.documentElement || document.body;
      var sp = se.scrollTop - (se.scrollHeight - se.clientHeight);
      target.style.height = (parseInt(e.data.split('avionioHeightScroll:')[1]) + 30) + 'px';
      se.scrollTop = sp + se.scrollHeight - se.clientHeight;
    }}
  }}, false);
}})();
</script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# REDIRECT STUBS — bounce old /flights/<airport-slug>/ to new /airports/<slug>/
# ---------------------------------------------------------------------------

def write_redirect(old_dir, new_url, label):
    """Write a minimal HTML at old_dir/index.html that meta-refreshes to new_url
    and includes a canonical link. GitHub Pages-friendly (no .htaccess)."""
    old_dir.mkdir(parents=True, exist_ok=True)
    (old_dir / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>Moved — {html.escape(label)} | The Mutapa Times</title>
<link rel="canonical" href="{new_url}">
<meta name="robots" content="noindex, follow">
<meta http-equiv="refresh" content="0; url={new_url}">
<script>location.replace("{new_url}");</script>
</head><body>
<p style="font-family:Inter,sans-serif;text-align:center;margin:80px auto;max-width:480px">
  This page has moved to <a href="{new_url}">{html.escape(new_url)}</a>.
</p>
</body></html>
''')


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------

(OUT / "index.html").write_text(render_hub())
print(f"wrote /flights/index.html")

for slug, cfg in CORRIDORS.items():
    out_dir = OUT / slug
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(render_corridor(slug, cfg))
    print(f"wrote /flights/{slug}/index.html")

# Airports now live at /airports/<slug>/  (was /flights/<slug>-airport/)
for slug, cfg in AIRPORTS.items():
    out_dir = AIRPORTS_OUT / slug
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(render_airport(slug, cfg))
    print(f"wrote /airports/{slug}/index.html")

# Airports hub
(AIRPORTS_OUT / "index.html").write_text(render_airports_hub())
print(f"wrote /airports/index.html")

# Redirect stubs from the old /flights/<airport-slug>/ URLs
old_to_new = [
    ("harare-airport",         "harare",         "Harare International"),
    ("bulawayo-airport",       "bulawayo",       "Bulawayo Airport"),
    ("victoria-falls-airport", "victoria-falls", "Victoria Falls Airport"),
]
for old_slug, new_slug, label in old_to_new:
    write_redirect(OUT / old_slug, f"https://www.mutapatimes.com/airports/{new_slug}/", label)
    print(f"wrote redirect: /flights/{old_slug}/ -> /airports/{new_slug}/")

print(f"\nDone. Month: {MONTH_YEAR}")
