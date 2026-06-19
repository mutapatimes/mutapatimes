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
from datetime import datetime, timezone, timedelta

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
try:
    from regions import get_region as _get_region  # noqa: E402
except ImportError:
    _get_region = None

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

    # Slugify title. Cap at 80 chars and cut on word boundary so we
    # don't ship slugs like "...project-stu" (truncated "studio") — the
    # mid-word break reads as spam and gets carried into the sitemap
    # news:title by generate_sitemap.py.
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    MAX_SLUG_LEN = 80
    if len(s) > MAX_SLUG_LEN:
        cut = s.rfind("-", 0, MAX_SLUG_LEN)
        s = s[:cut] if cut > 30 else s[:MAX_SLUG_LEN]
        s = s.rstrip("-")
    if not s:
        s = "news"

    # Hash suffix from URL → guaranteed uniqueness across re-fetches
    h = hashlib.md5(url.encode("utf-8")).hexdigest()[:6]
    return f"{date_part}-{s}-{h}"


def landing_url(article, pfx=""):
    return f"{BASE_URL}{pfx}/news/{make_slug(article)}"


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


def load_articles(region="zw"):
    """Read spotlight + category JSONs into a flat list, deduped by URL."""
    data_dir = DATA_DIR if region == "zw" else os.path.join(DATA_DIR, region)
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

    take(os.path.join(data_dir, "spotlight.json"), "spotlight")
    for cat in CATEGORY_FILES:
        take(os.path.join(data_dir, f"{cat}.json"), cat)
    if stale:
        print(f"  Dropped {stale} stale articles (>{MAX_ARTICLE_AGE_DAYS}d old)")
    return out


# ── Image-rights-safe hero ─────────────────────────────────────
# Never hotlink a major international agency/outlet photo as the news hero
# (PicRights et al. enforce AFP / Reuters / AP / Getty). Swap risky hosts for
# our own deterministic gradient artwork. Local/Zim outlet images pass through.
def news_safe_hero(image_url, canonical):
    try:
        from build_feed_cards import is_rights_risky
    except Exception:
        return image_url
    if not image_url or not is_rights_risky(image_url):
        return image_url
    slug = (canonical or "").rstrip("/").split("/")[-1]
    if slug.endswith(".html"):
        slug = slug[:-5]
    rel = f"img/news/auto/{slug}.jpg"
    try:
        os.makedirs(os.path.dirname(rel), exist_ok=True)
        if not os.path.exists(rel):
            from gradient_hero import make_gradient_hero
            make_gradient_hero(slug, rel)
    except Exception as e:  # better no hero than a hotlinked agency photo
        print(f"  news gradient hero failed for {slug}: {e}")
        return ""
    return f"/{rel}" if os.path.exists(rel) else ""


# ── Page rendering ─────────────────────────────────────────────
def render_page(article, related=None, region="zw", pfx="", depth=1):
    _meta = _get_region(region) if _get_region else {}
    country = _meta.get("name", "Zimbabwe")
    demonym_adj = _meta.get("demonym", "Zimbabwean")
    title = article["title"]
    summary = article["description"] or f"{title} — full story at {article['source']}."
    canonical = landing_url(article, pfx)
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
        country,
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
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}{pfx}/"},
            {"@type": "ListItem", "position": 2, "name": "News", "item": f"{BASE_URL}{pfx}/articles"},
            {"@type": "ListItem", "position": 3, "name": title, "item": canonical},
        ],
    }

    # page_head() returns <!doctype html><html>...<head>... (head left open)
    # page_nav() closes head, opens body, prints the masthead+nav
    # page_footer() prints the subscribe banner + footer + </body></html>
    parts = []
    # Pre-launch editions (e.g. /za before sign-off) carry noindex.
    robots_val = "index, follow" if _meta.get("indexable", True) else "noindex, follow"
    parts.append(page_head(page_title, meta_desc, canonical, "article", image, depth=depth, robots=robots_val, pfx=pfx))
    parts.append(f'<script type="application/ld+json">{json.dumps(structured)}</script>')
    parts.append(f'<script type="application/ld+json">{json.dumps(breadcrumb)}</script>')
    parts.append(page_nav(active="articles", depth=depth, pfx=pfx, region=region))
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
    _hero = news_safe_hero(article["image"], canonical)
    if _hero:
        parts.append(f'  <img class="news-hero" src="{esc(_hero)}" alt="{esc(title)}" loading="eager">')

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
            r_url = landing_url(r, pfx)
            parts.append(
                f'      <li><a href="{esc(r_url)}">{esc(r["title"])}</a> '
                f'<span class="news-related-source">&middot; {esc(r.get("source",""))}</span></li>'
            )
        parts.append('    </ul>')
        parts.append('  </section>')

    parts.append('  <p class="news-disclaimer">')
    parts.append(
        f'    The Mutapa Times aggregates {demonym_adj} news from foreign press. '
        f'The full article above lives at <a href="{esc(article["url"])}" target="_blank" rel="noopener">{esc(source)}</a>; '
        f'we link out to credit the original publisher.'
    )
    parts.append("  </p>")

    parts.append("</main>")

    parts.append(page_footer(depth=depth, pfx=pfx, region=region))

    return "\n".join(parts)


