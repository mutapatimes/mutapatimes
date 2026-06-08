#!/usr/bin/env python3
"""Build /fx/<corridor>/ landing pages.

Two page types:
  1. Rate pages:      /fx/<from>-to-zwl/   e.g. /fx/usd-to-zwl/, /fx/gbp-to-zwl/
  2. Send-money:      /fx/send-money-from-<country>-to-zimbabwe/  e.g. .../from-uk-...

Both pull from data/fx-rates.json + data/remittance-providers.json, and refresh
client-side from /data/fx-rates.json so the displayed rate stays current as the
nightly cron updates the data file.
"""
import json, re, html
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT  = ROOT / "fx"
OUT.mkdir(exist_ok=True)
TODAY = "2026-05-22"

fx = json.loads((ROOT / "data" / "fx-rates.json").read_text())
remit = json.loads((ROOT / "data" / "remittance-providers.json").read_text())
rates = fx["rates"]
as_of = fx.get("as_of", TODAY)

# Currency metadata
CURRENCIES = {
    "USD": {"name": "US Dollar",        "country": "United States", "flag": "🇺🇸", "country_slug": "usa"},
    "GBP": {"name": "British Pound",    "country": "United Kingdom","flag": "🇬🇧", "country_slug": "uk"},
    "ZAR": {"name": "South African Rand","country":"South Africa", "flag": "🇿🇦", "country_slug": "south-africa"},
    "EUR": {"name": "Euro",             "country": "Eurozone",      "flag": "🇪🇺", "country_slug": "eurozone"},
    "AUD": {"name": "Australian Dollar","country": "Australia",     "flag": "🇦🇺", "country_slug": "australia"},
    "CAD": {"name": "Canadian Dollar",  "country": "Canada",        "flag": "🇨🇦", "country_slug": "canada"},
    "AED": {"name": "UAE Dirham",       "country": "United Arab Emirates","flag":"🇦🇪","country_slug": "uae"},
    "ZWG": {"name": "Zimbabwe Gold",    "country": "Zimbabwe",      "flag": "🇿🇼", "country_slug": "zimbabwe"},
}

def rate(src, dst):
    """USD-based cross rate. fx['rates'] is X per 1 USD. So src→dst = rates[dst]/rates[src]."""
    return rates[dst] / rates[src]

def fmt(v, dp=4):
    if v >= 100:    return f"{v:,.2f}"
    if v >= 1:      return f"{v:,.4f}".rstrip("0").rstrip(".")
    return f"{v:,.6f}".rstrip("0").rstrip(".")

