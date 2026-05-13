#!/usr/bin/env python3
"""
Generate per-article landing pages on mutapatimes.com for every news headline
in data/*.json. Each page shows the headline, summary, source attribution, a
"Continue at source" CTA, plus the standard Mutapa Times header/footer.

This converts mutapatimes.com from a passive headlines feed into a destination
that ranks for the headline text and captures readers from social posts before
they leave for the source. Run after scripts/fetch_news.py.
"""
import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

# Reuse page chrome from the existing static pages builder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_static_pages import (  # noqa: E402
    BASE_URL, esc, format_date, iso_date,
    page_head, page_nav, page_footer,
)
# Brand headline-card URL — Metricool, X, Facebook etc. fetch og:image
# from the landing page, NOT the RSS enclosure. To make every social
# preview show the on-brand card (not the scraped source thumbnail),
# we emit the brand card as og:image instead of the article's hero photo.
from build_feed_cards import card_public_url as feed_card_url  # noqa: E402

DATA_DIR = "data"
NEWS_OUT = "news"
SPOTLIGHT_FILE = os.path.join(DATA_DIR, "spotlight.json")
CATEGORY_FILES = ["business", "technology", "entertainment", "sports", "science", "health"]


# ── Slug generation (must match build_metricool_csv.py for URL stability) ──
def make_slug(article):
    """Build a stable slug like 2026-05-08-headline-text-abc123."""
    title = (article.get("title") or "").strip()
    url = (article.get("url") or "").strip()
    published = article.get("publishedAt") or ""

    # Date prefix: prefer publishedAt; fallback to today
    date_part = ""
    if published:
        m = re.match(r"(\d{4}-\d{2}-\d{2})", published)
        if m:
            date_part = m.group(1)
    if not date_part:
        date_part = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Slugify title
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > 60:
        s = s[:60].rstrip("-")
    if not s:
        s = "news"

    # Hash suffix from URL → guaranteed uniqueness across re-fetches
    h = hashlib.md5(url.encode("utf-8")).hexdigest()[:6]
    return f"{date_part}-{s}-{h}"


def landing_url(article):
    return f"{BASE_URL}/news/{make_slug(article)}"


# ── Article loading ────────────────────────────────────────────
# Don't render a landing page for articles older than this. Stops Google
# News RSS resurfaces (e.g., a 2019 story reappearing in the tech feed)
# from getting a fresh-looking /news/{slug}.html.
MAX_ARTICLE_AGE_DAYS = 30


def normalize_source(src):
    if isinstance(src, dict):
        return (src.get("name") or "").strip()
    return str(src or "").strip()


def _parse_pub_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        pass
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def _is_fresh_enough(article):
    dt = _parse_pub_date(article.get("publishedAt") or "")
    if not dt:
        return True
    try:
        return (datetime.now(timezone.utc) - dt).days <= MAX_ARTICLE_AGE_DAYS
    except (TypeError, ValueError):
        return True


def load_articles():
    """Read spotlight + category JSONs into a flat list, deduped by URL."""
    seen = set()
    out = []
    stale = 0

    def take(filepath, label):
        nonlocal stale
        if not os.path.isfile(filepath):
            return
        try:
            data = json.load(open(filepath))
        except (json.JSONDecodeError, IOError):
            return
        for a in data.get("articles", []):
            url = (a.get("url") or "").strip()
            if not url or url in seen:
                continue
            if not _is_fresh_enough(a):
                stale += 1
                continue
            seen.add(url)
            out.append({
                "title": (a.get("title") or "").strip(),
                "description": (a.get("description") or "").strip(),
                "url": url,
                "image": (a.get("image") or "").strip(),
                "source": normalize_source(a.get("source")),
                "category": label,
                "publishedAt": a.get("publishedAt") or "",
            })

    take(SPOTLIGHT_FILE, "spotlight")
    for cat in CATEGORY_FILES:
        take(os.path.join(DATA_DIR, f"{cat}.json"), cat)
    if stale:
        print(f"  Dropped {stale} stale articles (>{MAX_ARTICLE_AGE_DAYS}d old)")
    return out


