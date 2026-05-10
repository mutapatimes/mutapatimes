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
    return f"{BASE_URL}/news/{make_slug(article)}.html"


# ── Article loading ────────────────────────────────────────────
def normalize_source(src):
    if isinstance(src, dict):
        return (src.get("name") or "").strip()
    return str(src or "").strip()


def load_articles():
    """Read spotlight + category JSONs into a flat list, deduped by URL."""
    seen = set()
    out = []

    def take(filepath, label):
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
    return out


# ── Page rendering ─────────────────────────────────────────────
def render_page(article):
    title = article["title"]
    summary = article["description"] or f"{title} — full story at {article['source']}."
    image = article["image"] or f"{BASE_URL}/img/banner.png"
    canonical = landing_url(article)
    pub_iso = iso_date(article.get("publishedAt", "")) or datetime.now(timezone.utc).isoformat()
    pub_human = format_date(article.get("publishedAt", "")) or ""
    source = article["source"] or "Source"
    category = article["category"]

    # Truncate description for meta tags
    meta_desc = re.sub(r"\s+", " ", summary)[:200]

    page_title = f"{title} | The Mutapa Times"

    # JSON-LD structured data — proper NewsArticle markup so search engines
    # treat the landing page as the canonical reference for the headline.
    structured = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title,
        "image": [image],
        "datePublished": pub_iso,
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
            {"@type": "ListItem", "position": 2, "name": "News", "item": f"{BASE_URL}/articles.html"},
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
    parts.append("  </div>")
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


# ── Main ───────────────────────────────────────────────────────
def main():
    print("=== BUILD NEWS LANDING PAGES ===")
    articles = load_articles()
    print(f"  {len(articles)} unique articles loaded")

    os.makedirs(NEWS_OUT, exist_ok=True)
    written = skipped = 0
    for art in articles:
        slug = make_slug(art)
        out_path = os.path.join(NEWS_OUT, f"{slug}.html")
        if os.path.exists(out_path):
            skipped += 1
            continue
        try:
            page_html = render_page(art)
        except Exception as e:
            print(f"  ERROR rendering {slug}: {e}")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        written += 1

    print(f"  Wrote {written} new pages, skipped {skipped} existing")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