# --- CSS (reuses main palette) ----------------------------------------------
CSS = """
.fxc-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
.fxc-section-header { padding: 24px 20px 4px; max-width: 1000px; margin: 0 auto; }
.fxc-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.fxc-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.fxc-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1.02em;
  line-height: 1.55; color: var(--text-mid); margin: 0 0 14px; max-width: 44em; }
.fxc-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 8px 0 0; }

/* Big rate display */
.fxc-hero-rate { max-width: 1000px; margin: 18px auto 8px; padding: 22px 24px;
  background: var(--paper); border: 1px solid var(--rule); border-radius: 12px;
  display: flex; flex-wrap: wrap; gap: 18px 32px; align-items: baseline;
  justify-content: space-between; }
.fxc-hero-rate-from { font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.78em; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-light); font-weight: 600; margin: 0 0 4px; }
.fxc-hero-rate-val { font-family: 'Playfair Display', Georgia, serif;
  font-weight: 700; font-size: clamp(1.8em, 5vw, 3em); line-height: 1.05;
  color: var(--ink); margin: 0; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.fxc-hero-rate-asof { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-light); margin: 6px 0 0; }

/* Conversion ladder */
.fxc-ladder { max-width: 1000px; margin: 12px auto 22px; padding: 0 20px; }
.fxc-ladder h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; color: var(--ink); margin: 0 0 12px; }
.fxc-ladder-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px; }
.fxc-ladder-cell { padding: 12px 14px; background: #fff; border: 1px solid var(--rule);
  border-radius: 8px; }
.fxc-ladder-from { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-light); margin: 0 0 4px; }
.fxc-ladder-to { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.2em; color: var(--ink); margin: 0; font-variant-numeric: tabular-nums; }

/* Providers table */
.fxc-providers { max-width: 1000px; margin: 22px auto; padding: 0 20px; }
.fxc-providers h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 12px; }
.fxc-prov-table-wrap { overflow-x: auto; }
.fxc-prov-table { width: 100%; border-collapse: collapse;
  font-family: 'Inter', system-ui, sans-serif; font-size: 0.92em;
  background: #fff; border: 1px solid var(--rule); border-radius: 8px; overflow: hidden; }
.fxc-prov-table thead th { text-align: left; padding: 10px 14px; background: var(--paper);
  border-bottom: 1px solid var(--rule); font-size: 0.72em; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-light); white-space: nowrap; }
.fxc-prov-table tbody td { padding: 12px 14px; border-bottom: 1px solid var(--rule); color: var(--text); }
.fxc-prov-table tbody tr:last-child td { border-bottom: 0; }
.fxc-prov-table tbody tr:hover { background: var(--paper); }
.fxc-prov-table a { color: var(--ink); font-weight: 600; text-decoration: none; }
.fxc-prov-table a:hover { color: var(--accent); }
.fxc-prov-name { font-weight: 600; }
.fxc-prov-notes { font-size: 0.85em; color: var(--text-light); margin-top: 3px; }
.fxc-prov-margin { font-variant-numeric: tabular-nums; }
.fxc-prov-margin.best { color: #1f7a3e; font-weight: 700; }
.fxc-prov-cta { display: inline-block; padding: 6px 12px; background: var(--ink);
  color: #fff !important; text-decoration: none !important; border-radius: 4px;
  font-size: 0.82em; font-weight: 600; white-space: nowrap; }
.fxc-prov-cta:hover { background: var(--accent); }

/* FAQ */
.fxc-faq { max-width: 720px; margin: 22px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.fxc-faq h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 14px; }
.fxc-faq details { background: var(--paper); border: 1px solid var(--rule);
  border-radius: 8px; padding: 0; margin: 0 0 8px; }
.fxc-faq summary { padding: 12px 16px; font-weight: 600; cursor: pointer;
  color: var(--ink); font-size: 0.98em; list-style: none; }
.fxc-faq summary::-webkit-details-marker { display: none; }
.fxc-faq summary::after { content: '＋'; float: right; color: var(--accent);
  font-weight: 400; transition: transform 0.15s; }
.fxc-faq details[open] summary::after { content: '−'; }
.fxc-faq details > p { padding: 0 16px 14px; margin: 0; line-height: 1.6;
  color: var(--text); font-size: 0.95em; }

.fxc-prose { max-width: 720px; margin: 0 auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.fxc-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; color: var(--ink); margin: 26px 0 10px; }
.fxc-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.fxc-prose ul, .fxc-prose ol { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.fxc-prose li { margin-bottom: 5px; }
.fxc-prose a { color: var(--accent); text-decoration: underline; }
.fxc-prose strong { color: var(--ink); }

.fxc-related { max-width: 1000px; margin: 22px auto; padding: 0 20px; }
.fxc-related h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; color: var(--ink); margin: 0 0 12px; }
.fxc-related-grid { display: grid; gap: 10px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
.fxc-related-link { display: block; padding: 14px 16px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); font-family: 'Inter', system-ui, sans-serif;
  transition: border-color 0.15s, transform 0.15s; }
.fxc-related-link:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.fxc-related-link strong { color: var(--ink); display: block; margin-bottom: 2px; font-size: 0.95em; }
.fxc-related-link span { font-size: 0.82em; color: var(--text-light); }

.fxc-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.fxc-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700; font-family: inherit; }
.fxc-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55; color: var(--text); }
.fxc-sources a { color: var(--ink); text-decoration: underline; }
.fxc-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }
"""

