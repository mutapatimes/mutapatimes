#!/usr/bin/env python3
"""Build the ZB Bank advertising demo by cloning live site pages and
injecting ZB ad placements + the password gate.

Source pages cloned (unchanged structure, ads inserted in dedicated slots):
  index.html, fx.html, property.html, articles.html
  5 real wire articles (sample selection)

Plus 3 ZB-authored sponsored articles, each rendered in the wire-article
template so they sit alongside real articles in the feed.

Output: /zb-demo/...
"""
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "zb-demo"
ART_DEMO = DEMO / "articles"

# Wire articles to clone into the demo. Their internal "more to read"
# links point to other wire articles by relative path; we don't rewrite
# those, so the reader leaves the demo if they click through (acceptable).
WIRE_SLUGS = [
    "2026-05-18-the-great-diaspora-takeover-how-zimbos-abroad-are-quietly-bu",
    "2026-05-19-exclusive-use-safari-camp-opens-on-zimbabwes-jafuta-reserve",
    "2026-05-18-namibia-joins-south-africa-and-zimbabwe-in-bold-southern-afr",
    "2026-05-18-over-70-smuggled-vehicles-seized-in-major-clampdown",
    "2026-05-17-against-all-odds-zimbabwe-bets-big-on-diamonds-amid-global-i",
]

# ── ad HTML fragments ───────────────────────────────────────────────
RIBBON = '<div class="zb-demo-ribbon" aria-hidden="true">ZB Bank · Sponsored content demo</div>'

def leaderboard(headline, img, cta):
    return f'''<aside class="zb-ad-leaderboard" role="complementary" aria-label="Advertisement">
  <div class="zb-ad-leaderboard-inner">
    <div class="zb-ad-leaderboard-copy">
      <span class="zb-ad-label">Advertisement</span>
      <h3 class="zb-ad-leaderboard-headline">{headline}</h3>
      <a class="zb-ad-cta" href="https://www.zb.co.zw/diaspora-hub" target="_blank" rel="noopener sponsored">{cta}</a>
    </div>
    <div class="zb-ad-leaderboard-image" style="background-image:url('/img/uploads/zb_bank_demo_site/{img}')"></div>
  </div>
</aside>'''

LEADERBOARD      = leaderboard("Buying back home, on your terms.",
                               "ZB_NEW_HOME_BUYERS.png", "Open an account →")
LEADERBOARD_PROP = leaderboard("Stands in Beitbridge, Ruwa, Bulawayo &amp; Greendale.",
                               "Homebuilding_zb_bank.png", "View stands →")
LEADERBOARD_FX   = leaderboard("Holding value across currencies.",
                               "DIASPORA_CURRENT_ACCOUNT.png", "Talk to ZB →")

def rail(img, headline, cta):
    return f'''<aside class="zb-ad-rail" role="complementary" aria-label="Advertisement">
  <span class="zb-ad-label">Advertisement</span>
  <div class="zb-ad-rail-image" style="background-image:url('/img/uploads/zb_bank_demo_site/{img}')"></div>
  <div class="zb-ad-rail-body">
    <h3 class="zb-ad-rail-headline">{headline}</h3>
    <a class="zb-ad-cta" href="https://www.zb.co.zw/diaspora-hub" target="_blank" rel="noopener sponsored">{cta}</a>
  </div>
</aside>'''

RAIL_MORTGAGE = rail("ZB_NEW_HOME_BUYERS.png",
                     "Buy back home — from abroad.", "Apply now →")
RAIL_FUNERAL  = rail("FUNERAL_ZB_BANK.png",
                     "A fitting farewell, prepared.", "Get a quote →")
RAIL_ACCOUNT  = rail("DIASPORA_CURRENT_ACCOUNT.png",
                     "Banking from where you are.", "Open an account →")
RAIL_BUILD    = rail("Homebuilding_zb_bank.png",
                     "Build, with the bank in your corner.", "Speak to ZB →")

def tile(href, img, headline):
    return f'''<a class="zb-ad-tile" href="{href}" target="_blank" rel="noopener sponsored">
  <span class="zb-ad-label">Advertisement</span>
  <div class="zb-ad-tile-image" style="background-image:url('/img/uploads/zb_bank_demo_site/{img}')"></div>
  <div class="zb-ad-tile-body">
    <h3 class="zb-ad-tile-headline">{headline}</h3>
  </div>
</a>'''

