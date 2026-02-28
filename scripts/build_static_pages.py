#!/usr/bin/env python3
"""
Build static HTML pages for articles and people.

Articles: Reads markdown from content/articles/, generates articles/{slug}.html
People:   Queries Wikidata SPARQL + Wikipedia, generates people/{id}.html

Run: python3 scripts/build_static_pages.py
"""
import glob
import json
import os
import re
import sys
import html as html_mod
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode
from urllib.error import URLError

BASE_URL = "https://www.mutapatimes.com"
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")
ARTICLES_SRC = os.path.join(ROOT_DIR, "content", "articles")
ARTICLES_OUT = os.path.join(ROOT_DIR, "articles")
PEOPLE_OUT = os.path.join(ROOT_DIR, "people")


# ─── Markdown → HTML (mirrors js/articles.js markdownToHtml) ──────────────
def markdown_to_html(md):
    h = md
    # Headings
    h = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", h, flags=re.MULTILINE)
    h = re.sub(r"^### (.+)$", r"<h3>\1</h3>", h, flags=re.MULTILINE)
    h = re.sub(r"^## (.+)$", r"<h2>\1</h2>", h, flags=re.MULTILINE)
    h = re.sub(r"^# (.+)$", r"<h1>\1</h1>", h, flags=re.MULTILINE)
    # Bold + italic combos
    h = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", h)
    h = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", h)
    h = re.sub(r"\*(.+?)\*", r"<em>\1</em>", h)
    # Images
    h = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" class="article-body-img">', h)
    # Links
    h = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', h)
    # Unordered lists
    h = re.sub(r"^- (.+)$", r"<li>\1</li>", h, flags=re.MULTILINE)
    h = re.sub(r"((?:<li>.*?</li>\n?)+)", r"<ul>\1</ul>", h)
    # Horizontal rules
    h = re.sub(r"^---$", "<hr>", h, flags=re.MULTILINE)
    # Blockquotes
    h = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", h, flags=re.MULTILINE)
    # Paragraphs
    h = re.sub(r"\n\n+", "\n</p>\n<p>\n", h)
    h = "<p>\n" + h + "\n</p>"
    # Clean up empty/nested block elements
    h = re.sub(r"<p>\s*</p>", "", h)
    h = re.sub(r"<p>\s*(<h[1-4]>)", r"\1", h)
    h = re.sub(r"(</h[1-4]>)\s*</p>", r"\1", h)
    h = re.sub(r"<p>\s*(<ul>)", r"\1", h)
    h = re.sub(r"(</ul>)\s*</p>", r"\1", h)
    h = re.sub(r"<p>\s*(<blockquote>)", r"\1", h)
    h = re.sub(r"(</blockquote>)\s*</p>", r"\1", h)
    h = re.sub(r"<p>\s*(<hr>)\s*</p>", r"\1", h)
    h = re.sub(r"<p>\s*(<hr>)", r"\1", h)
    return h


# ─── Frontmatter parser ──────────────────────────────────────────────────
def parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).split("\n"):
        colon = line.find(":")
        if colon == -1:
            continue
        key = line[:colon].strip()
        val = line[colon + 1:].strip()
        # Strip surrounding quotes
        if len(val) >= 2 and (
            (val[0] == '"' and val[-1] == '"') or
            (val[0] == "'" and val[-1] == "'")
        ):
            val = val[1:-1]
        meta[key] = val
    return meta, m.group(2)


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


def esc(s):
    return html_mod.escape(s or "", quote=True)


def iso_date(date_str):
    if not date_str:
        return ""
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return d.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except Exception:
        return date_str


# ─── Common HTML fragments ───────────────────────────────────────────────