# ── Page rendering ─────────────────────────────────────────────
def render_page(article, related=None):
    title = article["title"]
    summary = article["description"] or f"{title} — full story at {article['source']}."
    canonical = landing_url(article)
    # og:image + Schema.org image point at the brand headline card so social
    # previews are uniformly on-brand. The in-body hero <img> below still
    # uses article["image"] (the scraped source photo) so readers see real
    # editorial imagery on the page itself.
    image = feed_card_url(canonical)
    pub_iso = iso_date(article.get("publishedAt", "")) or datetime.now(timezone.utc).isoformat()
    pub_human = format_date(article.get("publishedAt", "")) or ""
    source = article["source"] or "Source"
    category = article["category"]

    # Truncate description for meta tags
    meta_desc = re.sub(r"\s+", " ", summary)[:200]

    page_title = f"{title} | The Mutapa Times"

    # JSON-LD structured data — proper NewsArticle markup so search engines
    # treat the landing page as the canonical reference for the headline.
    # Google News surfaces require dateModified; articleSection drives the
    # "Topics" listing on news.google.com; keywords help long-tail discovery.
    section_label = (category or "news").title()
    keywords = [w for w in [
        "Zimbabwe",
        section_label,
        source,
    ] if w]
    structured = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "image": [image],
        "datePublished": pub_iso,
        "dateModified": datetime.now(timezone.utc).isoformat(),
        "articleSection": section_label,
        "keywords": ", ".join(keywords),
        "author": {"@type": "Organization", "name": source},
        "publisher": {
            "@type": "Organization",
            "name": "The Mutapa Times",
            "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/img/logo.png"},
        },
        "description": meta_desc,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "News", "item": f"{BASE_URL}/articles"},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
        ],
    }

    # page_head() returns <!doctype html><html>...<head>... (head left open)
    # page_nav() closes head, opens body, prints the masthead+nav
    # page_footer() prints the subscribe banner + footer + </body></html>
    parts = []
    parts.append(page_head(page_title, meta_desc, canonical, "article", image, depth=1))
    parts.append(f'<script type="application/ld+json">{json.dumps(structured)}</script>')
    parts.append(f'<script type="application/ld+json">{json.dumps(breadcrumb)}</script>')
    parts.append(page_nav(active="articles", depth=1))
    # Stories rail — same IG-style highlight strip used on home + /articles.
    parts.append('<div id="stories-rail" aria-label="Story highlights"></div>')

    # Main story body
    parts.append('<main class="news-landing">')
    parts.append('  <div class="news-meta">')
    parts.append(f'    <span class="news-category">{esc(category.upper())}</span>')
    if pub_human:
        parts.append(f'    <time class="news-date" datetime="{esc(pub_iso)}">{esc(pub_human)}</time>')
    parts.append("  </div>")
    parts.append(f'  <h1 class="news-headline">{esc(title)}</h1>')
    parts.append(f'  <p class="news-source-line">VIA <strong>{esc(source.upper())}</strong></p>')
    if article["image"]:
        parts.append(f'  <img class="news-hero" src="{esc(article["image"])}" alt="{esc(title)}" loading="eager">')

    if article["description"]:
        parts.append(f'  <p class="news-summary">{esc(article["description"])}</p>')

    parts.append('  <div class="news-cta-wrap">')
    parts.append(
        f'    <a class="news-cta-btn" href="{esc(article["url"])}" '
        f'target="_blank" rel="noopener" '
        f'data-source="{esc(source)}">'
        f'Continue reading at {esc(source)} <span aria-hidden="true">→</span>'
        f'</a>'
    )
    parts.append(
        '    <p class="news-cta-secondary">'
        'Get the next story first &mdash; '
        '<a class="follow-x-cta" href="https://twitter.com/intent/follow?screen_name=mutapatimes" '
        'target="_blank" rel="noopener">Follow @mutapatimes on X</a>'
        '</p>'
    )
    parts.append("  </div>")

    # Related stories — internal links boost PageRank for long-tail SEO.
    if related:
        parts.append('  <section class="news-related">')
        parts.append('    <h3 class="news-related-title">More from this category</h3>')
        parts.append('    <ul class="news-related-list">')
        for r in related[:3]:
            r_url = landing_url(r)
            parts.append(
                f'      <li><a href="{esc(r_url)}">{esc(r["title"])}</a> '
                f'<span class="news-related-source">&middot; {esc(r.get("source",""))}</span></li>'
            )
        parts.append('    </ul>')
        parts.append('  </section>')

    parts.append('  <p class="news-disclaimer">')
    parts.append(
        f'    The Mutapa Times aggregates Zimbabwean news from foreign press. '
        f'The full article above lives at <a href="{esc(article["url"])}" target="_blank" rel="noopener">{esc(source)}</a>; '
        f'we link out to credit the original publisher.'
    )
    parts.append("  </p>")

    parts.append("</main>")

    parts.append(page_footer(depth=1))

    return "\n".join(parts)