# ── IndexNow (Bing/Yandex) — optional, env-controlled ────────
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")
INDEXNOW_HOST = "mutapatimes.com"


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
    import argparse
    ap = argparse.ArgumentParser()
    # --force rebuilds existing pages — useful when og:image / chrome /
    # JSON-LD shape changes and every page needs to refresh. Default is
    # skip-existing so the routine fetch-news cron stays cheap.
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--region", default="zw",
                    help="Region edition to build (default: zw = Zimbabwe at the root)")
    args = ap.parse_args()
    region = args.region
    pfx = "" if region == "zw" else f"/{region}"
    depth = 1 if region == "zw" else 2
    out_dir = NEWS_OUT if region == "zw" else os.path.join(region, NEWS_OUT)
    force = args.force
    print("=== BUILD NEWS LANDING PAGES ===")
    articles = load_articles(region)
    print(f"  {len(articles)} unique articles loaded (force={force})")

    os.makedirs(out_dir, exist_ok=True)
    written = skipped = 0
    new_urls = []
    for art in articles:
        slug = make_slug(art)
        out_path = os.path.join(out_dir, f"{slug}.html")
        if not force and os.path.exists(out_path):
            skipped += 1
            continue
        try:
            related = pick_related(art, articles)
            page_html = render_page(art, related=related, region=region, pfx=pfx, depth=depth)
        except Exception as e:
            print(f"  ERROR rendering {slug}: {e}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        written += 1
        new_urls.append(landing_url(art, pfx))

    print(f"  Wrote {written} pages, skipped {skipped} existing")

    # Soft noindex sweep: /news/ are aggregated wire pages. Keep fresh ones
    # (<=30d) indexed for the Discover/News window, then noindex the stale
    # commodity pages so the quality signal concentrates on original work.
    # Runs every build, so pages self-heal into noindex as they age.
    import glob as _glob
    cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_ARTICLE_AGE_DAYS)).date()
    swept = 0
    for f in _glob.glob(os.path.join(out_dir, "*.html")):
        m = re.search(r"/(\d{4})-(\d{2})-(\d{2})-", f)
        if not m:
            continue
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc).date()
        if d >= cutoff:
            continue
        try:
            s = open(f, encoding="utf-8").read()
        except OSError:
            continue
        if '<meta name="robots" content="index, follow">' in s:
            open(f, "w", encoding="utf-8").write(
                s.replace('<meta name="robots" content="index, follow">',
                          '<meta name="robots" content="noindex, follow">', 1))
            swept += 1
    if swept:
        print(f"  Noindexed {swept} stale (>{MAX_ARTICLE_AGE_DAYS}d) news pages")

    # Notify Bing/Yandex of fresh URLs (no-op without INDEXNOW_KEY)
    if new_urls:
        indexnow_ping(new_urls[:100])  # IndexNow caps at 10000 but be polite

    print("=== DONE ===")


if __name__ == "__main__":
    main()