# depth=1 means inside articles/ or people/ folder — CSS/JS paths go up one level
def page_head(title, description, canonical_url, og_type, og_image, depth=1):
    prefix = "../" if depth == 1 else ""
    return f"""<!doctype html>
<html class="no-js" lang="en">

    <head>
    <meta charset="utf-8">
    <meta name="google-site-verification" content="hiG_LERbmJeR4lCj2z4jsSumsaHhPI_wOjRFhT1E4Yw" />
    <title>{esc(title)}</title>
    <link rel="canonical" href="{esc(canonical_url)}">

    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">

    <link rel="manifest" href="{prefix}site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <meta name="format-detection" content="telephone=no">
    <link rel="apple-touch-icon" href="{prefix}icon.png">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <!-- Bootstrap core CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" rel="stylesheet">

    <link rel="stylesheet" href="{prefix}css/normalize.css">
    <link rel="stylesheet" href="{prefix}css/main.css">
    <meta name="description" content="{esc(description)}">
    <meta name="robots" content="index, follow">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta name="language" content="English">
    <meta name="author" content="The Mutapa Times">

<!-- Open Graph -->
<meta property="og:type" content="{esc(og_type)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1000">
<meta property="og:image:height" content="200">
<meta property="og:url" content="{esc(canonical_url)}">
<meta property="og:site_name" content="The Mutapa Times">
<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@mutapatimes">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">

    <link rel="apple-touch-icon" sizes="57x57" href="{prefix}img/apple-icon-57x57.png">
<link rel="apple-touch-icon" sizes="60x60" href="{prefix}img/apple-icon-60x60.png">
<link rel="apple-touch-icon" sizes="72x72" href="{prefix}img/apple-icon-72x72.png">
<link rel="apple-touch-icon" sizes="76x76" href="{prefix}img/apple-icon-76x76.png">
<link rel="apple-touch-icon" sizes="114x114" href="{prefix}img/apple-icon-114x114.png">
<link rel="apple-touch-icon" sizes="120x120" href="{prefix}img/apple-icon-120x120.png">
<link rel="apple-touch-icon" sizes="144x144" href="{prefix}img/apple-icon-144x144.png">
<link rel="apple-touch-icon" sizes="152x152" href="{prefix}img/apple-icon-152x152.png">
<link rel="apple-touch-icon" sizes="180x180" href="{prefix}img/apple-icon-180x180.png">
<link rel="icon" type="image/png" sizes="192x192"  href="{prefix}img/android-icon-192x192.png">
<link rel="icon" type="image/png" sizes="32x32" href="{prefix}img/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="96x96" href="{prefix}img/favicon-96x96.png">
<link rel="icon" type="image/png" sizes="16x16" href="{prefix}img/favicon-16x16.png">
<meta name="msapplication-TileColor" content="#ffffff">
<meta name="msapplication-TileImage" content="/ms-icon-144x144.png">
<meta name="theme-color" content="#1a1a1a">
<link rel="alternate" type="application/rss+xml" title="The Mutapa Times" href="https://www.mutapatimes.com/feed.xml">
<link rel="alternate" hreflang="en" href="{esc(canonical_url)}">
<link rel="alternate" hreflang="x-default" href="{esc(canonical_url)}">"""


def page_nav(active="articles", depth=1):
    prefix = "../" if depth == 1 else ""
    def cls(name):
        return ' class="active notranslate"' if name == active else ' class="notranslate"'
    eco_cls = ' class="economy-btn active"' if active == "economy" else ' class="economy-btn"'
    return f"""  </head>

  <body>
    <script src="{prefix}js/gate.js"></script>
   <div class="paper">
      <div class="aboutTitle">
        <div class="">&nbsp;</div>
        </div>
  <a href="{prefix}index.html" class="title-link">
    <div class="titleDiv">
      <h1 class="title notranslate">THE MUTAPA TIMES</h1>
    </div>
    <h4 class="sub notranslate">Zimbabwe outside-in.</h4>
  </a>
  <nav id="mainNav">
      <p>
          <a target="_self"{cls("news")} href="{prefix}index.html">News</a>
      </p>
      <p>
          <a target="_self"{eco_cls} href="{prefix}economy.html">Live Economy Data</a>
      </p>
      <p>
          <a target="_self"{cls("articles")} href="{prefix}articles.html">Articles</a>
      </p>
      <p>
          <a target="_self"{cls("people")} href="{prefix}people.html">People</a>
      </p>
      <p>
          <a target="_self"{cls("businesses")} href="{prefix}businesses.html">Businesses</a>
      </p>
  </nav>
  <hr class="topHr">
  <hr class="bottomHr">
  <div class="aboutTitle">
    <div class="date"></div>
    <div class="vol"></div>
    <div class="price"></div>
  </div>
  <hr class="dateHr">
"""


