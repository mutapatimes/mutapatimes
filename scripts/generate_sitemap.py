#!/usr/bin/env python3
"""Auto-generate sitemap.xml and news-sitemap.xml for The Mutapa Times."""
import glob
import html
import os
import re
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

BASE_URL = "https://www.mutapatimes.com"

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
    ("privacy", 0.3, "yearly"),
    ("terms", 0.3, "yearly"),
]


def extract_frontmatter(path):
    """Extract date, title, category, and draft flag from a markdown
    article's frontmatter. Returns (slug, date, title, category, is_draft)."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None, None, None, False
    fm = m.group(1)
    date_match = re.search(r"^date:\s*['\"]?(\S+)", fm, re.MULTILINE)
    date_str = date_match.group(1) if date_match else None
    title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
    title = title_match.group(1) if title_match else None
    cat_match = re.search(r'^category:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
    category = cat_match.group(1) if cat_match else None
    draft_match = re.search(r'^draft:\s*true\s*$', fm, re.MULTILINE | re.IGNORECASE)
    is_draft = bool(draft_match)
    slug = os.path.splitext(os.path.basename(path))[0]
    return slug, date_str, title, category, is_draft


def generate():
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    two_days_ago = now - timedelta(days=2)
    urls = []
    news_urls = []

    # Static pages
    for page, priority, freq in STATIC_PAGES:
        loc = f"{BASE_URL}/{page}" if page else f"{BASE_URL}/"
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
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    articles_dir = os.path.join(repo_root, "content", "articles")
    wires_dir = os.path.join(repo_root, "content", "wires")
    md_paths = sorted(glob.glob(os.path.join(articles_dir, "*.md"))
                      + glob.glob(os.path.join(wires_dir, "*.md")))
    for md_path in md_paths:
        slug, date_str, title, category, is_draft = extract_frontmatter(md_path)
        if not slug or slug == "index":
            continue
        if is_draft:
            continue
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
        loc = f"{BASE_URL}/articles/{slug}.html"
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
    for md_path in sorted(glob.glob(os.path.join(authors_dir, "*.md"))):
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
    news_dir = os.path.join(os.path.dirname(__file__), "..", "news")
    if os.path.isdir(news_dir):
        for path in sorted(glob.glob(os.path.join(news_dir, "*.html"))):
            slug = os.path.splitext(os.path.basename(path))[0]
            m = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+?)-([0-9a-f]{6})$", slug)
            if not m:
                continue
            date_str = m.group(1)
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
            loc = f"{BASE_URL}/news/{slug}"
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
    if os.path.isdir(uk_guide_dir):
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
    out = os.path.join(os.path.dirname(__file__), "..", "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"sitemap.xml written with {len(urls)} URLs")

    # Write Google News sitemap
    news_sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n'
        + "\n".join(news_urls)
        + "\n</urlset>\n"
    )
    news_out = os.path.join(os.path.dirname(__file__), "..", "news-sitemap.xml")
    with open(news_out, "w", encoding="utf-8") as f:
        f.write(news_sitemap)
    print(f"news-sitemap.xml written with {len(news_urls)} URLs")


if __name__ == "__main__":
    generate()