HEAD_COMMON = """    <meta charset="utf-8">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4428529474445353" crossorigin="anonymous"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="../../site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="../../icon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="../../css/normalize.css">
    <link rel="stylesheet" href="../../css/main.css?v=102">
    <link rel="icon" type="image/png" sizes="32x32" href="../../img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../../img/favicon-16x16.png">
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
</script>"""

# JS that refreshes the rate client-side from /data/fx-rates.json
def refresh_js(src, dst, ladder_amts):
    return f"""<script>
(function() {{
  fetch('/data/fx-rates.json', {{cache: 'no-store'}}).then(function(r) {{ return r.json(); }}).then(function(j) {{
    var rates = j.rates || {{}};
    var src = '{src}', dst = '{dst}';
    if (!(src in rates) || !(dst in rates)) return;
    var r = rates[dst] / rates[src];
    var fmt = function(v) {{ return v >= 100 ? v.toLocaleString('en-US', {{maximumFractionDigits:2}})
                                              : v >= 1 ? Number(v.toFixed(4)).toString()
                                              : Number(v.toFixed(6)).toString(); }};
    var el = document.getElementById('fxcRate'); if (el) el.textContent = fmt(r);
    var asof = document.getElementById('fxcAsOf'); if (asof) asof.textContent = 'Updated ' + (j.as_of || j.fetched_at || '');
    [{",".join(str(a) for a in ladder_amts)}].forEach(function(amt) {{
      var c = document.getElementById('fxcLad' + amt); if (c) c.textContent = fmt(amt * r);
    }});
  }}).catch(function(){{}});
}})();
</script>"""

# --- Rate page (e.g. /fx/gbp-to-zwl/) --------------------------------------
LADDER = [1, 10, 50, 100, 500, 1000, 5000]