def page_footer(depth=1):
    prefix = "../" if depth == 1 else ""
    return f"""  <hr class="dateHr">

<!-- Back to top -->
<div class="back-to-top-wrap">
  <button class="back-to-top-btn" onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="Back to top">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
    Back to top
  </button>
</div>

<!-- Subscribe banner -->
<div class="footer-subscribe">
  <div class="footer-subscribe-inner">
    <h4 class="footer-subscribe-title">Stay informed on Zimbabwe</h4>
    <p class="footer-subscribe-copy">Curated news, market data &amp; analysis delivered 3&times; a week.</p>
    <form class="footer-subscribe-form" method="POST" action="https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg==" target="brevo-footer-frame">
      <input type="email" class="footer-subscribe-input" name="EMAIL" placeholder="you@example.com" required autocomplete="email" aria-label="Email address">
      <button type="submit" class="footer-subscribe-btn">Subscribe Free</button>
    </form>
    <p class="footer-subscribe-fine">Free forever. Unsubscribe anytime.</p>
    <iframe name="brevo-footer-frame" style="display:none" aria-hidden="true"></iframe>
  </div>
</div>

<!-- Site footer -->
<footer class="site-footer">
    <div class="container" style="padding:25px 15px 15px;">
      <div class="row">
        <div class="col-sm-12 col-md-5">
            <h4 class="storyTitleCat">About</h4>
            <p class="storyfooter">The Mutapa Times is a business and intelligence newspaper that aggregates Zimbabwean news from foreign press to deliver curated coverage for the diaspora &amp; native residents.
                Powered by <a href="https://gnews.io/" target="_blank">GNews</a> &amp; <a href="https://open-meteo.com/" target="_blank">Open-Meteo</a>.</p>
          </div>

          <div class="col-sm-6 col-md-3">
            <h4 class="storyTitleCat">Sections</h4>
            <ul class="footer-links">
              <li><a href="{prefix}index.html">News</a></li>
              <li><a href="{prefix}economy.html">Live Economy Data</a></li>
              <li><a href="{prefix}articles.html">Articles</a></li>
              <li><a href="{prefix}people.html">People</a></li>
              <li><a href="{prefix}businesses.html">Businesses</a></li>
            </ul>
          </div>

          <div class="col-sm-6 col-md-2">
            <h4 class="storyTitleCat">Contact</h4>
            <ul class="footer-links">
              <li><a target="_blank" href="https://twitter.com/mutapatimes">Twitter</a></li>
              <li><a href="mailto:news@mutapatimes.com">Email</a></li>
              <li><a href="{prefix}terms.html">Terms &amp; Conditions</a></li>
            </ul>
          </div>
      </div>
      <hr>
      <div class="row">
        <div class="col-md-9 col-sm-8 col-xs-6">
          <p class="copyright-text notranslate">Copyright &copy; 2020&ndash;2026 All Rights Reserved by
       <a href="#">The Mutapa Times</a>.
          </p>
        </div>
        <div class="col-md-3 col-sm-4 col-xs-6">
          <p class="copyright-text">Developed by
             <a target="_blank" href="http://www.eluwasi.com">@eluwasi</a>.
          </p>
        </div>
      </div>
    </div>
</footer>
</div>

  <script defer src="{prefix}js/vendor/modernizr-3.8.0.min.js"></script>

<script>
if ('serviceWorker' in navigator) {{
  window.addEventListener('load', function() {{
    navigator.serviceWorker.register('/sw.js');
  }});
}}
</script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XQPRFK7JTB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-XQPRFK7JTB');
</script>

<!-- Contentsquare / Hotjar -->
<script src="https://t.contentsquare.net/uxa/c5a71947dd29b.js"></script>
</body>

</html>
"""


# ─── Share buttons (mirrors JS articleShareButtons / person shareButtons) ─
def article_share_buttons(title, canonical_url):
    url_enc = quote(canonical_url + "?utm_source=mutapatimes&utm_medium=article_share&utm_campaign=reader_share", safe="")
    text_enc = quote(f"{title} \u2014 The Mutapa Times \U0001f1ff\U0001f1fc", safe="")
    wa_text = quote(f"{title}\n\n{canonical_url}?utm_source=mutapatimes&utm_medium=whatsapp&utm_campaign=reader_share\n\nvia The Mutapa Times \u2014 Zimbabwe news from 100+ sources \U0001f1ff\U0001f1fc", safe="")
    return f"""<div class="article-share">
<span class="article-share-label">Share this article</span>
<div class="share-group">
<a href="https://api.whatsapp.com/send?text={wa_text}" target="_blank" rel="noopener" class="whatsapp-btn" title="Share on WhatsApp">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="currentColor"/></svg>
</a>
<a href="https://twitter.com/intent/tweet?url={url_enc}&text={text_enc}&via=mutapatimes" target="_blank" rel="noopener" class="share-btn" title="Share on X">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="currentColor"/></svg>
</a>
<a href="https://www.facebook.com/sharer/sharer.php?u={url_enc}" target="_blank" rel="noopener" class="share-btn" title="Share on Facebook">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="currentColor"/></svg>
</a>
<a href="https://www.linkedin.com/sharing/share-offsite/?url={url_enc}" target="_blank" rel="noopener" class="share-btn" title="Share on LinkedIn">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="currentColor"/></svg>
</a>
</div></div>"""