TILE_MORTGAGE = tile(
    "https://www.zb.co.zw/diaspora-hub",
    "ZB_NEW_HOME_BUYERS.png",
    "Buying back home, on your terms.",
)

FOOTER_AD = '''<aside class="zb-ad-footer" role="complementary" aria-label="Advertisement">
  <div class="zb-ad-footer-inner">
    <span class="zb-ad-label">Advertisement</span>
    <h3>Built with the diaspora in mind &mdash; for you.</h3>
    <a class="zb-ad-cta" href="https://www.zb.co.zw/diaspora-hub" target="_blank" rel="noopener sponsored">Talk to ZB →</a>
  </div>
</aside>'''


# ── transforms ──────────────────────────────────────────────────────
def head_inject(html: str, depth: int) -> str:
    rel = "" if depth == 0 else "../"
    inj = (f'<link rel="stylesheet" href="{rel}zb-ads.css">\n'
           f'<script src="{rel}zb-gate.js" defer></script>')
    return html.replace("</head>", inj + "\n</head>", 1)

def body_inject(html: str) -> str:
    return re.sub(r'(<body[^>]*>)', r'\1\n' + RIBBON, html, count=1)

def rewrite_assets_to_absolute(html: str) -> str:
    """Rewrite relative asset URLs (css/, js/, img/, data/, etc.) to
    absolute paths so they resolve correctly from the /zb-demo/ subtree.
    Idempotent — only rewrites if not already absolute."""
    patterns = [
        # Quoted attributes pointing at root-relative folders
        (r'(href|src)="(css|js|img|data)/', r'\1="/\2/'),
        (r'(href|src)="\.\./(css|js|img|data)/', r'\1="/\2/'),
        # Site root file references (manifest, favicons, sw)
        (r'(href|src)="(site\.webmanifest|sw\.js|icon\.png|favicon\.ico|feed\.xml)"',
         r'\1="/\2"'),
        (r'(href|src)="\.\./(site\.webmanifest|sw\.js|icon\.png|favicon\.ico|feed\.xml)"',
         r'\1="/\2"'),
    ]
    for pat, repl in patterns:
        html = re.sub(pat, repl, html)
    return html

def rewrite_links(html: str) -> str:
    """Keep top-level demo nav inside /zb-demo/. Articles slugs that we
    cloned are rewritten to point at the demo copy; others fall through."""
    html = rewrite_assets_to_absolute(html)
    pairs = [
        ('href="/"', 'href="/zb-demo/"'),
        ('href="/fx"', 'href="/zb-demo/fx.html"'),
        ('href="/property"', 'href="/zb-demo/property.html"'),
        ('href="/articles"', 'href="/zb-demo/articles.html"'),
    ]
    for old, new in pairs:
        html = html.replace(old, new)
    # Rewrite relative breadcrumbs in cloned articles
    html = html.replace('href="../index.html"', 'href="/zb-demo/index.html"')
    html = html.replace('href="../articles.html"', 'href="/zb-demo/articles.html"')
    return html

def inject_after_datehr(html: str, fragment: str) -> str:
    """Slot a block right after the masthead's dateHr."""
    return html.replace('<hr class="dateHr">',
                        '<hr class="dateHr">\n' + fragment, 1)

def inject_before_subscribe(html: str, fragment: str) -> str:
    """Slot a block before the 'Essential subscribe' section."""
    return html.replace('<section class="essential-subscribe"',
                        fragment + '\n<section class="essential-subscribe"', 1)

def inject_into_news_grid(html: str, fragment: str) -> str:
    """Slot a sponsored tile after the first card in the news grid on
    the homepage. The homepage feed cards live inside #news-grid; we
    inject the tile a few cards in so it doesn't grab the lead slot."""
    # Best-effort: try to find the news-grid container and insert.
    m = re.search(r'<div[^>]+id="news-grid"[^>]*>', html)
    if not m:
        return html
    # Insert fragment immediately after the container open tag, so it
    # appears first — but JS may rebuild the grid; for the demo this is
    # fine because the JS appends without clearing static children that
    # carry the .zb-ad-tile class. To be safe we put it just before the
    # grid closing as a fallback.
    return html.replace(m.group(0), m.group(0) + '\n' + fragment, 1)