def render_rate_page(src, dst):
    src_meta = CURRENCIES[src]
    dst_meta = CURRENCIES[dst]
    r = rate(src, dst)
    pair_label = f"{src} to {dst}"
    pair_slug = f"{src.lower()}-to-{dst.lower()}"
    page_dir = OUT / pair_slug
    page_dir.mkdir(exist_ok=True)

    title = f"{src} to {dst} exchange rate today &mdash; {fmt(r)} {dst} per 1 {src}"
    h1 = f"{src} to {dst} exchange rate today"
    desc = (f"Today's {src_meta['name']} to {dst_meta['name']} ({dst}) exchange rate: "
            f"1 {src} = {fmt(r)} {dst}. Live mid-market rate, conversion ladder, "
            f"and best money-transfer providers for the {src_meta['country']}-to-{dst_meta['country']} corridor.")

    ladder_cells = ""
    for amt in LADDER:
        ladder_cells += f'''      <div class="fxc-ladder-cell">
        <p class="fxc-ladder-from">{src_meta['flag']} {amt:,} {src}</p>
        <p class="fxc-ladder-to" id="fxcLad{amt}">{fmt(amt * r)}</p>
      </div>
'''

    # Providers (only for dst=ZWG and src in remit.routes)
    providers_html = ""
    if dst == "ZWG" and src in remit["routes"]:
        route = remit["routes"][src]
        provs = sorted(route["providers"], key=lambda p: p["fx_margin_pct"] + p["fee"]/100)
        rows = ""
        for i, p in enumerate(provs):
            best_cls = "best" if i == 0 else ""
            effective = r * (1 - p["fx_margin_pct"]/100)
            rows += f'''        <tr>
          <td>
            <div class="fxc-prov-name">{html.escape(p["name"])}</div>
            <div class="fxc-prov-notes">{html.escape(p.get("payout","—"))} &middot; {html.escape(p.get("speed","—"))}</div>
          </td>
          <td class="fxc-prov-margin {best_cls}">{p["fx_margin_pct"]:.1f}%</td>
          <td class="fxc-prov-margin">{src} {p["fee"]:.2f}</td>
          <td class="fxc-prov-margin">{fmt(effective)}</td>
          <td><a class="fxc-prov-cta" href="{html.escape(p["url"])}" rel="noopener nofollow sponsored" target="_blank">Send via {html.escape(p["name"])}</a></td>
        </tr>
'''
        providers_html = f'''<section class="fxc-providers">
  <h2>Best providers to send {src} to Zimbabwe</h2>
  <p class="fxc-prose"><span style="font-family:'Inter',system-ui,sans-serif;color:var(--text-mid);font-size:0.92em;line-height:1.55">Ranked by combined FX spread and flat fee. Effective rate is the mid-market rate ({fmt(r)}) minus the provider's spread. Always verify on the provider site before sending.</span></p>
  <div class="fxc-prov-table-wrap">
    <table class="fxc-prov-table">
      <thead><tr><th>Provider</th><th>Spread</th><th>Fee</th><th>Effective rate</th><th>&nbsp;</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</section>'''

    # FAQ
    faqs = []
    faqs.append((
        f"What is the {src} to {dst} exchange rate today?",
        f"1 {src} = {fmt(r)} {dst} at the mid-market rate as of {as_of}. Rates change every minute on the interbank market — the rate you actually receive will depend on the provider's spread and fees. See the provider comparison above."
    ))
    if dst == "ZWG":
        faqs.append((
            "Is ZWG the same as ZiG or Zim Gold?",
            "Yes. ZWG is the ISO 4217 currency code for Zimbabwe Gold (often written as ZiG locally), Zimbabwe's gold-backed currency introduced in April 2024 to replace the old Zimbabwean dollar (ZWL)."
        ))
        faqs.append((
            "What is the difference between the official rate and the parallel-market rate?",
            "The official rate is the interbank rate published by the Reserve Bank of Zimbabwe. The parallel-market rate is the rate at which ZWG actually trades on the street, typically at a premium of 10–30%. For inbound remittances paid out in USD, this gap rarely matters; for ZWG payouts, it does."
        ))
    if dst == "ZWG" and src in remit["routes"]:
        cheap = sorted(remit["routes"][src]["providers"], key=lambda p: p["fx_margin_pct"] + p["fee"]/100)[0]
        faqs.append((
            f"What is the cheapest way to send {src} to Zimbabwe?",
            f"For the {src_meta['country']}-to-Zimbabwe corridor at typical retail volumes, {cheap['name']} usually offers the best combined rate, with a {cheap['fx_margin_pct']:.1f}% FX spread and a {src} {cheap['fee']:.2f} flat fee. Effective rate: ~{fmt(r * (1 - cheap['fx_margin_pct']/100))} {dst} per 1 {src}. {cheap.get('notes','')}"
        ))
    faqs.append((
        "How often is this rate updated?",
        "The mid-market rate displayed on this page is refreshed daily from open.er-api.com, an interbank composite feed. The rate on this page is the latest published value; for live tick-by-tick rates, use the provider's own calculator at send-time."
    ))

    faq_html = ""
    faq_ld = []
    for q, a in faqs:
        faq_html += f'''  <details>
    <summary>{html.escape(q)}</summary>
    <p>{html.escape(a)}</p>
  </details>
'''
        faq_ld.append({"@type":"Question","name": q, "acceptedAnswer":{"@type":"Answer","text": a}})

    # Related currency links
    related = []
    for s2 in ["USD","GBP","ZAR","EUR","AUD","CAD","AED"]:
        if s2 == src or s2 == dst: continue
        related.append((s2, dst, CURRENCIES[s2]["country"]))
    related_html = ""
    for s2, d2, country in related:
        slug = f"{s2.lower()}-to-{d2.lower()}"
        r2 = rate(s2, d2)
        related_html += f'<a class="fxc-related-link" href="/fx/{slug}/"><strong>{s2} → {d2}</strong><span>{country} &middot; 1 {s2} = {fmt(r2)} {d2}</span></a>\n'

    ld_faq = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity": faq_ld}, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"FX rates","item":"https://www.mutapatimes.com/fx/"},
            {"@type":"ListItem","position":3,"name": f"{src} to {dst}","item": f"https://www.mutapatimes.com/fx/{pair_slug}/"},
        ]
    }, ensure_ascii=False)
    ld_xrate = json.dumps({
        "@context":"https://schema.org","@type":"ExchangeRateSpecification",
        "currency": dst, "currentExchangeRate": {"@type":"UnitPriceSpecification","price": round(r, 6),"priceCurrency": dst},
        "validFrom": as_of,
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{title} | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/fx/{pair_slug}/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://www.mutapatimes.com/fx/{pair_slug}/">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_xrate}</script>
<script type="application/ld+json">{ld_faq}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="fxc-section-header">
    <p class="fxc-eyebrow">FX rates &middot; {src_meta['flag']} {src} → {dst_meta['flag']} {dst}</p>
    <h1 class="fxc-title">{h1}</h1>
    <p class="fxc-stand">{html.escape(desc)}</p>
    <hr class="fxc-rule">
  </header>

  <div class="fxc-hero-rate">
    <div>
      <p class="fxc-hero-rate-from">1 {src_meta['flag']} {src_meta['name']} =</p>
      <p class="fxc-hero-rate-val"><span id="fxcRate">{fmt(r)}</span> <span style="font-size:0.6em;color:var(--text-mid);font-weight:400">{dst}</span></p>
      <p class="fxc-hero-rate-asof" id="fxcAsOf">Updated {as_of}</p>
    </div>
    <div style="text-align:right">
      <p class="fxc-hero-rate-from">1 {dst_meta['flag']} {dst} =</p>
      <p class="fxc-hero-rate-val" style="font-size:1.6em">{fmt(1/r)} <span style="font-size:0.65em;color:var(--text-mid);font-weight:400">{src}</span></p>
    </div>
  </div>

  <section class="fxc-ladder">
    <h2>Quick conversion: {src} to {dst}</h2>
    <div class="fxc-ladder-grid">
{ladder_cells}    </div>
  </section>

  {providers_html}

  <section class="fxc-faq">
    <h2>Frequently asked questions</h2>
{faq_html}  </section>

  <div class="fxc-prose">
    <h2>How this rate is calculated</h2>
    <p>The {src} to {dst} rate on this page is the mid-market (interbank) cross
      rate, computed from <a href="https://open.er-api.com" rel="noopener" target="_blank">open.er-api.com</a>'s
      daily USD baseline. It is the rate banks use when they trade with each
      other &mdash; not the rate you receive at a money-transfer provider, which
      will be slightly lower after their spread and fees.</p>
    <p>For real-time conversion across {len(rates)-1} currencies, use the
      <a href="/fx/">Mutapa Times FX converter</a>. For the send-money
      calculator with live provider comparison, see our
      <a href="/fx/">main FX page</a>.</p>
  </div>

  <section class="fxc-related">
    <h2>Other rates to {dst}</h2>
    <div class="fxc-related-grid">
{related_html}    </div>
  </section>

  <section class="fxc-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://open.er-api.com/v6/latest/USD" rel="noopener" target="_blank">open.er-api.com</a> &mdash; interbank composite rate (daily update)</li>
      <li>Provider spreads &amp; fees: hand-curated by The Mutapa Times, last reviewed {remit.get("_last_reviewed", TODAY)}</li>
    </ul>
    <p class="fxc-sources-note">Rates are indicative, not real-time. Verify the rate
      and fees on the provider's own site at send-time before transferring funds.
      This page is editorial &mdash; The Mutapa Times may earn referral revenue
      from links to money-transfer providers, which does not affect our ranking.</p>
  </section>
</main>
{FOOTER}
{refresh_js(src, dst, LADDER)}
</body>
</html>
'''
    (page_dir / "index.html").write_text(out)

# --- Send-money page (e.g. /fx/send-money-from-uk-to-zimbabwe/) ------------
def render_send_money_page(src):
    if src not in remit["routes"]: return
    src_meta = CURRENCIES[src]
    route = remit["routes"][src]
    slug = f"send-money-from-{src_meta['country_slug']}-to-zimbabwe"
    page_dir = OUT / slug
    page_dir.mkdir(exist_ok=True)
    provs = sorted(route["providers"], key=lambda p: p["fx_margin_pct"] + p["fee"]/100)
    r_zwg = rate(src, "ZWG")
    cheap = provs[0]

    title = f"Send money from {src_meta['country']} to Zimbabwe &mdash; cheapest providers, {src} to ZWG rate today"
    h1 = f"Send money from {src_meta['country']} to Zimbabwe"
    desc = (f"How to send {src} from {src_meta['country']} to Zimbabwe — current "
            f"rate ({fmt(r_zwg)} ZWG per 1 {src}), the cheapest provider "
            f"({cheap['name']}: {cheap['fx_margin_pct']:.1f}% spread, {src} {cheap['fee']:.2f} fee), "
            "and a side-by-side comparison of all major remittance providers.")

    rows = ""
    for i, p in enumerate(provs):
        best_cls = "best" if i == 0 else ""
        eff = r_zwg * (1 - p["fx_margin_pct"]/100)
        rows += f'''        <tr>
          <td>
            <div class="fxc-prov-name">{html.escape(p["name"])}</div>
            <div class="fxc-prov-notes">{html.escape(p.get("notes",""))}</div>
          </td>
          <td class="fxc-prov-margin {best_cls}">{p["fx_margin_pct"]:.1f}%</td>
          <td class="fxc-prov-margin">{src} {p["fee"]:.2f}</td>
          <td>{html.escape(p.get("payout","—"))}</td>
          <td>{html.escape(p.get("speed","—"))}</td>
          <td class="fxc-prov-margin">{fmt(eff)}</td>
          <td><a class="fxc-prov-cta" href="{html.escape(p["url"])}" rel="noopener nofollow sponsored" target="_blank">Send →</a></td>
        </tr>
'''

    faqs = [
        (f"What is the cheapest way to send money from {src_meta['country']} to Zimbabwe?",
         f"Based on combined FX spread and flat fees, {cheap['name']} is typically the cheapest for typical retail amounts: a {cheap['fx_margin_pct']:.1f}% spread and a {src} {cheap['fee']:.2f} fee, paying out via {cheap.get('payout','—')}. For very small or very large amounts, run the calculator on the provider's own site as fee structures change at thresholds."),
        ("How long does it take to send money from " + src_meta['country'] + " to Zimbabwe?",
         "It depends on the provider and the payout method. Mobile money payouts (EcoCash, OneMoney) usually arrive in minutes. Cash pickup at branches (Mukuru, ZB Bank, OK Mart) is also minutes. USD bank deposits can take a few hours to one business day. Bank-to-bank transfers without using a remittance specialist can take 2–5 days and cost considerably more."),
        ("Is it legal to send money to Zimbabwe?",
         f"Yes. {src_meta['country']} has no restrictions on outbound remittances to Zimbabwe. Inbound remittances are encouraged by the Reserve Bank of Zimbabwe and are typically paid out in USD or via mobile money in ZWG."),
        ("Can I send to EcoCash or OneMoney from " + src_meta['country'] + "?",
         "Yes. WorldRemit, Mukuru and Sasai support EcoCash and OneMoney mobile-money payouts. Wise and Remitly typically only deposit to USD bank accounts. Check each provider's payout list for the current options."),
        ("What's the difference between USD and ZWG payout?",
         "Most providers offer USD bank deposit as the default — this avoids any currency conversion at the Zimbabwean end. ZWG (Zim Gold) payouts convert at the provider's chosen rate, which may not match the official rate. For most diaspora purposes, USD payout is simpler."),
    ]
    faq_html = ""
    faq_ld = []
    for q, a in faqs:
        faq_html += f'''  <details>
    <summary>{html.escape(q)}</summary>
    <p>{html.escape(a)}</p>
  </details>
'''
        faq_ld.append({"@type":"Question","name": q, "acceptedAnswer":{"@type":"Answer","text": a}})

    related_html = ""
    for code in ["USD","GBP","ZAR","AUD","CAD","EUR"]:
        if code == src or code not in CURRENCIES: continue
        m = CURRENCIES[code]
        related_html += f'<a class="fxc-related-link" href="/fx/send-money-from-{m["country_slug"]}-to-zimbabwe/"><strong>{m["flag"]} {m["country"]} → ZW</strong><span>Send {code} to Zimbabwe</span></a>\n'
    # Add link to rate page
    related_html += f'<a class="fxc-related-link" href="/fx/{src.lower()}-to-zwl/"><strong>{src} → ZWG rate</strong><span>Today\'s {src}/ZWG exchange rate</span></a>\n'

    ld_faq = json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity": faq_ld}, ensure_ascii=False)
    ld_breadcrumb = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"FX rates","item":"https://www.mutapatimes.com/fx/"},
            {"@type":"ListItem","position":3,"name": f"Send money from {src_meta['country']} to Zimbabwe","item": f"https://www.mutapatimes.com/fx/{slug}/"},
        ]
    }, ensure_ascii=False)
    ld_howto = json.dumps({
        "@context":"https://schema.org","@type":"HowTo",
        "name": f"How to send money from {src_meta['country']} to Zimbabwe",
        "totalTime":"PT5M",
        "step":[
            {"@type":"HowToStep","name":"Compare providers","text":f"Compare {len(provs)} major providers for the {src}-to-Zimbabwe corridor by FX spread and fee."},
            {"@type":"HowToStep","name":"Sign up","text":"Create an account with the provider, verifying ID and the source of funds as required."},
            {"@type":"HowToStep","name":"Add recipient","text":"Add the Zimbabwe recipient with their EcoCash number, OneMoney number, USD bank account, or cash-pickup ID."},
            {"@type":"HowToStep","name":"Send","text":f"Enter the amount in {src}, confirm the recipient receives in their chosen currency, and authorise the transfer."},
        ],
    }, ensure_ascii=False)

    out = f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <title>{title} | The Mutapa Times</title>
    <link rel="canonical" href="https://www.mutapatimes.com/fx/{slug}/">
{HEAD_COMMON}
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="https://www.mutapatimes.com/fx/{slug}/">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{html.escape(desc)}">
<script type="application/ld+json">{ld_faq}</script>
<script type="application/ld+json">{ld_howto}</script>
<script type="application/ld+json">{ld_breadcrumb}</script>
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="fxc-section-header">
    <p class="fxc-eyebrow">Send money &middot; {src_meta['flag']} {src_meta['country']} → 🇿🇼 Zimbabwe</p>
    <h1 class="fxc-title">{h1}</h1>
    <p class="fxc-stand">{html.escape(desc)}</p>
    <hr class="fxc-rule">
  </header>

  <div class="fxc-hero-rate">
    <div>
      <p class="fxc-hero-rate-from">Mid-market rate today</p>
      <p class="fxc-hero-rate-val"><span id="fxcRate">{fmt(r_zwg)}</span> <span style="font-size:0.6em;color:var(--text-mid);font-weight:400">ZWG per 1 {src}</span></p>
      <p class="fxc-hero-rate-asof" id="fxcAsOf">Updated {as_of}</p>
    </div>
    <div style="text-align:right">
      <p class="fxc-hero-rate-from">Cheapest provider</p>
      <p class="fxc-hero-rate-val" style="font-size:1.6em">{html.escape(cheap["name"])}</p>
      <p class="fxc-hero-rate-asof">{cheap['fx_margin_pct']:.1f}% spread &middot; {src} {cheap['fee']:.2f} fee</p>
    </div>
  </div>

  <section class="fxc-providers">
    <h2>Provider comparison &mdash; {len(provs)} options for {src} → ZWG</h2>
    <div class="fxc-prov-table-wrap">
      <table class="fxc-prov-table">
        <thead><tr><th>Provider</th><th>Spread</th><th>Fee</th><th>Payout</th><th>Speed</th><th>Effective rate</th><th>&nbsp;</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </section>

  <div class="fxc-prose">
    <h2>How to send money to Zimbabwe in four steps</h2>
    <ol>
      <li><strong>Compare providers above.</strong> The cheapest by combined cost
        for typical retail amounts is currently {html.escape(cheap['name'])}. Effective
        rate ~{fmt(r_zwg * (1 - cheap['fx_margin_pct']/100))} ZWG per 1 {src}.</li>
      <li><strong>Sign up</strong> with the provider. {src_meta['country']} regulators
        require ID verification (passport or driving licence) and a proof of address.</li>
      <li><strong>Add your Zimbabwean recipient</strong> with their EcoCash or OneMoney
        number, a USD bank account number, or a cash-pickup ID. Mobile money is fastest;
        USD bank deposit is most flexible.</li>
      <li><strong>Send.</strong> Enter the amount, confirm the rate and fee, and authorise
        the transfer. Most arrive within minutes (mobile money) to one business day (bank).</li>
    </ol>

    <h2>What currency should I send in?</h2>
    <p>The default and simplest is to send {src} and have the recipient receive
      <strong>USD</strong> in Zimbabwe — either to a USD bank account or as cash pickup.
      USD circulates freely alongside ZWG and most prices are still quoted in USD.</p>
    <p>If your recipient specifically wants <strong>ZWG (Zim Gold)</strong>, choose a
      provider that pays out to an EcoCash or OneMoney ZWG wallet. Note that the
      provider will convert at their own rate, not the parallel-market rate.</p>
  </div>

  <section class="fxc-faq">
    <h2>Frequently asked questions</h2>
{faq_html}  </section>

  <section class="fxc-related">
    <h2>Other corridors &amp; rates</h2>
    <div class="fxc-related-grid">
{related_html}    </div>
  </section>

  <section class="fxc-sources" aria-label="Sources">
    <h2>Sources</h2>
    <ul>
      <li><a href="https://open.er-api.com/v6/latest/USD" rel="noopener" target="_blank">open.er-api.com</a> &mdash; interbank composite rate</li>
      <li>Provider spreads &amp; fees: hand-curated by The Mutapa Times, last reviewed {remit.get("_last_reviewed", TODAY)}. {html.escape(remit.get("_disclaimer",""))}</li>
    </ul>
    <p class="fxc-sources-note">This page is editorial. The Mutapa Times may earn
      referral revenue from links to money-transfer providers, which does not affect
      our ranking by effective rate.</p>
  </section>
</main>
{FOOTER}
{refresh_js(src, "ZWG", LADDER)}
</body>
</html>
'''
    (page_dir / "index.html").write_text(out)

# --- Run --------------------------------------------------------------------
# Rate pages: from {USD,GBP,ZAR,EUR,AUD,CAD,AED} to {ZWG}
# Plus a few popular Zimbabwean diaspora cross-pairs
RATE_PAIRS = [
    ("USD","ZWG"), ("GBP","ZWG"), ("ZAR","ZWG"),
    ("EUR","ZWG"), ("AUD","ZWG"), ("CAD","ZWG"), ("AED","ZWG"),
    ("GBP","USD"), ("ZAR","USD"), ("GBP","ZAR"),
]
print(f"Building {len(RATE_PAIRS)} rate pages…")
for src, dst in RATE_PAIRS:
    render_rate_page(src, dst)
    print(f"  /fx/{src.lower()}-to-{dst.lower()}/")

print(f"\nBuilding {len(remit['routes'])} send-money pages…")
for src in remit["routes"]:
    if src not in CURRENCIES: continue
    render_send_money_page(src)
    slug = f"send-money-from-{CURRENCIES[src]['country_slug']}-to-zimbabwe"
    print(f"  /fx/{slug}/")

print(f"\nDone.")