def person_share_buttons(name, canonical_url):
    url_enc = quote(canonical_url, safe="")
    text_enc = quote(f"{name} - Profile on The Mutapa Times", safe="")
    return f"""<div class="person-profile-share">
<span class="person-profile-share-label">Share</span>
<div class="share-group">
<a href="https://twitter.com/intent/tweet?url={url_enc}&text={text_enc}&via=mutapatimes" target="_blank" rel="noopener" class="share-btn" title="Share on X">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="currentColor"/></svg>
</a>
<a href="https://www.facebook.com/sharer/sharer.php?u={url_enc}" target="_blank" rel="noopener" class="share-btn" title="Share on Facebook">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="currentColor"/></svg>
</a>
<a href="https://www.linkedin.com/sharing/share-offsite/?url={url_enc}" target="_blank" rel="noopener" class="share-btn" title="Share on LinkedIn">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="currentColor"/></svg>
</a>
<a href="https://api.whatsapp.com/send?text={text_enc}%20{url_enc}" target="_blank" rel="noopener" class="whatsapp-btn" title="Share on WhatsApp">
<svg viewBox="0 0 24 24" width="14" height="14"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="currentColor"/></svg>
</a>
</div></div>"""


# ─── Build article pages ─────────────────────────────────────────────────
def build_articles():
    os.makedirs(ARTICLES_OUT, exist_ok=True)
    md_files = sorted(glob.glob(os.path.join(ARTICLES_SRC, "*.md")))
    count = 0

    for md_path in md_files:
        slug = os.path.splitext(os.path.basename(md_path))[0]
        if slug == "index":
            continue

        with open(md_path, "r", encoding="utf-8") as f:
            raw = f.read()

        meta, body = parse_frontmatter(raw)
        title = meta.get("title", "Untitled")
        page_title = f"{title} | The Mutapa Times"
        date_str = meta.get("date", "")
        author = meta.get("author", "")
        category = meta.get("category", "")
        image = meta.get("image", "")
        summary = meta.get("summary", "")
        source_url = meta.get("source_url", "")
        canonical = f"{BASE_URL}/articles/{slug}.html"
        og_image = image if image else f"{BASE_URL}/img/banner.png"

        date_display = format_date(date_str)
        body_html = markdown_to_html(body)

        # Schema.org NewsArticle JSON-LD
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": title,
            "description": summary,
            "url": canonical,
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
            "publisher": {
                "@type": "Organization",
                "name": "The Mutapa Times",
                "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/img/logo.png"}
            },
            "inLanguage": "en"
        }
        if image:
            schema["image"] = {"@type": "ImageObject", "url": image}
        if author:
            schema["author"] = {"@type": "Person", "name": author}
        if date_str:
            iso = iso_date(date_str)
            if iso:
                schema["datePublished"] = iso
                schema["dateModified"] = iso
        if category:
            schema["articleSection"] = category

        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Articles", "item": f"{BASE_URL}/articles.html"},
                {"@type": "ListItem", "position": 3, "name": title, "item": canonical}
            ]
        }

        # Build page
        html_parts = []
        html_parts.append(page_head(page_title, summary, canonical, "article", og_image, depth=1))
        html_parts.append(f"""
<script type="application/ld+json">
{json.dumps(schema)}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb)}
</script>""")
        html_parts.append(page_nav("articles", depth=1))
        html_parts.append("""
  <!-- Single article view -->
  <main>
    <article class="article-full">""")

        # Breadcrumb nav
        html_parts.append(f"""
      <nav class="article-breadcrumb" aria-label="Breadcrumb">
        <a href="../index.html">Home</a> <span aria-hidden="true">/</span>
        <a href="../articles.html">Articles</a> <span aria-hidden="true">/</span>
        <span>{esc(title)}</span>
      </nav>""")

        # Article header
        html_parts.append(f"""
      <div class="article-header">""")
        if category:
            html_parts.append(f'        <span class="article-category-tag">{esc(category)}</span>')
        html_parts.append(f'        <h1 class="article-title">{esc(title)}</h1>')
        html_parts.append(f'        <div class="article-meta">')
        if author:
            html_parts.append(f'          <span class="article-author">By {esc(author)}</span>')
        if date_display:
            html_parts.append(f'          <time class="article-date" datetime="{esc(date_str)}">{date_display}</time>')
        html_parts.append(f'        </div>')
        html_parts.append(f'      </div>')

        # Hero image
        if image:
            html_parts.append(f'      <img src="{esc(image)}" alt="{esc(title)}" class="article-hero-img">')

        # Article body
        html_parts.append(f'      <div class="article-body">{body_html}</div>')

        # Share buttons
        html_parts.append(f"      {article_share_buttons(title, canonical)}")

        # Back link
        html_parts.append(f'      <div class="article-back"><a href="../articles.html">&larr; All articles</a></div>')

        html_parts.append("""
    </article>
  </main>
""")
        html_parts.append(page_footer(depth=1))

        # Write file
        out_path = os.path.join(ARTICLES_OUT, f"{slug}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
        count += 1

    print(f"Built {count} static article pages in articles/")
    return count


# ─── Build people pages ──────────────────────────────────────────────────
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

SPARQL_QUERY = """SELECT ?person ?personLabel ?personDescription ?image ?occupationLabel ?birthDate ?article WHERE {
  ?person wdt:P31 wd:Q5.
  ?person wdt:P27 wd:Q954.
  ?person wdt:P106 ?occupation.
  VALUES ?occType { wd:Q43845 wd:Q131524 wd:Q484876 wd:Q806798 }
  ?occupation wdt:P279* ?occType.
  OPTIONAL { ?person wdt:P18 ?image. }
  OPTIONAL { ?person wdt:P569 ?birthDate. }
  OPTIONAL { ?article schema:about ?person. ?article schema:isPartOf <https://en.wikipedia.org/>. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}"""


def fetch_json(url, headers=None, timeout=20):
    req = Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  Warning: fetch failed for {url[:80]}... ({e})")
        return None


def fetch_wikidata_people():
    url = f"{WIKIDATA_ENDPOINT}?query={quote(SPARQL_QUERY)}&format=json"
    data = fetch_json(url, headers={"Accept": "application/sparql-results+json"}, timeout=30)
    if not data or "results" not in data:
        return []
    bindings = data["results"]["bindings"]
    people_map = {}
    for b in bindings:
        uri = b["person"]["value"]
        qid = uri.split("/")[-1]
        label = b.get("personLabel", {}).get("value", "")
        if not label or label == qid:
            continue
        if qid not in people_map:
            wp_url = b.get("article", {}).get("value", "")
            wp_title = wp_url.split("/wiki/")[-1] if "/wiki/" in wp_url else ""
            people_map[qid] = {
                "id": qid,
                "name": label,
                "description": b.get("personDescription", {}).get("value", ""),
                "image": b.get("image", {}).get("value", ""),
                "occupation": b.get("occupationLabel", {}).get("value", ""),
                "birthDate": b.get("birthDate", {}).get("value", ""),
                "wikidataUrl": uri,
                "wikipediaTitle": wp_title,
                "wikipediaUrl": wp_url,
                "bio": ""
            }
        else:
            occ = b.get("occupationLabel", {}).get("value", "")
            if occ and occ not in people_map[qid]["occupation"]:
                people_map[qid]["occupation"] += ", " + occ
    result = sorted(people_map.values(), key=lambda p: p["name"])
    return result


def fetch_wikipedia_bio(title):
    if not title:
        return ""
    url = WIKIPEDIA_API + quote(title)
    data = fetch_json(url, timeout=10)
    if data and "extract" in data:
        return data["extract"]
    return ""


def build_people():
    os.makedirs(PEOPLE_OUT, exist_ok=True)

    print("Fetching Wikidata SPARQL for Zimbabwean business people...")
    people = fetch_wikidata_people()
    if not people:
        print("  No people fetched (network unavailable or query failed). Skipping people pages.")
        return 0

    print(f"  Found {len(people)} people. Generating pages...")
    count = 0

    for person in people:
        qid = person["id"]
        name = person["name"]
        occ = person["occupation"]
        description = person["description"]
        image = person["image"]
        birth_date = person["birthDate"]
        wp_url = person["wikipediaUrl"]
        wd_url = person["wikidataUrl"]
        wp_title = person["wikipediaTitle"]
        canonical = f"{BASE_URL}/people/{qid}.html"
        og_image = image if image else f"{BASE_URL}/img/banner.png"

        # Title and description
        title_parts = [name]
        if occ:
            title_parts.append(occ.split(",")[0].strip())
        page_title = " - ".join(title_parts) + " | The Mutapa Times"

        desc = name
        if occ:
            desc += f" is a {occ}"
        if description:
            desc += f". {description}"
        if len(desc) > 160:
            desc = desc[:157] + "..."

        # Fetch Wikipedia bio
        bio = fetch_wikipedia_bio(wp_title) if wp_title else description

        # Birth date
        birth_display = format_date(birth_date) if birth_date else ""

        # Schema.org Person JSON-LD
        schema = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": name,
            "url": canonical,
            "description": description
        }
        if image:
            schema["image"] = image
        if occ:
            schema["jobTitle"] = occ.split(",")[0].strip()
        if birth_date:
            try:
                bd = datetime.fromisoformat(birth_date.replace("Z", "+00:00"))
                schema["birthDate"] = bd.strftime("%Y-%m-%d")
            except Exception:
                pass
        same_as = []
        if wp_url:
            same_as.append(wp_url)
        if wd_url:
            same_as.append(wd_url)
        if same_as:
            schema["sameAs"] = same_as

        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "People", "item": f"{BASE_URL}/people.html"},
                {"@type": "ListItem", "position": 3, "name": name, "item": canonical}
            ]
        }

        # Build page
        html_parts = []
        html_parts.append(page_head(page_title, desc, canonical, "profile", og_image, depth=1))
        html_parts.append(f"""
<script type="application/ld+json">
{json.dumps(schema)}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb)}
</script>""")
        html_parts.append(page_nav("people", depth=1))
        html_parts.append("""
  <!-- Single person profile -->
  <main>
    <div class="person-profile">""")

        # Breadcrumb
        html_parts.append(f"""
      <nav class="person-profile-breadcrumb" aria-label="Breadcrumb">
        <a href="../index.html">Home</a> <span aria-hidden="true">/</span>
        <a href="../people.html">People</a> <span aria-hidden="true">/</span>
        <span>{esc(name)}</span>
      </nav>""")

        # Profile header
        html_parts.append('      <div class="person-profile-header">')
        if image:
            html_parts.append(f'        <div class="person-profile-img-wrap"><img src="{esc(image)}" alt="{esc(name)}, {esc(occ)}" class="person-profile-img"></div>')
        html_parts.append(f'        <div class="person-profile-info">')
        html_parts.append(f'          <h1 class="person-profile-name">{esc(name)}</h1>')
        html_parts.append(f'          <p class="person-profile-role">{esc(occ)}</p>')
        if birth_display:
            html_parts.append(f'          <p class="person-profile-birth"><strong>Born:</strong> <time>{birth_display}</time></p>')
        # External links
        links = ""
        if wp_url:
            links += f'<a href="{esc(wp_url)}" target="_blank" rel="noopener" class="person-profile-extlink">Wikipedia</a>'
        if wd_url:
            links += f'{" " if links else ""}<a href="{esc(wd_url)}" target="_blank" rel="noopener" class="person-profile-extlink">Wikidata</a>'
        if links:
            html_parts.append(f'          <div class="person-profile-extlinks">{links}</div>')
        html_parts.append(f"          {person_share_buttons(name, canonical)}")
        html_parts.append('        </div>')
        html_parts.append('      </div>')

        # Bio
        if bio:
            html_parts.append(f'      <div class="person-profile-bio"><p>{esc(bio)}</p></div>')
        elif description:
            html_parts.append(f'      <div class="person-profile-bio"><p>{esc(description)}</p></div>')

        # Back link
        html_parts.append('      <div class="person-profile-back"><a href="../people.html">&larr; All people</a></div>')

        html_parts.append("""
    </div>
  </main>
""")
        html_parts.append(page_footer(depth=1))

        out_path = os.path.join(PEOPLE_OUT, f"{qid}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_parts))
        count += 1

    print(f"Built {count} static people pages in people/")
    return count


# ─── Main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== The Mutapa Times: Static Page Builder ===\n")
    article_count = build_articles()
    people_count = build_people()
    print(f"\nDone. {article_count} articles + {people_count} people pages generated.")