def inject_into_articles_grid(html: str, fragment: str) -> str:
    """Slot a sponsored tile near the top of the articles landing grid."""
    m = re.search(r'<div[^>]+class="[^"]*articles-list-grid[^"]*"[^>]*>', html)
    if not m:
        return html
    return html.replace(m.group(0), m.group(0) + '\n' + fragment, 1)

def inject_top_of_article_body(html: str, fragment: str) -> str:
    """For an article detail page: float a sidebar ad inside the article
    body so it acts as a sidebar on desktop, full-width below on mobile."""
    return html.replace('<div class="article-body">',
                        '<div class="article-body">' + fragment, 1)

def inject_before_share(html: str, fragment: str) -> str:
    return html.replace('<div class="article-share">',
                        fragment + '\n<div class="article-share">', 1)


# ── page-specific recipes ──────────────────────────────────────────
def transform_index(src: str) -> str:
    h = src
    h = head_inject(h, depth=0)
    h = body_inject(h)
    h = rewrite_links(h)
    h = inject_after_datehr(h, LEADERBOARD)
    h = inject_into_news_grid(h, TILE_MORTGAGE)
    h = inject_before_subscribe(h, FOOTER_AD)
    return h

def transform_fx(src: str) -> str:
    h = src
    h = head_inject(h, depth=0)
    h = body_inject(h)
    h = rewrite_links(h)
    h = inject_after_datehr(h, LEADERBOARD_FX)
    h = inject_before_subscribe(h, FOOTER_AD)
    return h

def transform_property(src: str) -> str:
    h = src
    h = head_inject(h, depth=0)
    h = body_inject(h)
    h = rewrite_links(h)
    h = inject_after_datehr(h, LEADERBOARD_PROP)
    h = inject_before_subscribe(h, FOOTER_AD)
    return h

def transform_articles(src: str) -> str:
    h = src
    h = head_inject(h, depth=0)
    h = body_inject(h)
    h = rewrite_links(h)
    h = inject_after_datehr(h, LEADERBOARD)
    # Add a sponsored tile mixed into the grid
    h = inject_into_articles_grid(h, TILE_MORTGAGE)
    h = inject_before_subscribe(h, FOOTER_AD)
    return h

def transform_article_detail(src: str, rail_html: str) -> str:
    h = src
    h = head_inject(h, depth=1)
    h = body_inject(h)
    h = rewrite_links(h)
    # Top leaderboard goes after the masthead chrome but inside main flow.
    # The article template doesn't have a dateHr at the same place; use a
    # different anchor: between </header><main> we can't easily target. We
    # instead inject a thin leaderboard before <main>.
    h = h.replace('<!-- Single article view -->',
                  LEADERBOARD + '\n  <!-- Single article view -->', 1)
    # Float the rail ad inside the article body
    h = inject_top_of_article_body(h, rail_html)
    # Footer banner before subscribe
    h = inject_before_subscribe(h, FOOTER_AD)
    return h


