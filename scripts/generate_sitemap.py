#!/usr/bin/env python3
"""Auto-generate sitemap.xml and news-sitemap.xml for The Mutapa Times."""
import argparse
import glob
import html
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from regions import get_region as _get_region
except ImportError:
    _get_region = None

BASE_URL = "https://mutapatimes.com"


def region_static_pages(region):
    """Static pages for a non-root edition: home + verticals + its city desks.
    Global pages (authors, about, diaspora, games, moving-to-*) live only in
    the root sitemap."""
    pages = [
        ("", 1.0, "hourly"), ("articles", 0.9, "daily"), ("economy", 0.8, "daily"),
        ("fx", 0.9, "daily"), ("markets", 0.9, "daily"), ("weather", 0.9, "daily"),
        ("property", 0.8, "daily"), ("jobs", 0.9, "hourly"),
    ]
    if _get_region:
        for c in _get_region(region).get("cities", []):
            pages.append((f"{c['slug']}-news", 0.9, "daily"))
    return pages

STATIC_PAGES = [
    ("", 1.0, "hourly"),
    ("articles", 0.9, "daily"),
    ("economy", 0.8, "daily"),
    ("fx", 0.9, "daily"),
    ("markets", 0.9, "daily"),
    ("weather", 0.9, "daily"),
    ("property", 0.8, "daily"),
    ("jobs", 0.9, "hourly"),
    # City news hubs — high SEO value, "{city} news latest" queries
    ("harare-news",          0.95, "hourly"),
    ("bulawayo-news",        0.95, "hourly"),
    ("mutare-news",          0.90, "daily"),
    ("gweru-news",           0.90, "daily"),
    ("masvingo-news",        0.90, "daily"),
    ("victoria-falls-news",  0.90, "daily"),
    ("links", 0.7, "daily"),
    ("authors/", 0.8, "weekly"),
    ("about", 0.7, "monthly"),
    ("advertising", 0.85, "weekly"),
    # Diaspora hubs — country-targeted SEO
    ("diaspora/",                0.85, "weekly"),
    ("diaspora/uk/",             0.85, "weekly"),
    ("diaspora/south-africa/",   0.85, "weekly"),
    ("diaspora/usa/",            0.85, "weekly"),
    # Games
    ("games/shona-wordle/",      0.80, "daily"),
    ("privacy", 0.3, "yearly"),
    ("terms", 0.3, "yearly"),
]