# ── IndexNow (Bing/Yandex) — optional, env-controlled ────────
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")
INDEXNOW_HOST = "www.mutapatimes.com"


def indexnow_ping(urls):
    """POST a batch of URLs to IndexNow so Bing/Yandex can crawl
    immediately. No-op if INDEXNOW_KEY env var isn't set."""
    if not INDEXNOW_KEY or not urls:
        return
    payload = {
        "host": INDEXNOW_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{INDEXNOW_HOST}/{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.indexnow.org/indexnow",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"  IndexNow ping ({len(urls)} URLs): HTTP {resp.status}")
    except Exception as e:
        print(f"  IndexNow ping failed: {e}")


def pick_related(article, all_articles, max_count=3):
    """Find up to N other articles in the same category, most recent first.
    Falls back to any other article if the category doesn't have enough."""
    same_cat = [
        a for a in all_articles
        if a.get("category") == article.get("category")
        and a["url"] != article["url"]
    ]
    same_cat.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    if len(same_cat) >= max_count:
        return same_cat[:max_count]
    seen = {a["url"] for a in same_cat} | {article["url"]}
    fallbacks = [a for a in all_articles if a["url"] not in seen]
    fallbacks.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return (same_cat + fallbacks)[:max_count]


# ── Main ───────────────────────────────────────────────────────
def main():
    print("=== BUILD NEWS LANDING PAGES ===")
    # --force rebuilds existing pages — useful when og:image / chrome /
    # JSON-LD shape changes and every page needs to refresh. Default is
    # skip-existing so the routine fetch-news cron stays cheap.
    force = "--force" in sys.argv
    articles = load_articles()
    print(f"  {len(articles)} unique articles loaded (force={force})")

    os.makedirs(NEWS_OUT, exist_ok=True)
    written = skipped = 0
    new_urls = []
    for art in articles:
        slug = make_slug(art)
        out_path = os.path.join(NEWS_OUT, f"{slug}.html")
        if not force and os.path.exists(out_path):
            skipped += 1
            continue
        try:
            related = pick_related(art, articles)
            page_html = render_page(art, related=related)
        except Exception as e:
            print(f"  ERROR rendering {slug}: {e}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        written += 1
        new_urls.append(landing_url(art))

    print(f"  Wrote {written} pages, skipped {skipped} existing")

    # Notify Bing/Yandex of fresh URLs (no-op without INDEXNOW_KEY)
    if new_urls:
        indexnow_ping(new_urls[:100])  # IndexNow caps at 10000 but be polite

    print("=== DONE ===")


if __name__ == "__main__":
    main()