# ── sponsored ZB articles (rendered in the wire-article template) ──
def sponsored_article(title: str, deck: str, slug: str, hero_img: str,
                      body_html: str, byline: str = "Tendai Kuwanda",
                      date: str = "May 17, 2026", category: str = "Sponsored · ZB Bank") -> str:
    """Generate a wire-article-template HTML page with ZB content."""
    sponsor_disclosure = (
        '<aside class="zb-sponsor-disclosure">'
        '<strong>Sponsored briefing by ZB Bank</strong>'
        'This article is produced by The Mutapa Times sponsored-content desk on behalf of ZB Financial Holdings. '
        'It sits alongside our editorial coverage but is paid for by the named sponsor. '
        'Editorial views in our newsroom are not affected.'
        '</aside>'
    )
    nav_inner = '''<a target="_self" class="notranslate" href="/zb-demo/">News</a>
        <a target="_self" class="economy-btn" href="/economy">Economy</a>
        <a target="_self" class="notranslate" href="/zb-demo/fx.html">FX</a>
        <a target="_self" class="notranslate" href="/zb-demo/property.html">Property</a>
        <a target="_self" class="notranslate" href="/jobs">Jobs</a>
        <a target="_self" class="notranslate" href="/arts">Arts</a>
        <a target="_self" class="active notranslate" href="/zb-demo/articles.html">Articles</a>'''
    nav_pees = "\n      ".join(f"<p>{a.strip()}</p>" for a in nav_inner.strip().splitlines())

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} | The Mutapa Times — Sponsored</title>
<meta name="robots" content="noindex, nofollow">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{deck}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'">
<link rel="stylesheet" href="../../css/normalize.css">
<link rel="stylesheet" href="../../css/main.css?v=102">
<link rel="stylesheet" href="../zb-ads.css">
<script src="../zb-gate.js" defer></script>
</head>
<body>
{RIBBON}
<div class="topbar" id="topbar"><a href="/zb-demo/" class="topbar-brand"><em>The Mutapa Times</em></a><a href="/subscribe" class="topbar-cta">Subscribe</a></div>
<div class="paper">
  <a href="/zb-demo/" class="title-link">
    <div class="titleDiv"><h1 class="title notranslate">THE MUTAPA TIMES</h1></div>
    <h4 class="sub notranslate">Zimbabwe outside-in</h4>
  </a>
  <nav id="mainNav">
      {nav_pees}
  </nav>
  <hr class="topHr"><hr class="bottomHr"><hr class="dateHr">

  {LEADERBOARD}

  <main>
    <article class="article-full">
      <nav class="article-breadcrumb" aria-label="Breadcrumb">
        <a href="/zb-demo/index.html">Home</a> <span aria-hidden="true">/</span>
        <a href="/zb-demo/articles.html">Articles</a> <span aria-hidden="true">/</span>
        <span>{title}</span>
      </nav>
      <div class="article-header">
        <span class="article-category-tag" style="background:#7bba1f;color:#fff">{category}</span>
        <h1 class="article-title">{title}</h1>
        <div class="article-meta">
          <span class="article-author">By {byline} · For ZB Financial Holdings</span>
          <time class="article-date">{date}</time>
        </div>
      </div>
      <div class="article-body">
        {sponsor_disclosure}
        <p><img src="/img/uploads/zb_bank_demo_site/{hero_img}" alt="{title}" style="width:100%;max-height:520px;object-fit:cover;display:block;margin:0 0 20px"></p>
        {body_html}
      </div>
      <div class="article-back" style="margin-top:36px"><a href="/zb-demo/articles.html">&larr; All articles</a></div>
    </article>
  </main>
  <hr class="dateHr">

  {FOOTER_AD}

</div>
</body>
</html>
'''


SPONSORED = [
    {
        "slug": "zb-sustainability-certification",
        "title": "ZB becomes Zimbabwe's first SSCI-certified bank.",
        "deck": "A five-year sustainability programme earns ZB an international certification — and a benchmark the rest of the country's banks are now working toward.",
        "hero": "ZB_GENERIC_PORTRAIT.png",
        "body": '''<p>ZB Bank has become the first financial institution in Zimbabwe to be awarded sustainability certification under the Sustainability Standards Certification Initiative (SSCI) — a framework supported by the European Organisation for Sustainable Development and adopted by the Reserve Bank of Zimbabwe as the new benchmark for the country's banking sector.</p>