def extract_frontmatter(path):
    """Extract date, title, category, draft flag and source type from a
    markdown article's frontmatter. Returns
    (slug, date, title, category, is_draft, source_type)."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None, None, None, False, None
    fm = m.group(1)
    date_match = re.search(r"^date:\s*['\"]?(\S+)", fm, re.MULTILINE)
    date_str = date_match.group(1) if date_match else None
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
    title = title_match.group(1) if title_match else None
    cat_match = re.search(r'^category:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
    category = cat_match.group(1) if cat_match else None
    draft_match = re.search(r'^draft:\s*true\s*$', fm, re.MULTILINE | re.IGNORECASE)
    is_draft = bool(draft_match)
    src_match = re.search(r'^source_type:\s*["\']?(\w+)', fm, re.MULTILINE)
    source_type = src_match.group(1) if src_match else None
    slug = os.path.splitext(os.path.basename(path))[0]
    return slug, date_str, title, category, is_draft, source_type


def generate(region="zw"):
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    two_days_ago = now - timedelta(days=2)
    # Mirror the page-level noindex policy (build_static_pages.py /
    # build_news_pages.py): wire/aggregated reposts older than 30 days
    # are noindexed, so they must NOT be advertised in the sitemap.
    # Originals stay indexed forever; fresh wire/news (<=30d) still gets
    # Discover/News exposure and stays in the sitemap.
    NOINDEX_AGE_DAYS = 30
    noindex_cutoff = now - timedelta(days=NOINDEX_AGE_DAYS)

    # Region wiring. Zimbabwe (root) keeps the full sitemap incl. global pages
    # (authors, diaspora, moving-to-*); other editions get a focused sitemap of
    # their own home + verticals + city desks + articles/news, written under
    # /<region>/. Global pages stay only in the root sitemap.
    pfx = "" if region == "zw" else f"/{region}"
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    if region == "zw":
        static_pages = STATIC_PAGES
        src_articles = os.path.join(repo_root, "content", "articles")
        src_wires = os.path.join(repo_root, "content", "wires")
        news_dir = os.path.join(repo_root, "news")
        include_global = True
        out_sitemap = os.path.join(repo_root, "sitemap.xml")
        out_news = os.path.join(repo_root, "news-sitemap.xml")
    else:
        static_pages = region_static_pages(region)
        src_articles = os.path.join(repo_root, "content", region, "articles")
        src_wires = os.path.join(repo_root, "content", region, "wires")
        news_dir = os.path.join(repo_root, region, "news")
        include_global = False
        out_sitemap = os.path.join(repo_root, region, "sitemap.xml")
        out_news = os.path.join(repo_root, region, "news-sitemap.xml")
        os.makedirs(os.path.join(repo_root, region), exist_ok=True)

    urls = []
    news_urls = []

    # Static pages
    for page, priority, freq in static_pages:
        loc = f"{BASE_URL}{pfx}/{page}" if page else f"{BASE_URL}{pfx}/"
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{now_str}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    # CMS articles - originals (content/articles) + wire archive
    # (content/wires). Both produce identical /articles/{slug}.html
    # output via build_static_pages.py, so they belong in the same
    # sitemap entries.
    md_paths = sorted(glob.glob(os.path.join(src_articles, "*.md"))
                      + glob.glob(os.path.join(src_wires, "*.md")))
    for md_path in md_paths:
        slug, date_str, title, category, is_draft, source_type = extract_frontmatter(md_path)
        if not slug or slug == "index":
            continue
        if is_draft:
            continue
        # Skip wire/aggregated reposts older than 30 days — they carry a
        # noindex tag, so listing them in the sitemap would only advertise
        # pages we're asking Google not to index. Originals are never
        # skipped; wire items with an unparseable date are kept (we can't
        # prove they're stale).
        if (source_type or "").strip().lower() != "original" and date_str:
            try:
                _adt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if _adt < noindex_cutoff:
                    continue
            except ValueError:
                pass
        # Normalize lastmod to YYYY-MM-DD. Some legacy articles have
        # frontmatter dates like "2026-02-13T09:31:00" (no timezone)
        # which Google flags as Invalid date. Truncating to the date
        # component is always W3C-valid and good enough for sitemap
        # priority / crawl-frequency hints.
        lastmod = (date_str or now_str)[:10]
        # Use the .html URL form so the sitemap matches the canonical
        # link inside each built article page. Otherwise Google crawls
        # the no-extension URL, sees its canonical points elsewhere,
        # and flags the crawled URL as "Alternative page with proper
        # canonical tag" (135-page batch we saw in Search Console).
        loc = f"{BASE_URL}{pfx}/articles/{slug}.html"
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )

        # Google News sitemap: only articles from last 2 days
        if date_str:
            try:
                art_date = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if art_date >= two_days_ago and title:
                    keywords = escape(category) if category else ""
                    news_urls.append(
                        f"  <url>\n"
                        f"    <loc>{escape(loc)}</loc>\n"
                        f"    <news:news>\n"
                        f"      <news:publication>\n"
                        f"        <news:name>The Mutapa Times</news:name>\n"
                        f"        <news:language>en</news:language>\n"
                        f"      </news:publication>\n"
                        f"      <news:publication_date>{date_str[:10]}</news:publication_date>\n"
                        f"      <news:title>{escape(title)}</news:title>\n"
                        + (f"      <news:keywords>{keywords}</news:keywords>\n" if keywords else "")
                        + f"    </news:news>\n"
                        f"  </url>"
                    )
            except ValueError:
                pass

    # Author pages — one entry per active author in content/authors/.
    authors_dir = os.path.join(repo_root, "content", "authors")
    for md_path in (sorted(glob.glob(os.path.join(authors_dir, "*.md"))) if include_global else []):
        slug = os.path.splitext(os.path.basename(md_path))[0]
        # Reuse the frontmatter parser; it gives us is_draft via the
        # `active: false` convention if we read the active flag here.
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                txt = f.read()
        except IOError:
            continue
        if re.search(r'^active:\s*false\s*$', txt, re.MULTILINE | re.IGNORECASE):
            continue
        loc = f"{BASE_URL}/authors/{slug}.html"
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{now_str}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )

    # News landing pages (auto-generated by build_news_pages.py).
    # Filename format: {YYYY-MM-DD}-{slug}-{hash}.html
    if os.path.isdir(news_dir):
        for path in sorted(glob.glob(os.path.join(news_dir, "*.html"))):
            slug = os.path.splitext(os.path.basename(path))[0]
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+?)-([0-9a-f]{6})$", slug)
            if not m:
                continue
            date_str = m.group(1)
            # /news/ pages older than 30 days are swept to noindex by
            # build_news_pages.py, so drop them from the sitemap too.
            try:
                _ndt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if _ndt < noindex_cutoff:
                    continue
            except ValueError:
                pass
            # Read the real title from the rendered HTML — the slug is
            # truncated for URL hygiene and reconstructing from it
            # produces mid-word breaks ("...project-stu") and broken
            # acronyms (".title()" turns "VFEX" into "Vfex").
            news_title = None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    head = f.read(4096)
                t_match = re.search(r"<title>(.*?)</title>", head, re.IGNORECASE | re.DOTALL)
                if t_match:
                    # The rendered HTML already entity-encodes apostrophes
                    # ("&#x27;"); unescape first so escape() below doesn't
                    # double-encode to "&amp;#x27;".
                    raw = html.unescape(t_match.group(1).strip())
                    news_title = re.sub(r"\s*\|\s*The Mutapa Times\s*$", "", raw)
            except IOError:
                pass
            if not news_title:
                news_title = m.group(2).replace("-", " ").strip().title()
            loc = f"{BASE_URL}{pfx}/news/{slug}"
            urls.append(
                f"  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f"    <lastmod>{date_str}</lastmod>\n"
                f"    <changefreq>weekly</changefreq>\n"
                f"    <priority>0.6</priority>\n"
                f"  </url>"
            )
            # Google News sitemap: last 2 days only
            try:
                art_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if art_date >= two_days_ago:
                    news_urls.append(
                        f"  <url>\n"
                        f"    <loc>{escape(loc)}</loc>\n"
                        f"    <news:news>\n"
                        f"      <news:publication>\n"
                        f"        <news:name>The Mutapa Times</news:name>\n"
                        f"        <news:language>en</news:language>\n"
                        f"      </news:publication>\n"
                        f"      <news:publication_date>{date_str}</news:publication_date>\n"
                        f"      <news:title>{escape(news_title)}</news:title>\n"
                        f"    </news:news>\n"
                        f"  </url>"
                    )
            except ValueError:
                pass

    # /moving-to-zimbabwe/ microsite — evergreen UK-citizen guides.
    # Not in main nav (deliberate SEO orphan-by-design) but must be in the
    # sitemap or Google will not find them.
    uk_guide_dir = os.path.join(repo_root, "moving-to-zimbabwe")
    if include_global and os.path.isdir(uk_guide_dir):
        # Hub page first, then individual guides in stable filename order.
        hub = os.path.join(uk_guide_dir, "index.html")
        if os.path.isfile(hub):
            urls.append(
                f"  <url>\n"
                f"    <loc>{BASE_URL}/moving-to-zimbabwe/</loc>\n"
                f"    <lastmod>{now_str}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.85</priority>\n"
                f"  </url>"
            )
        for path in sorted(glob.glob(os.path.join(uk_guide_dir, "*.html"))):
            slug = os.path.splitext(os.path.basename(path))[0]
            if slug == "index":
                continue
            urls.append(
                f"  <url>\n"
                f"    <loc>{BASE_URL}/moving-to-zimbabwe/{slug}.html</loc>\n"
                f"    <lastmod>{now_str}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.8</priority>\n"
                f"  </url>"
            )

    # Write main sitemap
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )
    with open(out_sitemap, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"{out_sitemap} written with {len(urls)} URLs")

    # Write Google News sitemap
    news_sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "\n".join(news_urls)
        + "\n</urlset>\n"
    )
    with open(out_news, "w", encoding="utf-8") as f:
        f.write(news_sitemap)
    print(f"{out_news} written with {len(news_urls)} URLs")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="zw",
                    help="Region edition (default: zw = Zimbabwe at the root)")
    generate(ap.parse_args().region)