<p>The certification is the public marker of a five-year shift inside the bank. From 2021, ZB embedded sustainability into its strategic pillars; sustainability is now woven through the group's vision, mission and values, alongside the more familiar drivers of profitability and growth.</p>
<blockquote style="border-left:4px solid #7bba1f;padding:8px 0 8px 18px;margin:20px 0;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:20px;line-height:1.4">
We have been certified as a nation, from that point, to say that the manner in which we want to conduct business is meeting the standards required at the international level on a sustainability basis.
<cite style="display:block;margin-top:10px;font-style:normal;font-family:Inter,sans-serif;font-size:12px;letter-spacing:0.1em;text-transform:uppercase;color:#5a5447">Dr Shepherd Fungura · Group CEO, ZB Financial Holdings</cite>
</blockquote>
<h2>Why the central bank pushed it</h2>
<p>The RBZ's view, articulated by Deputy Governor Dr Jesimen Chipika at the certification briefing, is that the country's banking sector needs to be both <em>profitable</em> and <em>resilient</em> — and that the discipline required to achieve SSCI standards delivers on both.</p>
<p>Of the country's 19 large banks, 15 are now enrolled in the SSCI process, alongside three smaller institutions — taking the participating share of the sector above 90%. ZB is the first across the line.</p>
<p>The framework requires more than environmental impact reporting. It tests how a bank governs itself, how it lends, which sectors it supports, and how its products serve people who would otherwise sit outside the formal financial system. It maps to environmental, social and governance (ESG) standards and connects directly to the United Nations Sustainable Development Goals.</p>
<h2>Three high-impact goals</h2>
<p>ZB Bank's chief executive, Mr Elisha Chibvuri, has named three priorities the bank is now organising itself around: <strong>financial inclusion</strong>, the <strong>agricultural value chain</strong>, and <strong>sustainable infrastructure investment</strong> — including the work the bank is doing on Green Climate Fund accreditation, which uses the SSCI certification as a reference.</p>
<h2>Three years, then renew</h2>
<p>The SSCI certification is valid for three years. To retain it, ZB has to evidence continued alignment with the framework's environmental, social, and governance criteria — which means the strategy embedded from 2021 cannot quietly become last-cycle's marketing material.</p>
<p>Dr Fungura confirmed the group is working with other Zimbabwean institutions on their own certification pipelines. For ZB, the certification serves as the formal opening of the 2026–2030 strategy cycle.</p>''',
    },
    {
        "slug": "zb-diaspora-mortgage-explained",
        "title": "Buying back home from abroad: ZB's diaspora mortgage, explained.",
        "deck": "A 25% deposit, a ten-year term, and a clear list of documents. We walk through what ZB's diaspora mortgage actually requires.",
        "hero": "ZB_NEW_HOME_BUYERS.png",
        "body": '''<p>For Zimbabweans abroad, the question of how to buy a home back home tends to sit in the back of the mind for years before becoming the question of the year. ZB Bank's Mortgage Plan, available to its Diaspora Current Account holders, is one of the routes — and on paper, one of the more structured.</p>
<h2>The shape of the loan</h2>
<ul>
<li><strong>Deposit:</strong> 25% of the property's valued price. The bank funds the remainder.</li>
<li><strong>Maximum term:</strong> ten years, per current ZB policy.</li>
<li><strong>Interest rate:</strong> set per risk profile — not a flat rate; the bank's offer depends on the applicant's documented income, credit history and the property itself.</li>
<li><strong>Interest treatment:</strong> compounded daily, posted at month-end.</li>
<li><strong>Offer letter:</strong> valid for one month — once issued, the clock is on.</li>
</ul>
<h2>What you actually need to file</h2>
<p>Before a mortgage application can move, the bank requires a Diaspora Current Account with ZB. That account, in turn, has its own document set, which is the bigger hurdle for most applicants. To open it you need certified or notarised copies of work permit and passport, proof of residence within three months, three months of host-country bank statements, a stamped reference letter, two recent passport photos, proof of income, and a credit bureau report.</p>
<p>Then the mortgage application proper requires a USD$100 application fee, a positive ID, a letter explaining the purpose of the loan, the property's title deeds (unbonded) and a current credit report. Buying an existing property additionally requires a signed, dated sale agreement and proof of income.</p>
<h2>Build, buy, or improve</h2>
<p>ZB offers three flavours of mortgage that matter to diaspora applicants. The <em>Flexi Mortgage Plan</em> lets you borrow up to 25% of valuation against property you already own. The standard <em>Mortgage Plan Individual</em> is the buy-an-existing-property route. The <em>Building Loan</em> funds construction from the ground up, with the bank releasing funds against inspections at each stage.</p>
<h2>The fees that are easy to miss</h2>
<p>The headline is the deposit. The line items that catch first-time applicants are the bond registration fee, the valuation fee (which on the Flexi plan can be capitalised and spread over six months), administration fees set by bank policy, and a one-month-valid offer letter that means you cannot leave the conveyancing to drift.</p>
<h2>If it works</h2>
<p>The structural advantage of ZB's diaspora mortgage isn't the rate; it's that the bank already knows you. If you've held the Diaspora Current Account for a couple of years and been remitting through it, the bank can underwrite against your own ZB transaction history rather than a thin file. That's the bit that turns "considering it for a few more years" into "offer letter in hand by the next visit home".</p>''',
    },
    {
        "slug": "dr-shepherd-fungura-profile",
        "title": "Dr Shepherd Fungura, the actuary leading ZB into its next chapter.",
        "deck": "Twenty-four years across banking, insurance and pensions — and a five-year plan that takes the group to 2030.",
        "hero": "Screenshot 2026-05-20 at 15.02.27.png",
        "body": '''<p>The route to running a financial services group in Zimbabwe rarely starts in the same place twice. For Dr Shepherd Tapiwanashe Fungura, the Group CEO of ZB Financial Holdings, it started in actuarial science — the discipline most banking executives encounter only as a column in the risk report.</p>
<p>An honours graduate of NUST in actuarial science, Dr Fungura went on to complete a doctorate in entrepreneurship and innovation in Italy. He holds Fellowship of the Actuarial Society of South Africa (FASSA) and Fellowship of the Institute of Actuaries (FIA). The career, by his own count, runs to more than 24 years across banking, life and non-life insurance, investments, pensions, and enterprise risk management, in Zimbabwe and abroad.</p>
<h2>The actuary's lens</h2>
<p>Actuaries are trained to price the future. Where most bankers learn to read a balance sheet, an actuary learns to read a probability distribution — the distribution of claims on an insurance book, of defaults on a loan portfolio, of payouts on a pension scheme over decades. It is a discipline of patience.</p>
<p>Dr Fungura's tenure at the top of ZB Financial Holdings has been characterised by precisely that quality. The group has been running on five-year strategy cycles — a cadence that lets compounding effects show — and the 2021–2025 cycle ended, in May 2026, with ZB Bank becoming Zimbabwe's first SSCI-certified financial institution.</p>
<h2>Two boards, several lifetimes</h2>
<p>Dr Fungura has been President of the Actuarial Society of Zimbabwe (ASZ) and an Executive Member of the Insurance Council of Zimbabwe (ICZ). He sits on multiple company boards as a non-executive director and is a member of the Institute of Directors of Zimbabwe (IoDZ). The portfolio looks like the kind of professional capital that takes a generation to assemble — and indeed it has.</p>
<p>What's interesting is how that depth shows up in the bank's posture. ZB has been less noisy than some of its peers about retail growth and digital launches; quieter about pricing wars. It has instead positioned itself around the long, structural conversation about how a Zimbabwean financial institution can be both profitable <em>and</em> resilient.</p>
<h2>What 2026–2030 looks like</h2>
<p>The new cycle takes the group through to 2030. Dr Fungura has been measured about what it adds; the bank's stated high-impact goals — financial inclusion, the agricultural value chain, sustainable infrastructure — are evolutions of the 2021–2025 themes rather than a reset. Green Climate Fund accreditation is on the work plan; so is a continued push on diaspora services.</p>
<p>If the previous five years were about putting sustainability into the bank's bones, the next five years — on the actuary's reading — are about pricing the long horizon of that decision into every product the bank ships.</p>''',
    },
]


# ── main ──────────────────────────────────────────────────────────
def main():
    DEMO.mkdir(exist_ok=True)
    ART_DEMO.mkdir(exist_ok=True)

    # Top-level pages
    pages = [
        ("index.html",     "index.html",     transform_index),
        ("fx.html",        "fx.html",        transform_fx),
        ("property.html",  "property.html",  transform_property),
        ("articles.html",  "articles.html",  transform_articles),
    ]
    for src_name, out_name, transform in pages:
        src_path = ROOT / src_name
        if not src_path.exists():
            print(f"  skip (missing): {src_name}")
            continue
        out = transform(src_path.read_text())
        (DEMO / out_name).write_text(out)
        print(f"  wrote zb-demo/{out_name}  ({len(out)//1024} KB)")

    # Wire articles — cycle through a small set of rail ads so different
    # articles show different ZB products.
    rails = [RAIL_MORTGAGE, RAIL_ACCOUNT, RAIL_FUNERAL, RAIL_BUILD, RAIL_MORTGAGE]
    for i, slug in enumerate(WIRE_SLUGS):
        src_path = ROOT / "articles" / f"{slug}.html"
        if not src_path.exists():
            print(f"  skip (missing wire): {slug}")
            continue
        out = transform_article_detail(src_path.read_text(), rails[i % len(rails)])
        (ART_DEMO / f"{slug}.html").write_text(out)
        print(f"  wrote zb-demo/articles/{slug}.html")

    # Sponsored ZB articles
    for s in SPONSORED:
        html = sponsored_article(
            title=s["title"], deck=s["deck"], slug=s["slug"],
            hero_img=s["hero"], body_html=s["body"],
        )
        (ART_DEMO / f"{s['slug']}.html").write_text(html)
        print(f"  wrote zb-demo/articles/{s['slug']}.html  (sponsored)")

    print("done.")


if __name__ == "__main__":
    main()
